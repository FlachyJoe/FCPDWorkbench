## @package pdserver

import select
import socket
import sys
import FreeCAD as App
import FreeCADGui

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError


## Deal with PureData connection
class PureDataServer:

    ## PureDataServer constructor
    #  @param self
    #  @param listen_address the local interface to listen
    #  @param listen_port the local port to listen
    def __init__(self, listen_address, listen_port):
        self.is_running = False
        self.is_waiting = False
        self.remote_address = ""
        self.listen_address = listen_address
        self.listen_port = listen_port
        self.message_handler_list = {}
        self.message_box = False
        self.write_buffer = ""
        self.objects_store = {}

    ## Ask the server to terminate
    #  @param self
    def terminate(self):
        try:
            # send close message to PD
            self.output_socket.send(b"0 close")
        except BrokenPipeError:
            # output_socket already disconnected
            pass
        self.is_running = False

    ## remove quotes, brackets and others
    #  @param self
    #  @param strMessage a string to clean
    #  @return a valid PureData message
    def _spacer(self, strMessage):
        return strMessage.translate(str.maketrans(',=', '  ', ';()[]{}"\''))

    ## this function is called when a unregistred message incomes
    #  do nothing and can be overwritten if needed
    #  @param self
    #  @param msg the incomming message as a list of words
    #  @return Nothing
    def default_message_handler(self, msg):
        pass

    ## this function is called when an error occurs in incomming message processing
    #  can be overwritten if needed
    #  @param self
    #  @param msg the incomming message as a list of words
    #  @return the string "ERROR" followed by the error description
    def error_handler(self, msg):
        '''can be overwriten'''
        return "ERROR %s" % sys.exc_info()[1]

    ## stores a message processing function for specific first words
    #  @param self
    #  @param first_words list of first words for which the function is called
    #  @param handler the function to call
    #  handler is called with 2 parameters : the PureDataServer object and the incomming message as a list of words
    #  @return Nothing
    def register_message_handler(self, first_words, handler):
        if not callable(handler):
            raise ValueError("handler must be callable")
        try:
            for words in first_words:
                self.message_handler_list[words] = handler
        except TypeError:
            self.message_handler_list[first_words] = handler

    def _pdMsgListProcessor(self, msgList):
        returnValue = []
        for msg in msgList:
            # remove trailing semicolon and newline
            msg = msg[:-2]
            Log("PDServer : <<<%s\r\n" % msg)

            # split words
            words = msg.split(' ')
            if words[0] == 'initrcv':
                self.output_socket.connect((self.remote_address, int(words[1])))
                Log("PDServer : Callback initialized to %s:%s\r\n" % (self.remote_address, words[1]))
            elif words[0] == 'close':
                self.terminate()
            else:
                # is words[1] registered ?
                try:
                    if words[1] in self.message_handler_list:
                        ret = self.message_handler_list[words[1]](self, words)
                    else:
                        ret = self.default_message_handler(words)
                    if type(ret) != str:
                        ret = str(ret)
                except Exception:
                    ret = self.error_handler(words)
                # callback include current patch id ($0 in PD) to route the message and a trailing semicolon
                # quotes, bracket and other are removed by spacer function
                returnValue.append("%s %s;" % (words[0], self._spacer(ret)))
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
        self.message_box = mb

    ## send a message to the PureData client
    #  @param self
    #  @param data the message as a string
    #  @return Nothing
    def send(self, data):
        self.write_buffer += data

    ## launch the server
    #  @param self
    #  @param with_dialog if True show a dialog to let the user stops the server
    #  @return Nothing but only when the server stops
    def run(self, with_dialog=False):
        self.is_running = True
        self.input_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.input_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.output_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.output_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.input_socket.bind((self.listen_address, self.listen_port))
            self.input_socket.listen(1)

            if with_dialog:
                self._showDialog()

            self.is_waiting = True

            Log("PDServer : Listening on port %i\r\n" % self.listen_port)

            read_list = [self.input_socket]
            write_list = [self.output_socket]
            readBuffer = ""
            while self.is_running:
                FreeCADGui.updateGui()
                readable, writable, errored = select.select(read_list, write_list, [], 0.05)
                for s in readable:
                    if s is self.input_socket:
                        client_socket, address = self.input_socket.accept()
                        read_list.append(client_socket)
                        self.remote_address = address[0]
                        Log("PDServer : Connection from %s:%s\r\n" % address)
                        if self.message_box:
                            self.message_box.setText("Connected with PureData")
                        self.is_waiting = False

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
                                    bret = bytes(ret, "utf8")
                                    self.output_socket.send(bret)
                                    Log("PDServer : >>> %s\r\n" % ret)
                        else:
                            s.close()
                            Log("PDServer : close connection\r\n")
                            read_list.remove(s)

                for s in writable:
                    if self.write_buffer:
                        try:
                            self.output_socket.send(bytes(self.write_buffer, "utf8"))
                            Log("PDServer (buffered) : >>> %s\r\n" % self.write_buffer)
                            self.write_buffer = ""
                        except BrokenPipeError:
                            Log("PDServer : nowhere to write, keep in buffer")
        except ValueError:
            Err("PDServer : %s\r\n" % sys.exc_info()[1])
        finally:
            try:
                self.input_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        self.input_socket.close()
        self.output_socket.close()
        Log("PDServer : No more listening port %i\r\n" % self.listen_port)
        if with_dialog and self.message_box:
            self.message_box.close()
