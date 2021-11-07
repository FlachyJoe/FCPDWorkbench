# -*- coding: utf-8 -*-
###################################################################################
#
#  __init__.py
#
#  Copyright 2021 Flachy Joe
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
from PySide2.QtCore import QProcess

import FreeCAD

import fcpdwb_locator as locator
from . import pdserver, pdtools, pdcontrolertools, pdrawtools

class FCPDCore():
    def __init__(self):
        self.pdProcess = QProcess()

        # prepare pdserver
        self.pdServer = pdserver.PureDataServer()

        # register message handlers
        pdtools.registerToolList(self.pdServer)

        pdcontrolertools.registerToolList(self.pdServer)

        if self.userPref().GetBool('fc_allowRaw', False):
            pdrawtools.registerToolList(self.pdServer)

    def userPref(self):
        # get prefs
        return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/FCPD")

    def pdIsRunning(self):
        return not self.pdProcess.state() == QProcess.NotRunning

    def runPD(self):
        if not self.pdIsRunning():
            pdBin = self.userPref().GetString('pd_path')

            pdArgs = ['-path', os.path.join(locator.PD_PATH, 'pdlib'),
                      '-helppath', os.path.join(locator.PD_PATH, 'pdhelp')]

            if self.userPref().GetBool('fc_allowRaw', False):
                clientTemplate = "client_raw.pdtemplate"
                pdArgs += ['-path', os.path.join(locator.PD_PATH, 'pdautogen'),
                           '-helppath', os.path.join(locator.PD_PATH, 'pdautogenhelp')]
            else:
                clientTemplate = "client.pdtemplate"

            with open(os.path.join(locator.PD_PATH, clientTemplate), 'r') as f:
                clientContents = f.read()
            clientContents = clientContents.replace('%FCLISTEN%',
                                                    str(self.userPref().GetInt('fc_listenport')))
            clientContents = clientContents.replace('%PDLISTEN%',
                                                    str(self.userPref().GetInt('pd_defaultport')))

            clientFilePath = os.path.join(locator.PD_PATH, 'client.pd')
            with open(clientFilePath, 'w') as f:
                f.write(clientContents)

            self.pdProcess.startDetached(pdBin, pdArgs + ['-open', clientFilePath])
