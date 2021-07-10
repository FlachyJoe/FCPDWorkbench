###################################################################################
#
#  pdcontroler.py
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

import FreeCAD as App
import fcpdwb_locator as locator

class PDControler:
    def __init__(self, obj, controlerInput, controlerOutput):

        obj.Proxy = self

        self.Type = "PDControler"
        self.controlerInput = controlerInput
        self.controlerOutput = controlerOutput

        obj.addProperty('App::PropertyFileIncluded', 'PDPatch', '', 'The Pure-data patch').PDPatch =""
        obj.Group = [self.controlerInput, self.controlerOutput]
        obj.setPropertyStatus('Group','ReadOnly')

    def onChanged(self, fp, prop):
        if str(prop) == 'Group':
            fp.Group = [self.controlerInput, self.controlerOutput]
        # TODO load PD patch

    # ~ def onDocumentRestored(self, obj):
        # ~ pass

    def execute(self, obj):
        pass


class PDControlerViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def getIcon(self):
        return locator.icon('insert-link.png')


class PDControlerInput:
    def __init__(self, obj):

        obj.Proxy = self
        self.Object = obj
        self.Type = "PDControlerInput"

    def onChanged(self, fp, prop):
        # No change accepted : read-only properties
        pass

    def execute(self, obj):
        pass

    def setProperty(self, name, typ, value):
        try :
            setattr(self.Object, name, value)
        except AttributeError:
            self.Object.addProperty(typ, name, '', 'IncommingDataFlow')
            self.Object.setPropertyStatus(name, 'ReadOnly')
            setattr(self.Object, name, value)


class PDControlerOutput:
    def __init__(self, obj):

        obj.Proxy = self
        self.Type = "PDControlerOutput"

    def onChanged(self, fp, prop):
        # TODO send data to PD
        pass

    def execute(self, obj):
        pass


def isPDControler(obj):
    if hasattr(obj, 'Proxy') and  hasattr(obj.Proxy, 'Type'):
        return obj.Proxy.Type == "PDControler"
    return False


def create():
    """
    Object creation method
    """

    #Return the PDControler if it already exists
    for obj in App.ActiveDocument.Objects:
        if isPDControler(obj):
            return obj

    #Create a new one
    pdIn = App.ActiveDocument.addObject('App::FeaturePython', 'IncommingData')
    pdOut = App.ActiveDocument.addObject('App::FeaturePython', 'OutgoingData')
    obj = App.ActiveDocument.addObject('App::DocumentObjectGroupPython', 'PDControler')

    PDControlerInput(pdIn)
    PDControlerOutput(pdOut)
    PDControler(obj, pdIn, pdOut)
    PDControlerViewProvider(obj.ViewObject)

    return obj
