# -*- coding: utf-8 -*-
###################################################################################
#
#  fcpdwb_commands.py
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

import os
import subprocess
import FreeCAD as App
import FreeCADGui

import fcpdwb_locator
fcpdWBpath = os.path.dirname(fcpdwb_locator.__file__)
fcpdWB_icons_path = os.path.join(fcpdWBpath, 'Icons')

FCPDwb = FreeCADGui.getWorkbench('FCPDWorkbench')

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError

class FCPD_CommandLaunch():
    """Launch Pure-Data"""

    global FCPDwb

    def GetResources(self):
        return {'Pixmap': os.path.join(fcpdWB_icons_path, 'FCPDLogo.svg'),
                'MenuText': "Launch Pure-Data",
                'ToolTip': "Launch Pure-Data and connect it to the internal server."}

    def Activated(self):
        if FCPDwb.pdProcess is None or FCPDwb.pdProcess.poll() is not None:
            # initial message creates the client canvas
            initMsg = "pd filename FCPD Client; #N canvas; #X pop 1;"
            initMsg += "pd-FCPD obj 0 0 fc_client localhost "
            initMsg += "%i " % (FCPDwb.user_pref.GetInt('fc_listenport'))
            initMsg += "%i " % (FCPDwb.user_pref.GetInt('pd_defaultport'))
            initMsg += " 1; "
            initMsg += "pd-FCPD text 10 90 This patch is auto-created by FCPD Workbench don't close it.; "
            initMsg += "pd-FCPD text 10 120 help :; "
            initMsg += "pd-FCPD obj 60 120 helplink FCPD; "
            initMsg += "pd-FCPD loadbang"

            # pd command line
            FCPDwb.pdProcess = subprocess.Popen([FCPDwb.user_pref.GetString('pd_path'),
                                                 '-path', os.path.join(fcpdWBpath, 'pdlib'),
                                                 '-helppath', os.path.join(fcpdWBpath, 'pdhelp'),
                                                 '-send', initMsg])

            FreeCADGui.runCommand('FCPD_Run')
        else:
            Log("Pure-Data is already running.\n")
        return

    def IsActive(self):
        return True


class FCPD_CommandRun():
    """Run PDServer"""

    global FCPDwb

    def GetResources(self):
        return {'Pixmap': os.path.join(fcpdWB_icons_path, 'start.png'),
                'MenuText': "Run Pure-Data server",
                'ToolTip': "Run the internal server and let Pure-Data to connect to."}

    def Activated(self):
        """Do something here"""
        if not FCPDwb.pd_server.is_running:
            FCPDwb.widget.btnRunStop.setText('Server Stop')
            FCPDwb.pd_server.run(with_dialog=False)
            # WARNING Doesn't return until server termination !
            FCPDwb.widget.btnRunStop.setText('Server Start')
        return

    def IsActive(self):
        """Here you can define if the command must be active or not (grayed) if certain conditions
        are met or not. This function is optional."""
        # return FCPDwb.pd_server.is_running
        return True


class FCPD_CommandStop():
    """Stop PDServer"""

    global FCPDwb

    def GetResources(self):
        return {'Pixmap': os.path.join(fcpdWB_icons_path, 'stop.png'),
                'MenuText': "Stop Pure-Data server",
                'ToolTip': "Stop the internal Pure-Data server."}

    def Activated(self):
        """Do something here"""
        if FCPDwb.pd_server.is_running:
            FCPDwb.widget.btnRunStop.setText('Server Start')
            FCPDwb.pd_server.terminate()
        return

    def IsActive(self):
        """Here you can define if the command must be active or not (grayed) if certain conditions
        are met or not. This function is optional."""
        # return FCPDwb.pd_server.is_running
        return True


FreeCADGui.addCommand('FCPD_Run', FCPD_CommandRun())
FreeCADGui.addCommand('FCPD_Stop', FCPD_CommandStop())
FreeCADGui.addCommand('FCPD_Launch', FCPD_CommandLaunch())
