# -*- coding: utf-8 -*-
###################################################################################
#
#  pdserver.py
#
#  Copyright 2020 Flachy Joe
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
###################################################################################

# this module implements a TCP server to get FUDI messages from a PureData instance

## @package pdserver

import select
import socket
import sys

from PyQt5 import QtCore

import FreeCAD as App
import FreeCADGui

from pdmsgtranslator import PDMsgTranslator

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError


## Deal with PureData connection
class PureDataServer:

    ## PureDataServer constructor
    #  @param self
    def __init__(self):
        self.isRunning = False
        self.isWaiting = False
        self.remoteAddress = ""
        self.listenAddress = "localhost"
        self.listenPort = 8888
        self.messageHandlerList = {}
        self.readBuffer = ""
        self.writeBuffer = ""
        self.readList = []
        self.observersStore = {}

        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.serverProcess)

    def __eq__(self, other):
        if isinstance(other, bool):
            return other == self.isRunning
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, bool):
            return other != self.isRunning
        return NotImplemented

    ## Update listenning address and port
    #  @param self
    #  @param listenAddress the local interface to listen
    #  @param listenPort the local port to listen
    def setConnectParameters(self, listenAddress, listenPort):
        self.listenAddress = listenAddress
        self.listenPort = listenPort

    ## this function is called when a unregistered message incomes
    #  do nothing and can be overwritten if needed
    #  @param self
    #  @param msg the incoming message as a list of words
    #  @return Nothing
    def defaultMessageHandler(self, msg):
        pass

    ## this function is called when an error occurs in incoming message processing
    #  can be overwritten if needed
    #  @param self
    #  @param msg the incoming message as a list of words
    #  @return the string "ERROR" followed by the error description
    def errorHandler(self, msg):
        '''can be overwriten'''
        return "ERROR %s" % sys.exc_info()[1]

    ## stores a message processing function for specific first words
    #  @param self
    #  @param first_words list of first words for which the function is called
    #  @param handler the function to call
    #  handler is called with 2 parameters : the PureDataServer object and the incoming message as a list of words
    #  @return Nothing
    def registerMessageHandler(self, first_words, handler):
        if not callable(handler):
            raise ValueError("handler must be callable")
        try:
            for words in first_words:
                self.messageHandlerList[words] = handler
        except TypeError:
            self.messageHandlerList[first_words] = handler

    def _pdMsgListProcessor(self, msgList):
        returnValue = []
        for msg in msgList:
            # remove trailing semicolon and newline
            msg = msg[:-2]
            Log("PDServer : <<<%s\r\n" % msg)

            # split words
            words = msg.split(' ')
            if words[0] == 'initrcv':
                self.outputSocket.connect((self.remoteAddress, int(words[1])))
                Log("PDServer : Callback initialized to %s:%s\r\n" % (self.remoteAddress, words[1]))
            elif words[0] == 'close':
                self.terminate()
            else:
                # is words[1] registered ?
                try:
                    if words[1] in self.messageHandlerList:
                        ret = self.messageHandlerList[words[1]](self, words)
                    else:
                        ret = self.defaultMessageHandler(words)
                except Exception:
                    ret = self.errorHandler(words)
                # callback include current patch id ($0 in PD) to route the message
                returnValue.append("%s %s;" % (words[0], PDMsgTranslator.strFromValue(ret)))
        return returnValue

    ## send a message to the PureData client
    #  @param self
    #  @param data the message as a string
    #  @return Nothing
    def send(self, *data):
        for d in data:
            self.writeBuffer += " %s" % PDMsgTranslator.strFromValue(d)
        self.writeBuffer += ";\n"
        if not self.isRunning or self.isWaiting:
            Wrn('WARNING : Data are sent to PDServer but Pure-Data is not connected.\n')

    ## launch the server
    #  @param self
    #  @return Nothing
    def run(self):
        self.isRunning = True

        try:
            self.inputSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.inputSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self.outputSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.outputSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self.inputSocket.bind((self.listenAddress, self.listenPort))
            self.inputSocket.listen(1)

            self.isWaiting = True

            Log("PDServer : Listening on port %i\r\n" % self.listenPort)

            self.readList = [self.inputSocket]
            self.timer.start()

        except OSError:
            Err("PDServer : port %i already in use.\r\n" % self.listenPort)
            self.isWaiting = False
            self.isRunning = False

    ## Ask the server to terminate
    #  @param self
    def terminate(self):
        try:
            # send close message to PD
            self.outputSocket.send(b"0 close;")
        except (BrokenPipeError, OSError):
            # outputSocket already disconnected
            pass
        self.isRunning = False
        self.timer.stop()
        try:
            self.inputSocket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.inputSocket.close()
        self.outputSocket.close()
        Log("PDServer : No more listening port %i\r\n" % self.listenPort)

    # QTimer timeout callback
    def serverProcess(self):
        try:
            if self.writeBuffer:
                writeList = [self.outputSocket]
            else:
                writeList = []

            readable, writable, _ = select.select(self.readList, writeList, [], 0.05)
            for s in readable:
                if s is self.inputSocket:
                    client_socket, address = self.inputSocket.accept()
                    self.readList.append(client_socket)
                    self.remoteAddress = address[0]
                    Log("PDServer : Connection from %s:%s\r\n" % address)
                    self.isWaiting = False
                else:
                    data = s.recv(1024)
                    if data:
                        self.readBuffer += data.decode('utf8')
                        msgList = self.readBuffer.splitlines(True)
                        # is last line complete ?
                        lastLine = msgList[-1]
                        self.readBuffer = ""
                        if not (lastLine[-1:] == "\n" or lastLine[-1] == ";"):
                            msgList = msgList[:-1]
                            self.readBuffer = lastLine
                        retList = self._pdMsgListProcessor(msgList)
                        if retList:
                            for ret in retList:
                                self.send(ret)
                    else:
                        s.close()
                        Log("PDServer : close connection\r\n")
                        self.readList.remove(s)

            for s in writable:
                try:
                    self.outputSocket.send(bytes(self.writeBuffer, "utf8"))
                    Log("PDServer : >>> %s\r\n" % self.writeBuffer)
                    self.writeBuffer = ""
                except BrokenPipeError:
                    Log("PDServer : nowhere to write, kept in the buffer\n")
            self.timer.start()
        except ValueError:
            Err("PDServer : %s\r\n" % sys.exc_info()[1])
            self.isWaiting = False
            self.isRunning = False
        except OSError:
            Err("PDServer : port %i already in use.\r\n" % self.listenPort)
            self.isWaiting = False
            self.isRunning = False

