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

def value_from_str(words):
    "return a FreeCAD value from a string"

    return_value = None

    if words[0] in ["Vector", "Pos"]:
        return_value = App.Vector(float(words[1]),float(words[2]),float(words[3]))
    elif words[0] in ["Rotation", "Yaw-Pitch-Roll", "Rot"]:
        return_value = App.Rotation(float(words[1]),float(words[2]),float(words[3]))
    elif words[0]=="Placement":
        return_value = App.Placement(value_from_str(words[1:5]), value_from_str(words[5:]))
    else:
        try :
            return_value = App.Units.parseQuantity(''.join(words))
        except:
            Log(sys.exc_info())
            Log("[%s] \r\n" % words[0])

    return return_value


def registerToolList(pd_server):
    toolList = [("get", pdGet),
                ("set", pdSet),
                ("copy", pdCopy),
                ("delete", pdDelete),
                ("recompute", pdRecompute),
                ("Part", pdPart)]

    for word,func in toolList:
        pd_server.register_message_handler([word], func)
    pd_server.default_message_handler = pdElse


def pdElse(words):
    pass


def pdGet(words):
    if words[2] == "selection":
        sel = Gui.Selection.getSelection()
        objList = [obj.Name for obj in sel]
        return objList
    elif words[2] == "property":
        obj = App.ActiveDocument.getObject(words[3])
        return obj.getPropertyByName(words[4])
    elif words[2] == "constraint":
        skc = App.ActiveDocument.getObject(words[3])
        return skc.getDatum(words[4])


def pdSet(words):
    if words[2] == "property":
        obj = App.ActiveDocument.getObject(words[3])
        return setattr(obj,words[4], value_from_str(words[5:]))
    elif words[2] == "constraint":
        skc = App.ActiveDocument.getObject(words[3])
        return skc.setDatum(words[4],  value_from_str(words[5:]))


def pdCopy(words):
    obj = App.ActiveDocument.getObject(words[2])
    obj2 = App.ActiveDocument.copyObject(obj, False, False)
    for prt in [tpl[0] for tpl in obj.Parents]:
        prt.addObject(obj2)
    return obj2.Name


def pdDelete(words):
    for obj in words[2:]:
        App.ActiveDocument.removeObject(obj)


def pdRecompute(words):
        App.ActiveDocument.recompute()


def pdPart(words):
    if words[2] == "create":
        if words[3] == "Loft":
            doc = App.ActiveDocument
            loft = doc.addObject('Part::Loft','Loft')
            loft.Sections=[doc.getObject(name) for name in words[4:]]
            loft.Solid = True
            return loft.Name
