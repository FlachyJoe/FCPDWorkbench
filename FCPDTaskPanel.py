
import os
import subprocess
from PySide.QtUiTools import QUiLoader
from PySide.QtCore import QFile
import FreeCAD as App
import FreeCADGui

import fcpdwb_locator

FCPDwb = FreeCADGui.getWorkbench('FCPDWorkbench')

fcpdWBpath = os.path.dirname(fcpdwb_locator.__file__)

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError


def runStopServer():
    global FCPDwb
    if FCPDwb.pd_server.is_running:
        FreeCADGui.runCommand('FCPD_Stop')
    else:
        FreeCADGui.runCommand('FCPD_Run')


def getPanel():
    global fcpdWBpath

    # read UI file
    ui_file = QFile(os.path.join(fcpdWBpath, "FCPDwb_taskpanel.ui"))
    ui_file.open(QFile.ReadOnly)
    widget = QUiLoader().load(ui_file)
    ui_file.close()

    # connection
    widget.btnLaunch.clicked.connect(lambda: FreeCADGui.runCommand('FCPD_Launch'))
    widget.btnRunStop.clicked.connect(runStopServer)

    return widget
