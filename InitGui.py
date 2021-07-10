# -*- coding: utf-8 -*-
###################################################################################
#
#  InitGui.py
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

class FCPDWorkbench(Workbench):

    MenuText = "FCPD"
    ToolTip = "Pure-Data connection"
    import fcpdwb_locator as locator
    Icon = locator.icon('FCPDLogo.svg')

    def Initialize(self):
        "This function is executed when FreeCAD starts"
        # command list
        import fcpdwb_commands
        self.commandList = ["FCPD_Run", "FCPD_Stop", "FCPD_Launch", "FCPD_AddPDControler", "FCPD_EditPDControler"]
        self.appendToolbar("FCPD", self.commandList)   # creates a new toolbar with your commands
        self.appendMenu("FCPD", self.commandList)      # creates a new menu

        # prefs UI
        import fcpdwb_locator as locator
        FreeCADGui.addIconPath(locator.ICONS_PATH)
        FreeCADGui.addPreferencePage(os.path.join(locator.PATH, "FCPDwb_pref.ui"), "FCPD")

        # prepare pdserver
        import pdserver
        self.pdServer = pdserver.PureDataServer()

        # register message handlers
        import pdtools
        pdtools.registerToolList(self.pdServer)
        import pdcontrolertools
        pdcontrolertools.registerToolList(self.pdServer)

        if self.userPref().GetBool('fc_allowRaw', False):
            import pdrawtools
            pdrawtools.registerToolList(self.pdServer)

        self.pdProcess = None

    def userPref(self):
        # get prefs
        return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/FCPD")

    def Activated(self):
        "This function is executed when the workbench is activated"
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        return

    def ContextMenu(self, recipient):
        "This is executed whenever the user right-clicks on screen"
        # "recipient" will be either "view" or "tree"
        # self.appendContextMenu("FCPD", self.commandList)   # add commands to the context menu

    def GetClassName(self):
        # this function is mandatory if this is a full python workbench
        return "Gui::PythonWorkbench"


Gui.addWorkbench(FCPDWorkbench())
