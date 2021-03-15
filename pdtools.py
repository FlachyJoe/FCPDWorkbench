# -*- coding: utf-8 -*-
###################################################################################
#
#  pdtools.py
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

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError


def registerToolList(pd_server):
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
                ("Part", pdPart),
                ("Draft", pdDraft),
                ]

    for word, func in toolList:
        pd_server.register_message_handler([word], func)
    pd_server.default_message_handler = pdElse


def pdElse(words):
    pass


def pdGet(pd_server, words):
    if words[2] == "selection":
        sel = App.Gui.Selection.getSelection()
        objList = [obj.Name for obj in sel]
        return objList
    elif words[2] == "property":
        obj = pd_server.value_from_str(words[3])[0]
        return obj.getPropertyByName(words[4])
    elif words[2] == "constraint":
        skc = pd_server.value_from_str(words[3])[0]
        return skc.getDatum(words[4])
    elif words[2] == "reference":
        return App.ActiveDocument.getObject(words[3])


def pdSet(pd_server, words):
    if words[2] == "property":
        obj = pd_server.value_from_str(words[3])[0]
        val = pd_server.value_from_str(words[5:])[0]
        return setattr(obj, words[4], val)

    elif words[2] == "constraint":
        skc = pd_server.value_from_str(words[3])[0]
        return skc.setDatum(words[4],  pd_server.value_from_str(words[5:])[0])


def pdCopy(pd_server, words):
    ''' copy Object --> NewObjectName '''
    obj = pd_server.value_from_str(words[2])[0]
    obj2 = App.ActiveDocument.copyObject(obj, False, False)
    for prt in [tpl[0] for tpl in obj.Parents]:
        prt.addObject(obj2)
    return obj2.Name


def pdDelete(pd_server, words):
    ''' delete ObjectName --> bang '''
    for obj in words[2:]:
        App.ActiveDocument.removeObject(obj)


def pdRecompute(pd_server, words):
    ''' recompute --> bang '''
    App.ActiveDocument.recompute()


def pdSelObserver(pd_server, words):
    '''selobserver --> "OK" at creation
            --> list of selected objects when selection changes'''
    # See https://wiki.freecadweb.org/Code_snippets#Function_resident_with_the_mouse_click_action
    class SelObserver:
        def __init__(self, pd_server, uid):
            self.pd_server = pd_server
            self.uid = uid

        def send(self):
            sel = App.Gui.Selection.getSelection()
            objList = [obj.Name for obj in sel]
            self.pd_server.send(self.uid, objList)

        def addSelection(self, doc, obj, sub, pnt):
            self.send()

        def removeSelection(self, doc, obj, sub):
            self.send()

        def setSelection(self, doc):
            self.send()

        def clearSelection(self, doc):
            self.send()

    s = SelObserver(pd_server, words[0])
    pd_server.observers_store[words[0]] = s   # store the observer to allow removing later
    App.Gui.Selection.addObserver(s)
    return 'OK'


def pdObjObserver(pd_server, words):
    '''objobserver ObjectName   --> "OK" at creation
                         --> bang when mouse enter the object'''
    class PreSelObserver:
        def __init__(self, pd_server, uid, obj):
            self.pd_server = pd_server
            self.uid = uid
            self.obj = obj

        def setPreselection(self, doc, obj, sub):
            if obj == self.obj:
                self.pd_server.send("%s %s;" % (self.uid, 'bang'))
    s = PreSelObserver(pd_server, words[0], words[2])
    pd_server.observers_store[words[0]] = s   # store the observer to allow removing later
    App.Gui.Selection.addObserver(s)
    return 'OK'


def pdRemObserver(pd_server, words):
    '''remobserver --> "OK" '''
    # Uninstall the resident function
    App.Gui.Selection.removeObserver(pd_server.observers_store[words[0]])
    del pd_server.observers_store[words[0]]
    return 'OK'


def pdLink(pd_server, words):
    ''' link Object --> NewObjectName '''
    doc = App.ActiveDocument
    obj = pd_server.value_from_str(words[2])[0]
    lnk = doc.addObject('App::Link', 'Link')
    lnk.setLink(obj)
    lnk.Label = obj.Label
    return lnk.Name


def pdByLabel(pd_server, words):
    ''' bylabel Label  --> [Objects] '''
    doc = App.ActiveDocument
    lst = doc.getObjectsByLabel(words[2])
    return [o.Name for o in lst]


def pdObject(pd_server, words):
    ''' Object Module Type [Property1 Value1 Property2 Value2 ...]  --> NewObjectName '''
    doc = App.ActiveDocument
    objMod = words[2].title()
    objType = words[3].title()
    obj = doc.addObject('%s::%s' % (objMod, objType), objType)
    current = 4
    while current < len(words):
        propName = words[current]
        propValue, used = pd_server.value_from_str(words[current+1:])
        current += used+1
        if hasattr(obj, propName):
            setattr(obj, propName, propValue)
    return obj.Name


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
            paramstr = docstr[leftpar:rightpar]
            paramstr = paramstr.replace("[", "")
            paramstr = paramstr.replace("]", "")
            paramstr = paramstr.replace("\n", "")
            params = paramstr.split(",")
    return len(params)


###################################################
# PART WORKBENCH                                  #
def pdPart(pd_server, words):
    import Part
    if words[2].startswith('make'):
        shape = None
        func_name = words[2]
        if hasattr(Part, func_name):
            func = getattr(Part, func_name)
            pcount = getParametersCount(func)
            _, args = pd_server.pop_values(words[3:], pcount)
            shape = func(*args)
            Part.show(shape)
            return App.ActiveDocument.ActiveObject.Name
    else:
        result = None
        func_name = words[2]
        if hasattr(Part, func_name):
            func = getattr(Part, func_name)
            pcount = getParametersCount(func)
            _, args = pd_server.pop_values(words[3:], pcount)
            return func(*args)

#                                  PART WORKBENCH #
###################################################


###################################################
# DRAFT WORKBENCH                                 #
def pdDraft(pd_server, words):
    import Draft
    shape = None
    func_name = words[2]
    if hasattr(Draft, func_name):
        func = getattr(Draft, func_name)
        pcount = getParametersCount(func)
        _, args = pd_server.pop_values(words[3:], pcount)
        shape = func(*args)
        if hasattr(shape, 'Name'):
            return shape.Name
        # if no Name return a reference
        return shape
#                                 DRAFT WORKBENCH #
###################################################
