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

import sys

from PySide2 import QtCore
from PySide2.QtNetwork import QTcpServer, QTcpSocket, QHostAddress

import FreeCAD as App

from . import pdmsgtranslator
PDMsgTranslator = pdmsgtranslator.PDMsgTranslator

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError

DEBUG = False


## Deal with PureData connection
class PureDataServer(QtCore.QObject):

    ## PureDataServer constructor
    #  @param self
    def __init__(self):
        super().__init__()

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

        self.tcpServer = QTcpServer(self)
        self.tcpServer.setMaxPendingConnections(1)
        self.tcpServer.newConnection.connect(self.newConnection)

        self.inputSocket = None
        self.outputSocket = QTcpSocket(self)

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
                self.outputSocket.connectToHost(self.remoteAddress, int(words[1]), QtCore.QIODevice.WriteOnly)
                if self.outputSocket.waitForConnected(1000):
                    self.isWaiting = False
                    Log("PDServer : Callback initialized to %s:%s\n" % (self.remoteAddress.toString(), words[1]))
                else:
                    Log("PDServer : ERROR during callback initialization\n%s\n" % self.outputSocket.error())
            elif words[0] == 'close':
                self.terminate()
            else:
                # is words[1] registered ?
                try:
                    if words[1] in self.messageHandlerList:
                        ret = self.messageHandlerList[words[1]](self, words)
                    else:
                        ret = self.defaultMessageHandler(words)
                except Exception as e:
                    if DEBUG:
                        raise e
                    ret = self.errorHandler(words)
                # callback include current patch id ($0 in PD) to route the message
                returnValue.append("%s %s;" % (words[0], PDMsgTranslator.strFromValue(ret)))
        return returnValue

    ## send a message to the PureData client
    #  @param self
    #  @param data the message as a string
    #  @return Nothing
    def send(self, *data):
        if self.outputSocket.isOpen():
            writeBuffer=""
            for d in data:
                writeBuffer += " %s" % PDMsgTranslator.strFromValue(d)
            writeBuffer += ";\n"
            self.outputSocket.write(bytes(writeBuffer, "utf8"))
            Log("PDServer : >>> %s\r\n" % writeBuffer)
        else:
            Wrn('WARNING : Data are sent to PDServer but Pure-Data is not connected.\n')

    ## launch the server
    #  @param self
    #  @return Nothing
    def run(self):
        if self.tcpServer.listen(QHostAddress(self.listenAddress), self.listenPort):
            self.isRunning = True
            self.isWaiting = True
            Log("PDServer : Listening on port %i\r\n" % self.listenPort)


    ## Ask the server to terminate
    #  @param self
    def terminate(self):
        self.outputSocket.write(b"0 close;")
        self.outputSocket.disconnectFromHost()
        self.isRunning = False


    def newConnection(self):
            self.inputSocket = self.tcpServer.nextPendingConnection()
            self.inputSocket.readyRead.connect(self.readyRead)
            self.inputSocket.aboutToClose.connect(self.remoteClose)
            self.tcpServer.close()  # no new connection accepted
            self.remoteAddress = self.inputSocket.peerAddress()
            Log("PDServer : Connection from %s:%s\r\n" % (self.remoteAddress.toString(), self.inputSocket.peerPort()))


    def readyRead(self):
        data = self.inputSocket.readAll()
        if data:
            self.readBuffer += str(data, 'utf8')
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


    def remoteClose(self):
        Log("PDServer : %s close connection\r\n" % self.inputSocket.peerAddress().toString())
        if self.isRunning:
            self.run()  # let tcpServer wait for a new connection
