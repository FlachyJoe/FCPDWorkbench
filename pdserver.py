import FreeCAD as App
import FreeCADGui
import select
import socket
import sys

#shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Err = App.Console.PrintError


class PureDataServer:

    def __init__(self, listen_address, listen_port):
        self.is_running = False
        self.is_waiting = False
        self.remote_address = ""
        self.listen_address = listen_address
        self.listen_port = listen_port
        self.message_handler_list={}
        self.message_box = False

    def terminate(self):
        # send close message to PD
        try :
            self.output_socket.send(b"CLOSE")
        except BrokenPipeError:
            # output_socket already disconnected
            pass
        self.is_running = False

    def _spacer(self, strMessage):
        '''remove quotes, brackets and others'''
        return strMessage.translate(str.maketrans(',=', '  ', ';()[]{}"\'' ))

    def default_message_handler(self, msg):
        '''can be overwriten'''
        pass

    def error_handler(self, msg):
        '''can be overwriten'''
        return "ERROR %s" % sys.exc_info()[1]

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
            #remove trailing semicolon and newline
            msg = msg[:-2]
            Log("PDServer : <<<%s\r\n" % msg)

            #split words
            words = msg.split(' ')
            if words[0] == 'initrcv':
                self.output_socket.connect((self.remote_address, int(words[1])))
                Log("PDServer : Callback initialized to %s:%s\r\n" % (self.remote_address, words[1]))
            elif words[0] == 'close':
                self.terminate()
            else:
                #is words[1] registered ?
                try :
                    if words[1] in self.message_handler_list:
                        ret = self.message_handler_list[words[1]](words)
                    else:
                        ret = self.default_message_handler(words)
                    if type(ret) != str:
                        ret = str(ret)
                except :
                    ret = self.error_handler(words)
                #callback include current patch id ($0 in PD) to route the message and a trailing semicolon
                #quotes, bracket and other are removed by spacer function
                returnValue.append("%s %s;" % (words[0], self._spacer(ret)) )
        return returnValue

    def _showDialog(self):
        from PySide import QtGui
        mb = QtGui.QMessageBox()
        mb.setIcon(mb.Icon.Warning)
        mb.setText("Wait for PureData connection...")
        mb.setWindowTitle("PureData connection")
        mb.setModal(False)
        mb.setStandardButtons(mb.StandardButton.Close)
        mb.buttonClicked.connect(lambda btn : self.terminate())
        mb.show()
        self.message_box = mb

    def run(self, with_dialog=True):
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
            write_list = []
            readBuffer = ""
            while self.is_running:
                FreeCADGui.updateGui()
                readable, writable, errored = select.select(read_list, write_list, [],0.05)
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
                            #is last line complete ?
                            lastLine = msgList[-1]
                            readBuffer = ""
                            if not (lastLine[-1:] == "\n" or lastLine[-1] == ";"):
                                msgList =  msgList[:-1]
                                readBuffer = lastLine
                            retList = self._pdMsgListProcessor(msgList)
                            if retList:
                                for ret in retList:
                                    bret=bytes(ret, "utf8")
                                    n=self.output_socket.send(bret)
                                    Log("PDServer : >>> %s\r\n" % ret)
                        else:
                            s.close()
                            Log("PDServer : close connection\r\n")
                            read_list.remove(s)

        except ValueError:
            import sys
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
