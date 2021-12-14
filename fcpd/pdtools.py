# -*- coding: utf-8 -*-
###################################################################################
#
#  pdtools.py
#
#  Copyright 2020 Florian Foinant-Willig <ffw@2f2v.fr>
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

# this module translate pd message to action

import FreeCAD as App

from . import pdmsgtranslator
PDMsgTranslator = pdmsgtranslator.PDMsgTranslator

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError


def registerToolList(pdServer):
    toolList = [("get", pdGet),
                ("set", pdSet),
                ("copy", pdCopy),
                ("delete", pdDelete),
                ("recompute", pdRecompute),
                ("selobserver", pdSelObserver),
                ("objobserver", pdObjObserver),
                ("remobserver", pdRemObserver),
                ("link", pdLink),
                ("bylabel", pdByLabel),
                ("Object", pdObject),
                ("onMove", pdOnMove),
                ("matrixPlacement", pdMatrixPlacement),
                ("Part", pdPart),
                ("Shape", pdShape),
                ("Draft", pdDraft),
                ]

    for word, func in toolList:
        pdServer.registerMessageHandler([word], func)
    pdServer.defaultMessageHandler = pdElse


def pdElse(words):
    return "ERROR unknown or unallowed command (see the FCPDWorkbench preference page to allow raw python commands)."


def pdGet(pdServer, words):
    if words[2] == "selection":
        sel = App.Gui.Selection.getSelection()
        objList = [obj.Name for obj in sel]
        return objList
    elif words[2] == "property":
        obj = PDMsgTranslator.valueFromStr(words[3])[0].value
        return getattr(obj, words[4])
    elif words[2] == "constraint":
        skc = PDMsgTranslator.valueFromStr(words[3])[0].value
        return skc.getDatum(words[4])
    elif words[2] == "reference":
        return App.ActiveDocument.getObject(words[3])


def pdSet(pdServer, words):
    if words[2] == "property":
        obj = PDMsgTranslator.valueFromStr(words[3])[0].value
        val = PDMsgTranslator.valueFromStr(words[5:])[0].value
        return setattr(obj, words[4], val)

    elif words[2] == "constraint":
        skc = PDMsgTranslator.valueFromStr(words[3])[0].value
        return skc.setDatum(words[4], PDMsgTranslator.valueFromStr(words[5:])[0].value)


def pdCopy(pdServer, words):
    ''' copy Object --> NewObjectName '''
    obj = PDMsgTranslator.valueFromStr(words[2])[0].value
    copyDep = False
    if len(words) > 3:
        copyDep = PDMsgTranslator.valueFromStr(words[3])[0].value
        copyDep = copyDep or copyDep == 1
    obj2 = App.ActiveDocument.copyObject(obj, copyDep, False)
    for prt in [tpl[0] for tpl in obj.Parents]:
        prt.addObject(obj2)
    return obj2.Name


def pdDelete(pdServer, words):
    ''' delete ObjectName --> bang '''
    for obj in words[2:]:
        App.ActiveDocument.removeObject(obj)


def pdRecompute(pdServer, words):
    ''' recompute --> bang '''
    App.ActiveDocument.recompute()


def pdSelObserver(pdServer, words):
    '''selobserver --> "OK" at creation
            --> list of selected objects when selection changes'''
    # See https://wiki.freecadweb.org/Code_snippets#Function_resident_with_the_mouse_click_action
    class SelObserver:
        def __init__(self, pdServer, uid):
            self.pdServer = pdServer
            self.uid = uid

        def send(self):
            sel = App.Gui.Selection.getSelection()
            objList = [obj.Name for obj in sel]
            self.pdServer.send(self.uid, objList)

        def addSelection(self, doc, obj, sub, pnt):
            self.send()

        def removeSelection(self, doc, obj, sub):
            self.send()

        def setSelection(self, doc):
            self.send()

        def clearSelection(self, doc):
            self.send()

    s = SelObserver(pdServer, words[0])
    pdServer.observersStore[words[0]] = s   # store the observer to allow removing later
    App.Gui.Selection.addObserver(s)
    return 'OK'


def pdObjObserver(pdServer, words):
    '''objobserver ObjectName   --> "OK" at creation
                                --> bang when mouse enter the object'''
    class PreSelObserver:
        def __init__(self, pdServer, uid, obj):
            self.pdServer = pdServer
            self.uid = uid
            self.obj = obj

        def setPreselection(self, doc, obj, sub):
            if obj == self.obj:
                self.pdServer.send("%s %s;" % (self.uid, 'bang'))
    s = PreSelObserver(pdServer, words[0], words[2])
    pdServer.observersStore[words[0]] = s   # store the observer to allow removing later
    App.Gui.Selection.addObserver(s)
    return 'OK'


def pdRemObserver(pdServer, words):
    '''remobserver --> "OK" '''
    # Uninstall the resident function
    try:
        App.Gui.Selection.removeObserver(pdServer.observersStore[words[0]])
        App.removeDocumentObserver(pdServer.observersStore[words[0]])
    except KeyError:
        return
    del pdServer.observersStore[words[0]]
    return 'OK'


def pdLink(pdServer, words):
    ''' link Object --> NewObjectName '''
    doc = App.ActiveDocument
    obj = PDMsgTranslator.valueFromStr(words[2])[0].value
    lnk = doc.addObject('App::Link', 'Link')
    lnk.setLink(obj)
    lnk.Label = obj.Label
    return lnk.Name


def pdByLabel(pdServer, words):
    ''' bylabel Label  --> [Objects] '''
    doc = App.ActiveDocument
    lst = doc.getObjectsByLabel(words[2])
    return [o.Name for o in lst]


def pdObject(pdServer, words):
    ''' Object Module Type [Property1 Value1 Property2 Value2 ...]  --> NewObjectName '''
    doc = App.ActiveDocument
    objMod = words[2]
    objType = words[3]
    obj = doc.addObject('%s::%s' % (objMod, objType), objType)
    current = 4
    while current < len(words):
        propName = words[current]
        prop, used = PDMsgTranslator.valueFromStr(words[current+1:])
        current += used+1
        if hasattr(obj, propName):
            setattr(obj, propName, prop.value)
    return obj.Name


def pdOnMove(pdServer, words):
    '''onMove ObjectName    --> "OK" at creation
                            --> placement when the object move'''
    class DocObserver:
        def __init__(self, pdServer, uid, obj):
            self.pdServer = pdServer
            self.uid = uid
            self.obj = obj
        def slotChangedObject(self, obj, prop):
            if obj.Label == self.obj and prop == "Placement":
                self.pdServer.send(self.uid, obj.Placement)

    s = DocObserver(pdServer, words[0], words[2])
    pdServer.observersStore[words[0]] = s   # store the observer to allow removing later
    App.addDocumentObserver(s)
    return "OK"


# return the count of parameters of the given function
def getParametersCount(func):
    try:
        import inspect
        params = list(inspect.signature(func).parameters.keys())
    except ValueError:
        # parse __doc__
        docstr = func.__doc__
        if docstr:
            leftpar = docstr.find("(")+1
            rightpar = docstr.find(")", leftpar)
            if rightpar > 0:
                paramstr = docstr[leftpar:rightpar]
                paramstr = paramstr.replace("[", "")
                paramstr = paramstr.replace("]", "")
                paramstr = paramstr.replace("\n", "")
                params = paramstr.split(",")
            else:
                params = []
                # TODO try to call the func without param and get info from error msg
    return len(params)


def pdMatrixPlacement(pdServer, words):
    val, _ = PDMsgTranslator.valueFromStr(words[2:])
    val = val.value
    if hasattr(val, 'flatten'):
        # numpy array case
        return App.Placement(App.Matrix(*val.flatten()))
    else:
        return App.Placement(App.Matrix(*val))


###################################################
# PART WORKBENCH                                  #
def pdPart(pdServer, words):
    import Part
    func_name = words[2]
    if hasattr(Part, func_name):
        func = getattr(Part, func_name)
        pcount = getParametersCount(func)
        _, values = PDMsgTranslator.popValues(words[3:], pcount, ignoreNotSet=True)
        args = [val.value for val in values]
        if words[2].startswith('make_'):
            shape = func(*args)
            Part.show(shape)
            return App.ActiveDocument.ActiveObject.Name
        else:
            return func(*args)
    else:
        return "ERROR unknown function Part.%s" % func_name


def pdShape(pdServer, words):
    import Part
    func_name = words[2]
    if hasattr(Part.Shape, func_name):
        theShape = PDMsgTranslator.valueFromStr(words[3])[0].value
        func = theShape.__getattribute__(func_name)
        pcount = getParametersCount(func)
        _, values = PDMsgTranslator.popValues(words[4:], pcount, ignoreNotSet=True)
        args = [val.value for val in values]
        return func(*args)
    else:
        return "ERROR unknown function Part.Shape.%s" % func_name

#                                  PART WORKBENCH #
###################################################


###################################################
# DRAFT WORKBENCH                                 #
def pdDraft(pdServer, words):
    import Draft
    shape = None
    func_name = words[2]
    if hasattr(Draft, func_name):
        func = getattr(Draft, func_name)
        pcount = getParametersCount(func)
        _, values = PDMsgTranslator.popValues(words[3:], pcount, ignoreNotSet=True)
        args = [val.value for val in values]
        shape = func(*args)
        if hasattr(shape, 'Name'):
            return shape.Name
        # if no Name return a reference
        return shape
    else:
        return "ERROR unknown function Draft.%s" % func_name
#                                 DRAFT WORKBENCH #
###################################################
