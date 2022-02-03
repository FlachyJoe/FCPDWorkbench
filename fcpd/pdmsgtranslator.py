# -*- coding: utf-8 -*-
###################################################################################
#
#  pdmsgtranslator.py
#
#  Copyright 2021 Florian Foinant-Willig <ffw@2f2v.fr>
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

# this module translate PD message to/from Python values

import numbers

import FreeCAD as App

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError


class PDMsgTranslator:
    NOT_SET = ''
    FLOAT = 'App::PropertyFloat'
    INT = 'App::PropertyInteger'
    VECTOR = 'App::PropertyVector'
    ROTATION = 'rotation'
    PLACEMENT = 'App::PropertyPlacement'
    LIST = 'list'
    BOOL = 'App::PropertyBool'
    STRING = 'App::PropertyString'
    OBJECT = 'App::PropertyLink'
    QUANTITY = 'App::PropertyQuantity'
    ANGLE = 'App::PropertyAngle'
    FC_TYPES = [NOT_SET, FLOAT, INT, VECTOR, ROTATION, PLACEMENT, LIST, BOOL,
                STRING, OBJECT, QUANTITY, ANGLE]
    SHORT_TYPES = ['0', 'f', 'i', 'v', 'r', 'p', 'l', 'b',
                   's', 'o', 'q', 'a']
    LONG_TYPES = ['empty', 'float', 'integer', 'vector', 'rotation', 'placement', 'list', 'boolean',
                  'string', 'object', 'quantity', 'angle']

    objectsStore = []  # store binary untextable objects to get them back by reference

    ## Return a string representation of a value
    #  @param self
    #  @param val the value to convert
    #  @return a valid PureData message
    @classmethod
    def strFromValue(cls, val):
        if isinstance(val, list):
            if len(val) > 1:
                string = "list %i" % len(val)
                for v in val:
                    string += " %s" % cls.strFromValue(v)
            elif len(val) == 1:
                # don't send list with one element
                string = cls.strFromValue(val[0])
            else:
                # empty list
                string = 'None'
        elif (isinstance(val, numbers.Number) or
              isinstance(val, bool) or
              isinstance(val, App.Vector) or
              isinstance(val, App.Rotation) or
              isinstance(val, App.Placement)
             ):
            string = str(val)
        elif isinstance(val, str):
            string = val
        else:
            # store this object and return a ref
            try:
                return "^%i" % cls.objectsStore.index(val)
            except ValueError:
                cls.objectsStore.append(val)
                return "^%i" % (len(cls.objectsStore)-1)

        return string.translate(str.maketrans(',=', '  ', ';()[]{}"\''))

    ## Return a value from a PureData message
    #  @param self
    #  @param words a PureData message splits by words
    #  @return (ROValue, usedWords_count)
    @classmethod
    def valueFromStr(cls, words):
        retValue = cls.NOT_SET
        retType = cls.NOT_SET

        usedWords = 0
        if words:
            if not isinstance(words, list):
                words = [words]
            try:
                # float...
                retValue = float(words[0])
                retType = cls.FLOAT
                if int(retValue) == retValue:
                    # ...or int
                    retValue = int(retValue)
                    retType = cls.INT
                usedWords = 1
            except ValueError:
                if words[0] in ["Vector", "Pos"]:
                    retValue = App.Vector(float(words[1]), float(words[2]), float(words[3]))
                    retType = cls.VECTOR
                    usedWords = 4
                elif words[0] == "Ox":
                    retValue = App.Vector(1, 0, 0)
                    retType = cls.VECTOR
                    usedWords = 1
                elif words[0] == "Oy":
                    retValue = App.Vector(0, 1, 0)
                    retType = cls.VECTOR
                    usedWords = 1
                elif words[0] == "Oz":
                    retValue = App.Vector(0, 0, 1)
                    retType = cls.VECTOR
                    usedWords = 1
                elif words[0] in ["Rotation", "Yaw-Pitch-Roll", "Rot"]:
                    retValue = App.Rotation(float(words[1]), float(words[2]), float(words[3]))
                    retType = cls.ROTATION
                    usedWords = 4
                elif words[0] == "Placement":
                    retValue = App.Placement(cls.valueFromStr(words[1:5])[0].value,
                                             cls.valueFromStr(words[5:])[0].value)
                    retType = cls.PLACEMENT
                    usedWords = 9
                elif words[0] == "list":
                    retValue = []
                    retType = cls.LIST
                    count = int(words[1])
                    usedWords = 2
                    for _ in range(0, count):
                        val, cnt = cls.valueFromStr(words[usedWords:])
                        retValue.append(val.value)
                        usedWords += cnt
                elif words[0] == "True":
                    retValue = True
                    retType = cls.BOOL
                    usedWords = 1
                elif words[0] == "False":
                    retValue = False
                    retType = cls.BOOL
                    usedWords = 1
                elif words[0] == "None":
                    retValue = None
                    usedWords = 1
                elif words[0].startswith('"'):
                    # String
                    # find closing quote
                    strLen = [i for (i, w) in enumerate(words)
                              if isinstance(w, str) and w.endswith('"')
                              ][0] + 1
                    # create the string
                    retValue = ' '.join(map(str, words[:strLen])).replace('"', '')
                    retType = cls.STRING
                    usedWords = strLen
                elif words[0].startswith("^"):
                    # Reference to a stored object
                    index = int(words[0][1:])
                    retValue = cls.objectsStore[index]
                    retType = cls.OBJECT
                    Log("%s refers to %s\n" % (words[0], str(retValue)))
                    usedWords = 1
                elif App.ActiveDocument is not None and App.ActiveDocument.getObject(words[0]):
                    # ActiveDocument Object
                    retValue = App.ActiveDocument.getObject(words[0])
                    retType = cls.OBJECT
                    usedWords = 1
                else:
                    # Quantity
                    try:
                        retValue = App.Units.parseQuantity(words[0])
                        retType = cls.QUANTITY
                        usedWords = 1
                    except OSError:
                        # String
                        retValue = words[0]
                        retType = cls.STRING
                        usedWords = 1
        return (ROValue(retValue, retType), usedWords)

    ## Extract a given number of values from a PureData message
    #  @param self
    #  @param words a PureData message splits by words
    #  @param count number of value to extract or "all" to consume all the words
    #  @return a couple (remaining words, [ROValue])
    @classmethod
    def popValues(cls, words, count="all", ignoreNotSet=False):
        values = []
        if count == "all":
            while words:
                val, cnt = cls.valueFromStr(words)
                values.append(ROValue(*val))
                words = words[cnt:]
            if ignoreNotSet:
                return ([], cls.filterNotSet(values))
            return ([], values)

        for _ in range(count):
            val, cnt = cls.valueFromStr(words)
            values.append(ROValue(*val))
            words = words[cnt:]
        if ignoreNotSet:
            return (words, cls.filterNotSet(values))
        return (words, values)

    @classmethod
    def filterNotSet(cls, valList):
        return [val for val in valList if val.isSet()]

    @classmethod
    def fcType(cls, short):
        return cls.FC_TYPES[cls.SHORT_TYPES.index(short)]


class ROValue:
    """A read-only typed value"""

    def __init__(self, value, typ):
        self._value = value
        self._type = typ

    @property
    def value(self):
        """Get the current value."""
        return self._value

    @property
    def type(self):
        """Get the current type."""
        return self._type

    def __getitem__(self, key):
        """Allow access as list"""
        if key == 0:
            return self._value
        elif key == 1:
            return self._type
        raise IndexError()

    def isSet(self):
        """Return True if the value is set"""
        return self._value != PDMsgTranslator.NOT_SET
