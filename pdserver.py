## @package pdserver

import select
import socket
import sys

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
        self.messageBox = False
        self.writeBuffer = ""
        self.observersStore = {}

        self.strFromValue = PDMsgTranslator.strFromValue
        self.valueFromStr = PDMsgTranslator.valueFromStr
        self.popValues = PDMsgTranslator.popValues

    ## Update listenning address and port
    #  @param self
    #  @param listenAddress the local interface to listen
    #  @param listenPort the local port to listen
    def setConnectParameters(self, listenAddress, listenPort):
        self.listenAddress = listenAddress
        self.listenPort = listenPort

    ## Ask the server to terminate
    #  @param self
    def terminate(self):
        try:
            # send close message to PD
            self.output_socket.send(b"0 close;")
        except BrokenPipeError:
            # output_socket already disconnected
            pass
        self.isRunning = False

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
                self.output_socket.connect((self.remoteAddress, int(words[1])))
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
                returnValue.append("%s %s;" % (words[0], self.strFromValue(ret)))
        return returnValue

    def _showDialog(self):
        from PySide import QtGui
        mb = QtGui.QMessageBox()
        mb.setIcon(mb.Icon.Warning)
        mb.setText("Wait for PureData connection...")
        mb.setWindowTitle("PureData connection")
        mb.setModal(False)
        mb.setStandardButtons(mb.StandardButton.Close)
        mb.buttonClicked.connect(lambda btn: self.terminate())
        mb.show()
        self.messageBox = mb

    ## send a message to the PureData client
    #  @param self
    #  @param data the message as a string
    #  @return Nothing
    def send(self, *data):
        for d in data:
            self.writeBuffer += " %s" % self.strFromValue(d)
        self.writeBuffer += ";\n"

    ## launch the server
    #  @param self
    #  @param withDialog if True show a dialog to let the user stops the server
    #  @return Nothing but only when the server stops
    def run(self, withDialog=False):
        self.isRunning = True
        self.input_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.input_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.output_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.output_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.input_socket.bind((self.listenAddress, self.listenPort))
            self.input_socket.listen(1)

            if withDialog:
                self._showDialog()

            self.isWaiting = True

            Log("PDServer : Listening on port %i\r\n" % self.listenPort)

            readList = [self.input_socket]
            readBuffer = ""
            while self.isRunning:
                FreeCADGui.updateGui()

                if self.writeBuffer:
                    write_list = [self.output_socket]
                else:
                    write_list = []

                readable, writable, _ = select.select(readList, write_list, [], 0.05)
                for s in readable:
                    if s is self.input_socket:
                        client_socket, address = self.input_socket.accept()
                        readList.append(client_socket)
                        self.remoteAddress = address[0]
                        Log("PDServer : Connection from %s:%s\r\n" % address)
                        if self.messageBox:
                            self.messageBox.setText("Connected with PureData")
                        self.isWaiting = False

                    else:
                        data = s.recv(1024)
                        if data:
                            readBuffer += data.decode('utf8')
                            msgList = readBuffer.splitlines(True)
                            # is last line complete ?
                            lastLine = msgList[-1]
                            readBuffer = ""
                            if not (lastLine[-1:] == "\n" or lastLine[-1] == ";"):
                                msgList = msgList[:-1]
                                readBuffer = lastLine
                            retList = self._pdMsgListProcessor(msgList)
                            if retList:
                                for ret in retList:
                                    self.send(ret)
                        else:
                            s.close()
                            Log("PDServer : close connection\r\n")
                            readList.remove(s)

                for s in writable:
                    try:
                        self.output_socket.send(bytes(self.writeBuffer, "utf8"))
                        Log("PDServer : >>> %s\r\n" % self.writeBuffer)
                        self.writeBuffer = ""
                    except BrokenPipeError:
                        Log("PDServer : nowhere to write, kept in the buffer")
        except ValueError:
            Err("PDServer : %s\r\n" % sys.exc_info()[1])
        except OSError:
            Err("PDServer : port %i already in use.\r\n" % self.listenPort)
        finally:
            self.isRunning = False
            try:
                self.input_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        self.input_socket.close()
        self.output_socket.close()
        Log("PDServer : No more listening port %i\r\n" % self.listenPort)
        if withDialog and self.messageBox:
            self.messageBox.close()
