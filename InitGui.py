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

import fcpdwb_locator
fcpdWBpath = os.path.dirname(fcpdwb_locator.__file__)

fcpdWB_icons_path = os.path.join(fcpdWBpath, 'Icons')

fcpdWB_main_icon = os.path.join(fcpdWB_icons_path, 'FCPDLogo.svg')


class FCPDWorkbench(Workbench):

    global fcpdWB_main_icon
    global fcpdWB_icons_path
    global fcpdWBpath

    MenuText = "FCPD"
    ToolTip = "Pure-Data connection"
    Icon = fcpdWB_main_icon

    def Initialize(self):
        "This function is executed when FreeCAD starts"
        # command list
        import fcpdwb_commands
        self.command_list = ["FCPD_Run", "FCPD_Stop", "FCPD_Launch"]
        self.appendToolbar("FCPD", self.command_list)   # creates a new toolbar with your commands
        self.appendMenu("FCPD", self.command_list)      # creates a new menu

        # prefs UI
        FreeCADGui.addIconPath(fcpdWB_icons_path)
        FreeCADGui.addPreferencePage(os.path.join(fcpdWBpath, "FCPDwb_pref.ui"), "FCPD")

        # get prefs
        self.user_pref = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/FCPD")

        # prepare pdserver
        import pdserver
        self.pd_server = pdserver.PureDataServer(self.user_pref.GetString('fc_listenaddress'),
                                                 self.user_pref.GetInt('fc_listenport'))
        # register message handlers
        import pdtools
        pdtools.registerToolList(self.pd_server)

        self.pdProcess = None

        # Show TaskPanel
        from PySide import QtCore, QtGui
        import FCPDTaskPanel
        mw = FreeCADGui.getMainWindow()
        awidget = QtGui.QDockWidget("FCPDTaskPanel", mw)
        self.widget = FCPDTaskPanel.getPanel()
        awidget.setWidget(self.widget)
        mw.addDockWidget(QtCore.Qt.LeftDockWidgetArea, awidget)

    def Activated(self):
        "This function is executed when the workbench is activated"
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        return

    def ContextMenu(self, recipient):
        "This is executed whenever the user right-clicks on screen"
        # "recipient" will be either "view" or "tree"
        self.appendContextMenu("FCPD", self.command_list)   # add commands to the context menu

    def GetClassName(self):
        # this function is mandatory if this is a full python workbench
        return "Gui::PythonWorkbench"


Gui.addWorkbench(FCPDWorkbench())
