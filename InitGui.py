# -*- coding: utf-8 -*-
###################################################################################
#
#  InitGui.py
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


class FCPDWorkbench(Workbench):

    def QT_TRANSLATE_NOOP(scope, text):
        return text

    import fcpdwb_locator as locator

    MenuText = "FCPD"
    ToolTip = QT_TRANSLATE_NOOP("FCPDWorkbench", "Pure-Data connection")
    Icon = locator.icon("FCPDLogo.svg")

    def Initialize(self):
        import fcpd

        import fcpdwb_locator as locator

        FreeCADGui.addLanguagePath(locator.TRANSLATIONS_PATH)
        FreeCADGui.updateLocale()

        # command list
        import fcpdwb_commands

        self.commandList = [
            "FCPD_Launch",
            "FCPD_AddInclude",
            "FCPD_AddPopulatedInclude",
        ]
        self.appendToolbar("FCPD", self.commandList)  # creates a new toolbar
        self.appendMenu("FCPD", self.commandList)  # creates a new menu

        # prefs UI
        FreeCADGui.addIconPath(locator.ICONS_PATH)
        FreeCADGui.addPreferencePage(locator.resource("FCPDwb_pref.ui"), "FCPD")

    def ContextMenu(self, recipient):
        if recipient == "tree":
            # add commands to the context menu
            self.appendContextMenu(
                "FCPD", ["FCPD_AddInclude", "FCPD_AddPopulatedInclude"]
            )

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(FCPDWorkbench())
