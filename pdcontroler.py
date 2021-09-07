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

        obj.Group = [self.controlerInput, self.controlerOutput]
        obj.setPropertyStatus('Group', 'ReadOnly')

    def onChanged(self, obj, prop):
        if str(prop) == 'Group':
            obj.Group = [self.controlerInput, self.controlerOutput]

    def setIncommingPropertyType(self, ind, typ):
        name = 'DataFlow_%i' % ind
        # Check existence
        if hasattr(App.ActiveDocument.IncommingData, name):
            App.ActiveDocument.IncommingData.removeProperty(name)

        # App:PropertyRotation doesn't exist so store it in a placement
        if typ == 'rotation':
            typ = 'App::PropertyPlacement'

        self.controlerInput.addProperty(typ, name, '', 'IncommingDataFlow')
        self.controlerInput.setPropertyStatus(name, 'ReadOnly')


    def setOutgoingPropertyType(self, ind, typ):
        name = 'DataFlow_%i' % ind
        # Check existence
        if hasattr(App.ActiveDocument.OutgoingData, name):
            App.ActiveDocument.OutgoingData.removeProperty(name)

        # App:PropertyRotation doesn't exist so store it in a placement
        if typ == 'rotation':
            typ = 'App::PropertyPlacement'

        self.controlerOutput.addProperty(typ, name, '', 'OutgoingDataFlow')

    def setProperty(self, ind, typ, value):
        name = 'DataFlow_%i' % ind

        # App:PropertyRotation doesn't exist so store it in a placement
        if typ == 'rotation':
            value = App.Placement(App.Vector(0,0,0), value)

        try :
            setattr(self.controlerInput.Object, name, value)
        except AttributeError:
            self.controlerInput.Object.addProperty(typ, name, '', 'IncommingDataFlow')
            self.controlerInput.Object.setPropertyStatus(name, 'ReadOnly')
            setattr(self.Object, name, value)

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
        #self.Object = obj
        self.Type = "PDControlerInput"


class PDControlerOutput:
    def __init__(self, obj, pdServer, dollarZero):

        obj.Proxy = self
        self.Type = "PDControlerOutput"

        self.pdServer = pdServer
        self.dollarZero = dollarZero

        self.propToSend = []

    def onChanged(self, obj, prop):
        if not prop[:8] == 'DataFlow':
            return
        self.propToSend.append(prop)

    def execute(self, obj):
        # send changed properties right to left
        for prop in sorted(set(self.propToSend), reverse=True):
            ind = int(prop[9:])
            self.pdServer.send(self.dollarZero, ind, getattr(obj, prop))
        self.propToSend = []


def isPDControler(obj):
    if hasattr(obj, 'Proxy') and hasattr(obj.Proxy, 'Type'):
        return obj.Proxy.Type == "PDControler"
    return False

def get():
    # Return the PDControler if it already exists
    for obj in App.ActiveDocument.Objects:
        if isPDControler(obj):
            return obj
    return None

def create(pdServer, dollarZero):
    """
    Object creation method
    """
    curObj = get()
    if get() is not None:
        pdOut = curObj.Proxy.controlerOutput.Proxy
        pdOut.pdServer = pdServer
        pdOut.dollarZero = dollarZero
        return curObj
    else:
        pdIn = App.ActiveDocument.addObject('App::FeaturePython', 'IncommingData')
        pdOut = App.ActiveDocument.addObject('App::FeaturePython', 'OutgoingData')
        obj = App.ActiveDocument.addObject('App::DocumentObjectGroupPython', 'PDControler')

        PDControlerInput(pdIn)
        PDControlerOutput(pdOut, pdServer, dollarZero)
        PDControler(obj, pdIn, pdOut)
        PDControlerViewProvider(obj.ViewObject)
        return obj
