# -*- coding: utf-8 -*-
###################################################################################
#
#  fcpdwb_commands.py
#
#  Copyright 2025 Florian Foinant-Willig <ffw@2f2v.fr>
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

import FreeCAD as App
import FreeCADGui

import fcpdwb_locator as locator

import fcpd


def QT_TRANSLATE_NOOP(scope, text):
    return text


# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError


class FCPD_CommandLaunch:
    """Launch Pure-Data"""

    def GetResources(self):
        return {
            "Pixmap": locator.icon("FCPDLogo.svg"),
            "MenuText": QT_TRANSLATE_NOOP("FCPD_Launch", "Launch Pure-Data"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "FCPD_Launch",
                "Launch Pure-Data and connect it" " to the internal server.",
            ),
        }

    def Activated(self):
        if not fcpd.pdServer.isRunning:
            FreeCADGui.runCommand("FCPD_Run")

        if not fcpd.pdIsRunning():
            fcpd.runPD()
        else:
            Log(QT_TRANSLATE_NOOP("FCPD_Launch", "Pure-Data is already running.\n"))
        return

    def IsActive(self):
        return not fcpd.pdIsRunning()


class FCPD_CommandRun:
    """Run PDServer"""

    def GetResources(self):
        return {
            "Pixmap": locator.icon("start.svg"),
            "MenuText": QT_TRANSLATE_NOOP("FCPD_Run", "Run Pure-Data server"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "FCPD_Run",
                "Run the internal server and let" " Pure-Data to connect to.",
            ),
        }

    def Activated(self):
        serv = fcpd.pdServer
        if not serv.isRunning:
            serv.setConnectParameters(
                fcpd.userPref.GetString("fc_listenaddress", "127.0.0.1"),
                fcpd.userPref.GetInt("fc_listenport", 8888),
            )
            serv.run()
        return

    def IsActive(self):
        # return not FCPD.pdServer.isRunning
        return True


class FCPD_CommandStop:
    """Stop PDServer"""

    def GetResources(self):
        return {
            "Pixmap": locator.icon("stop.svg"),
            "MenuText": QT_TRANSLATE_NOOP("FCPD_Stop", "Stop Pure-Data server"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "FCPD_Stop", "Stop the internal Pure-Data server."
            ),
        }

    def Activated(self):
        if fcpd.pdServer.isRunning:
            fcpd.pdServer.terminate()
        return

    def IsActive(self):
        return fcpd.pdServer.isRunning


class FCPD_CommandAddInclude:
    """Create a PDInclude object"""

    def GetResources(self):
        return {
            "Pixmap": locator.icon("new-include.svg"),
            "MenuText": QT_TRANSLATE_NOOP(
                "FCPD_AddInclude", "Create a PDInclude object"
            ),
            "ToolTip": QT_TRANSLATE_NOOP(
                "FCPD_AddInclude",
                "Create a PDInclude object to store"
                " a PD patch in the FreeCAD document.",
            ),
        }

    def Activated(self):
        from fcpd import pdinclude

        pdinclude.createWithEmpty()
        return

    def IsActive(self):
        return True


class FCPD_CommandAddPopulatedInclude:
    """Create a PDInclude object from an *.pd file"""

    def GetResources(self):
        return {
            "Pixmap": locator.icon("new-populated-include.svg"),
            "MenuText": QT_TRANSLATE_NOOP(
                "FCPD_AddPopulatedInclude",
                "Create a PDInclude object from an *.pd file",
            ),
            "ToolTip": QT_TRANSLATE_NOOP(
                "FCPD_AddPopulatedInclude",
                "Create a PDInclude object to store a given"
                " PD patch in the FreeCAD document.",
            ),
        }

    def Activated(self):
        from fcpd import pdinclude

        from PySide.QtWidgets import QFileDialog

        fileName = QFileDialog.getOpenFileName(
            None,
            QT_TRANSLATE_NOOP("FCPD_AddPopulatedInclude", "Open a Pure-Data file"),
            "",
            QT_TRANSLATE_NOOP("FCPD_AddPopulatedInclude", "Pure-Data Files (*.pd)"),
        )
        if fileName:
            obj = pdinclude.create()
            obj.PDFile = fileName

    def IsActive(self):
        return True


FreeCADGui.addCommand('FCPD_Run', FCPD_CommandRun())
FreeCADGui.addCommand('FCPD_Stop', FCPD_CommandStop())
FreeCADGui.addCommand("FCPD_Launch", FCPD_CommandLaunch())
FreeCADGui.addCommand("FCPD_AddInclude", FCPD_CommandAddInclude())
FreeCADGui.addCommand("FCPD_AddPopulatedInclude", FCPD_CommandAddPopulatedInclude())
