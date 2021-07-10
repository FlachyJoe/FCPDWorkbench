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

import fcpdwb_locator as locator


FCPD = FreeCADGui.getWorkbench('FCPDWorkbench')

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError

class FCPD_CommandLaunch():
    """Launch Pure-Data"""

    def GetResources(self):
        return {'Pixmap': locator.icon('FCPDLogo.svg'),
                'MenuText': "Launch Pure-Data",
                'ToolTip': "Launch Pure-Data and connect it to the internal server."}

    def Activated(self):
        if FCPD.pdProcess is None or FCPD.pdProcess.poll() is not None:
            pdBin = FCPD.userPref().GetString('pd_path')

            pdArgs = ['-path', os.path.join(locator.PATH, 'pdlib'),
                      '-helppath', os.path.join(locator.PATH, 'pdhelp')]

            if FCPD.userPref().GetBool('fc_allowRaw', False):
                clientTemplate = "client_raw.pdtemplate"
                pdArgs += ['-path', os.path.join(locator.PATH, 'pdautogen'),
                           '-helppath', os.path.join(locator.PATH, 'pdautogenhelp')]
            else:
                clientTemplate = "client.pdtemplate"

            with open(os.path.join(locator.PATH, clientTemplate), 'r') as f:
                clientContents = f.read()
            clientContents = clientContents.replace('%FCLISTEN%', str(FCPD.userPref().GetInt('fc_listenport')))
            clientContents = clientContents.replace('%PDLISTEN%', str(FCPD.userPref().GetInt('pd_defaultport')))

            clientFilePath = os.path.join(locator.PATH, 'client.pd')
            with open(clientFilePath, 'w') as f:
                f.write(clientContents)

            FCPD.pdProcess = subprocess.Popen([pdBin]
                                              + pdArgs
                                              + ['-open', clientFilePath])

            FreeCADGui.runCommand('FCPD_Run')
        else:
            Log("Pure-Data is already running.\n")
        return

    def IsActive(self):
        # return FCPD.pdProcess is None or FCPD.pdProcess.poll() is not None
        return True


class FCPD_CommandRun():
    """Run PDServer"""

    global FCPD

    def GetResources(self):
        return {'Pixmap': locator.icon('start.png'),
                'MenuText': "Run Pure-Data server",
                'ToolTip': "Run the internal server and let Pure-Data to connect to."}

    def Activated(self):
        serv = FCPD.pdServer
        if not serv.isRunning:
            serv.setConnectParameters(FCPD.userPref().GetString('fc_listenaddress', 'localhost'),
                                      FCPD.userPref().GetInt('fc_listenport', 8888))
            serv.run(withDialog=False)
            # WARNING Doesn't return until server termination !
        return

    def IsActive(self):
        # return not FCPD.pdServer.isRunning
        return True


class FCPD_CommandStop():
    """Stop PDServer"""

    global FCPD

    def GetResources(self):
        return {'Pixmap': locator.icon('stop.png'),
                'MenuText': "Stop Pure-Data server",
                'ToolTip': "Stop the internal Pure-Data server."}

    def Activated(self):
        if FCPD.pdServer.isRunning:
            FCPD.pdServer.terminate()
        return

    def IsActive(self):
        # return FCPD.pdServer.isRunning
        return True


class FCPD_CommandAddPDControler():
    """Create a PDControler object in the document"""

    def GetResources(self):
        return {'Pixmap': locator.icon('insert-link.png')
                'MenuText': "Create the PDControler object",
                'ToolTip': "Create an object to store PD-controllable properties"}

    def Activated(self):
        import pdcontroler
        pdcontroler.create()
        return

    def IsActive(self):
        return True


class FCPD_CommandEditPDControler():
    """Edit a PDControler file in Pure-Data"""

    global FCPD

    def GetResources(self):
        return {'Pixmap': locator.icon('document-page-setup.png'),
                'MenuText': "Edit a PDControler patch",
                'ToolTip': "Open the PDControler patch in Pure-Data"}

    def Activated(self):
        import pdcontroler
        #get (existent) PDControler
        curObj = pdcontroler.create()
        #copy file contents
        from pathlib import Path
        import tempfile
        fcTempFile = curObj.PDPatch
        contents = Path(fcTempFile).read_text()
        _, cpFile = tempfile.mkstemp(text=True)
        Path(cpFile).write_text(contents)
        #open with PD
        FreeCADGui.runCommand('FCPD_Launch')
        #TODO wait until PD opened
        FCPD.pdServer.send("0 pd open", os.path.basename(cpFile), os.path.dirname(cpFile))
        #set PDPatch property to cpFile so change will be saved with FC file
        #TODO have to be done AFTER file change, use watchdog
        curObj.PDPatch = cpFile

    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 1:
            curObj = sel[0]
            return pdcontroler.isPDControler(curObj)
        return False


FreeCADGui.addCommand('FCPD_Run', FCPD_CommandRun())
FreeCADGui.addCommand('FCPD_Stop', FCPD_CommandStop())
FreeCADGui.addCommand('FCPD_Launch', FCPD_CommandLaunch())
FreeCADGui.addCommand('FCPD_AddPDControler', FCPD_CommandAddPDControler())
FreeCADGui.addCommand('FCPD_EditPDControler', FCPD_CommandEditPDControler())
