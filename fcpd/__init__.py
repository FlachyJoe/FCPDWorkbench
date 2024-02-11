# -*- coding: utf-8 -*-
###################################################################################
#
#  __init__.py
#
#  Copyright 2021 Florian Foinant-Willig <ffw@2f2v.fr>
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

import os
import sys
import time

from PySide2 import QtGui, QtWidgets
from PySide2.QtCore import QProcess, Qt

import FreeCAD
import FreeCADGui as Gui

import fcpdwb_locator as locator
from . import pdserver
from . import pdtools, pdcontrolertools, pdincludetools, pdrawtools, pdgeometrictools

TRY2EMBED = False

pdProcess = QProcess()
pdServer = pdserver.PureDataServer()


# register message handlers
pdtools.registerToolList(pdServer)
pdcontrolertools.registerToolList(pdServer)
pdincludetools.registerToolList(pdServer)
pdrawtools.registerToolList(pdServer)
pdgeometrictools.registerToolList(pdServer)

userPref = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/FCPD")


def pdIsRunning():
    return pdProcess.state() != QProcess.NotRunning


def runPD():
    if not pdIsRunning():
        pdBin = userPref.GetString("pd_path")

        pdArgs = [
            "-path",
            os.path.join(locator.PD_PATH, "pdlib"),
            "-helppath",
            os.path.join(locator.PD_PATH, "pdhelp"),
        ]

        if userPref.GetBool("fc_allowRaw", False):
            clientTemplate = "client_raw.pdtemplate"
            pdArgs += [
                "-path",
                os.path.join(locator.PD_PATH, "pdautogen"),
                "-helppath",
                os.path.join(locator.PD_PATH, "pdautogenhelp"),
            ]
        else:
            clientTemplate = "client.pdtemplate"

        with open(os.path.join(locator.PD_PATH, clientTemplate), "r") as f:
            clientContents = f.read()
        clientContents = clientContents.replace(
            "%FCLISTEN%", str(userPref.GetInt("fc_listenport"))
        )
        clientContents = clientContents.replace(
            "%PDLISTEN%", str(userPref.GetInt("pd_defaultport"))
        )

        clientFilePath = os.path.join(locator.PD_PATH, "client.pd")
        with open(clientFilePath, "w") as f:
            f.write(clientContents)

        if TRY2EMBED:
            pdProcess.start(pdBin, pdArgs + ["-open", clientFilePath])
            time.sleep(1)
            embedPD()
        else:
            pdProcess.startDetached(pdBin, pdArgs + ["-open", clientFilePath])


def embedPD():
    """
    Try to embed the pd window(s) in FreeCAD
    return True in success
    only implemented for PureData and PlugData on Linux platform
    """
    if not sys.platform.startswith("linux"):
        return False

    exe = userPref.GetString("pd_path").lower()
    if "plugdata" in exe:
        wName = ["PlugData"]
    elif "pd" in exe or "puredata" in exe:
        wName = ["Pd", "PatchWindow"]
    else:
        return False

    mw = Gui.getMainWindow()
    mdi = mw.findChild(QtWidgets.QMdiArea)
    isOk = False
    for w in wName:
        cl = f'xwininfo -root -tree | grep -i \'"{w}"\' | cut -f9 -d" "'
        cliP = QProcess()
        cliP.start("bash", ["-c", cl])
        cliP.waitForReadyRead()
        winid, _ = cliP.readAllStandardOutput().toInt(16)
        if winid:
            container = WinEmbeder(winid, w)
            isOk = True
        cliP.waitForFinished()
    return isOk


class WinEmbeder(QtWidgets.QMainWindow):
    def __init__(self, winId, title):
        mw = Gui.getMainWindow()
        mdi = mw.findChild(QtWidgets.QMdiArea)
        super().__init__(mdi)

        pdProcess.finished.connect(self.close)

        win = QtGui.QWindow.fromWinId(winId)
        cont = QtWidgets.QWidget.createWindowContainer(
            win, self, Qt.FramelessWindowHint
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(cont)

        mdi.addSubWindow(self)

        self.setWindowTitle(title)
        self.show()

    def closeEvent(self, event):
        pass
