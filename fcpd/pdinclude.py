#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  pdinclude.py
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

import os
import tempfile
import shutil
import time

from PySide import QtCore

import FreeCAD as App
import FreeCADGui as Gui

import fcpd
import fcpdwb_locator as locator

DEBUG = True

# shortcuts of FreeCAD console
Log = App.Console.PrintLog if DEBUG else lambda *args: None
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError


def createPDFile(filePath):
    with open(filePath, "w") as fd:
        fd.writelines("#N canvas 200 200 450 300 12;\n")


def addCloseDetection(filePath):
    """Add a [fc_isIncluded] in a .pd file to send endedit message on close"""
    _, fileName = os.path.split(filePath)
    with open(filePath, "r+") as fd:
        contents = fd.readlines()
        # add onClose subpatch
        onClose = f"#X obj 10 10 fc_isIncluded {fileName};\n"
        # find last connect line bottom to top
        for lineNumber, line in reversed(list(enumerate(contents))):
            if not line.startswith("#X connect "):
                break
        newContents = (
            contents[: lineNumber + 1] + [onClose] + contents[lineNumber + 1 :]
        )
        fd.seek(0)
        fd.writelines(newContents)
    Log("FCPD", "close detection added\n")


def hasCloseDetection(filePath):
    """check the existence of [fc_isIncluded] in a .pd file"""
    with open(filePath, "r+") as fd:
        contents = fd.readlines()
        # find first subpatch line
        for lineNumber, line in enumerate(contents):
            if line.startswith("#X obj ") and ("fc_isIncluded" in line):
                return lineNumber
    return False


def updateCloseDetection(filePath):
    """update [fc_isIncluded] argument to the correct filename"""
    _, fileName = os.path.split(filePath)
    lineNumber = hasCloseDetection(filePath)
    if lineNumber:
        with open(filePath, "r+") as fd:
            contents = fd.readlines()
            onClose = f"#X obj 10 10 fc_isIncluded {fileName};\n"
            newContents = contents[:lineNumber] + [onClose] + contents[lineNumber + 1 :]
            fd.seek(0)
            fd.writelines(newContents)
            Log("FCPD", "close detection updated\n")
    else:
        addCloseDetection(filePath)


class PDInclude:
    def __init__(self, obj):
        obj.Proxy = self
        self.object = obj
        self.Type = "PDInclude"
        obj.addProperty("App::PropertyFileIncluded", "PDFile", "", "")
        self.isOpen = False
        self.docObserver = None
        self.skipChange = 0
        self.tmpFile = ""

    def startEdit(self):
        if not self.isOpen:
            sFile = self.object.PDFile
            if sFile:
                if not fcpd.pdServer.isAvailable():
                    fcpd.pdServer.run()
                    fcpd.runPD()

                _, self.tmpFile = tempfile.mkstemp()
                shutil.copyfile(sFile, self.tmpFile)
                dirName, fileName = os.path.split(self.tmpFile)

                updateCloseDetection(self.tmpFile)

                fcpd.pdServer.send(f"0 pd open {fileName} {dirName}")
                self.isOpen = True
                self.skipChange = 0

                # watch for file change
                self.fs_watcher = QtCore.QFileSystemWatcher([self.tmpFile])
                self.fs_watcher.fileChanged.connect(self.fileChanged)

                # auto save pd file when document is saved
                class MyObserver(object):
                    def __init__(self, target_doc, caller, fileName):
                        self.target_doc = target_doc
                        self.caller = caller
                        self.fileName = fileName

                    def slotStartSaveDocument(self, doc, label):
                        if doc == self.target_doc:
                            Log("FCPD", "Ask PD to save\n")
                            self.caller.pdServer.send("0 pd-{self.fileName} menusave;")
                            Gui.updateGui()
                            # give PD 500ms to save
                            time.sleep(0.5)
                            # store the file back
                            self.caller.fileChanged(self.caller.tmpFile)
                            self.caller.skipChange = 2
                            self.caller.object.recompute(True)

                self.docObserver = MyObserver(App.ActiveDocument, self, fileName)
                App.addDocumentObserver(self.docObserver)

    def fileChanged(self, filename):
        if self.skipChange > 0:
            self.skipChange -= 1
        elif os.path.exists(self.tmpFile):
            Log("FCPD", f"{self.tmpFile} changed\n")
            self.object.PDFile = self.tmpFile
            App.ActiveDocument.recompute()
        else:
            Log("FCPD", f"{self.tmpFile} deleted\n")

    def endEdit(self):
        Log("FCPD", f"{self.tmpFile} closed\n")
        try:
            os.remove(self.tmpFile)
            os.remove(self.tmpFile + "_")
            del self.fs_watcher
        except FileNotFoundError:
            pass
        App.removeDocumentObserver(self.docObserver)
        self.isOpen = False

    def onDocumentRestored(self, obj):
        self.object = obj
        self.isOpen = False

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
    obj = App.ActiveDocument.addObject("App::FeaturePython", "PDInclude")
    PDInclude(obj)
    PDIncludeViewProvider(obj.ViewObject, obj)
    return obj


def createWithEmpty():
    obj = create()
    _, tmpFile = tempfile.mkstemp()
    createPDFile(tmpFile)
    obj.PDFile = tmpFile
    Gui.updateGui()
    obj.Proxy.startEdit()
