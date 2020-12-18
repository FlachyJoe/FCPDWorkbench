
import os
from PySide import QtGui
from PySide.QtUiTools import QUiLoader
from PySide.QtCore import QFile, QIODevice
import FreeCADGui
import subprocess

global FCPDwb
FCPDwb = FreeCADGui.getWorkbench('FCPDWorkbench')

import fcpdwb_locator
global fcpdWBpath
fcpdWBpath = os.path.dirname(fcpdwb_locator.__file__)

import FreeCAD as App
#shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Err = App.Console.PrintError

def runStopServer(widget):
    global FCPDwb
    if FCPDwb.pd_server.is_running:
        widget.btnRunStop.setText('Lancer le serveur')
        FCPDwb.pd_server.terminate()
    else:
        widget.btnRunStop.setText('Stopper le serveur')
        FCPDwb.pd_server.run(with_dialog=False)


def launchPureData(widget):
    global FCPDwb
    global fcpdWBpath

    initMsg = "pd filename new FCPD; #N canvas; #X pop 1;"
    initMsg += "pd-new obj 0 0 fc_client localhost "
    initMsg += "%i " % (FCPDwb.user_pref.GetInt('fc_listenport'))
    initMsg += "%i " % (FCPDwb.user_pref.GetInt('pd_defaultport'))
    initMsg += " 1; "
    initMsg += "pd-new loadbang"

    FCPDwb.pdProcess = subprocess.Popen([FCPDwb.user_pref.GetString('pd_path'),
                                 '-path', os.path.join(fcpdWBpath, 'pdlib'),
                                 '-send', initMsg])
    # wait for pd launch
    import time
    time.sleep(2)

    # ~ # window embedding
    # ~ import sys
    # ~ if sys.platform.startswith('linux'):
        # ~ mw = FreeCADGui.getMainWindow()
        # ~ mdi = mw.findChild(QtGui.QMdiArea)
        # ~ try :
            # ~ consoleWinid = subprocess.check_output(['xdotool', 'search', '--name', os.path.basename(FCPDwb.user_pref.GetString('pd_path'))])
            # ~ pdPid =  subprocess.check_output(['xdotool', 'getwindowpid', consoleWinid])
            # ~ winIds = subprocess.check_output(['xdotool', 'search', '--pid', pdPid])
            # ~ for winId in winIds.split(b"\n"):
                # ~ if winId :
                    # ~ winName = subprocess.check_output(['xdotool', 'getwindowname', winId]).decode('utf8')
                    # ~ if not winName.startswith('nw'):
                        # ~ Log(winName)
                        # ~ qwin = QtGui.QWindow.fromWinId(int(winId))
                        # ~ pdEmbedder = QtGui.QWidget.createWindowContainer(qwin)
                        # ~ pdEmbedder.setWindowTitle(winName)
                        # ~ mdi.addSubWindow(pdEmbedder)
                        # ~ pdEmbedder.setParent(mdi)
        # ~ except subprocess.CalledProcessError:
            # ~ Log('Unable to embed')

    runStopServer(widget)
    # Don't return until server termination !

def getPanel():
    global fcpdWBpath

    # read UI file
    ui_file = QFile(os.path.join(fcpdWBpath, "FCPDwb_taskpanel.ui"))
    ui_file.open(QFile.ReadOnly)
    widget = QUiLoader().load(ui_file)
    ui_file.close()

    # connection
    widget.btnLaunch.clicked.connect(lambda : launchPureData(widget))
    widget.btnRunStop.clicked.connect(lambda : runStopServer(widget))

    return widget
