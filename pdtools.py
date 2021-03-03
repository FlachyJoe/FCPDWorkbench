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


def value_from_str(words):
    "return a FreeCAD value from a string"
    return_value = None
    used_words = 0
    if words:
        try:
            return_value = float(words[0])
            used_words = 1
        except ValueError:
            if words[0] in ["Vector", "Pos"]:
                return_value = App.Vector(float(words[1]), float(words[2]), float(words[3]))
                used_words = 4
            elif words[0] in ["Rotation", "Yaw-Pitch-Roll", "Rot"]:
                return_value = App.Rotation(float(words[1]), float(words[2]), float(words[3]))
                used_words = 4
            elif words[0] == "Placement":
                return_value = App.Placement(value_from_str(words[1:5])[0], value_from_str(words[5:])[0])
                used_words = 9
            elif words[0] == "List":
                return_value = []
                count = words[1]
                used_words = 2
                for i in range(0, count):
                    val, cnt = value_from_str(words[used_words:])
                    return_value.append(val)
                    used_words += cnt
            elif words[0] == "True":
                return_value = True
                used_words = 1
            elif words[0] == "False":
                return_value = False
                used_words = 1
            elif words[0] == "None":
                return_value = None
                used_words = 1
            else:
                try:
                    return_value = App.Units.parseQuantity(''.join(words))
                    used_words = len(words)
                except Exception:
                    Log(sys.exc_info())
                    Log(" value_from_str [%s] \r\n" % words)
    return (return_value, used_words)


def pop_values(words, count):
    "use words to get values"
    values = []
    for i in range(count):
        val, cnt = value_from_str(words)
        values.append(val)
        words = words[cnt:]
    return (words, values)


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
        obj = App.ActiveDocument.getObject(words[3])
        return obj.getPropertyByName(words[4])
    elif words[2] == "constraint":
        skc = App.ActiveDocument.getObject(words[3])
        return skc.getDatum(words[4])


def pdSet(pd_server, words):
    if words[2] == "property":
        obj = App.ActiveDocument.getObject(words[3])
        return setattr(obj, words[4], value_from_str(words[5:])[0])
    elif words[2] == "constraint":
        skc = App.ActiveDocument.getObject(words[3])
        return skc.setDatum(words[4],  value_from_str(words[5:])[0])


def pdCopy(pd_server, words):
    obj = App.ActiveDocument.getObject(words[2])
    obj2 = App.ActiveDocument.copyObject(obj, False, False)
    for prt in [tpl[0] for tpl in obj.Parents]:
        prt.addObject(obj2)
    return obj2.Name


def pdDelete(pd_server, words):
    for obj in words[2:]:
        App.ActiveDocument.removeObject(obj)


def pdRecompute(pd_server, words):
    App.ActiveDocument.recompute()


def pdSelObserver(pd_server, words):
    # See https://wiki.freecadweb.org/Code_snippets#Function_resident_with_the_mouse_click_action
    class SelObserver:
        def __init__(self, pd_server, uid):
            self.pd_server = pd_server
            self.uid = uid

        def send(self):
            sel = App.Gui.Selection.getSelection()
            objList = [obj.Name for obj in sel]
            self.pd_server.send("%s %s;" % (self.uid, self.pd_server._spacer(str(objList))))

        def addSelection(self, doc, obj, sub, pnt):
            self.send()

        def removeSelection(self, doc, obj, sub):
            self.send()

        def setSelection(self, doc):
            self.send()

        def clearSelection(self, doc):
            self.send()

    s = SelObserver(pd_server, words[0])
    pd_server.objects_store[words[0]] = s   # store the observer to allow removing later
    App.Gui.Selection.addObserver(s)
    return 'OK'


def pdObjObserver(pd_server, words):
    '''bang when mouse enter the object'''
    class PreSelObserver:
        def __init__(self, pd_server, uid, obj):
            self.pd_server = pd_server
            self.uid = uid
            self.obj = obj

        def setPreselection(self, doc, obj, sub):
            if obj == self.obj:
                self.pd_server.send("%s %s;" % (self.uid, 'bang'))
    s = PreSelObserver(pd_server, words[0], words[2])
    pd_server.objects_store[words[0]] = s   # store the observer to allow removing later
    App.Gui.Selection.addObserver(s)
    return 'OK'


def pdRemObserver(pd_server, words):
    # Uninstall the resident function
    App.Gui.Selection.removeObserver(pd_server.objects_store[words[0]])
    del pd_server.objects_store[words[0]]
    return 'OK'


def pdLink(pd_server, words):
    doc = App.ActiveDocument
    obj = doc.getObject(words[2])
    lnk = doc.addObject('App::Link', 'Link')
    lnk.setLink(obj)
    lnk.Label = obj.Label
    return lnk.Name


def pdByLabel(pd_server, words):
    doc = App.ActiveDocument
    lst = doc.getObjectsByLabel(words[2])
    return [o.Name for o in lst]


def pdObject(pd_server, words):
    doc = App.ActiveDocument
    objMod = words[2].title()
    objType = words[3].title()
    obj = doc.addObject('%s::%s' % (objMod, objType), objType)
    current = 4
    while current < len(words):
        propName = words[current]
        propValue, used = value_from_str(words[current+1:])
        current += used+1
        if hasattr(obj, propName):
            setattr(obj, propName, propValue)
    return obj.Name


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
            _, args = pop_values(words[3:], pcount)
            shape = func(*args)
            Part.show(shape)
            return App.ActiveDocument.ActiveObject.Name
#                                  PART WORKBENCH #
###################################################


###################################################
# DRAFT WORKBENCH                                 #
def pdDraft(pd_server, words):
    import Draft
    shape = None
    func_name = "make_" + words[2]
    if hasattr(Draft, func_name):
        func = getattr(Draft, func_name)
        pcount = getParametersCount(func)
        _, args = pop_values(words[3:], pcount)
        shape = func(*args)

    if hasattr(shape, 'Name'):
        return shape.Name
    else:
        return str(shape)
#                                 DRAFT WORKBENCH #
###################################################
