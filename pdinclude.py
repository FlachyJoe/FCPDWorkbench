#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  pdinclude.py
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

import os
import tempfile
import shutil

from PyQt5 import QtCore

import FreeCAD as App

import fcpdwb_locator as locator

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError

class PDInclude:
    def __init__(self, obj):
        obj.Proxy = self
        self.object = obj
        self.Type = "PDInclude"
        obj.addProperty('App::PropertyFileIncluded', 'PDFile', '', '')

    def startEdit(self):
        sFile = self.object.PDFile
        pdServer = locator.getFCPDWorkbench().pdServer
        if sFile and pdServer.isRunning :
            _, self.tmpFile = tempfile.mkstemp()
            shutil.copyfile(sFile, self.tmpFile)
            dirName, fileName = os.path.split(self.tmpFile)
            pdServer.send('0 pd open %s %s' % (fileName, dirName))
            # watch for file change
            self.fs_watcher = QtCore.QFileSystemWatcher([self.tmpFile])
            self.fs_watcher.fileChanged.connect(self.endEdit)

    def endEdit(self, filename):
        Log("%s have changed\n" % filename)
        if self.tmpFile:
            self.object.PDFile = self.tmpFile
            App.ActiveDocument.recompute()

    def onDocumentRestored(self, obj):
        self.object = obj

    def __getstate__(self):
        return None

class PDIncludeViewProvider:
    def __init__(self, vobj, obj):
        vobj.Proxy = self

    def doubleClicked(self, vobj):
        vobj.Object.Proxy.startEdit()

    def __getstate__(self):
        return None

def create():
    obj = App.ActiveDocument.addObject('App::FeaturePython', 'PDInclude')
    PDInclude(obj)
    PDIncludeViewProvider(obj.ViewObject, obj)
