# -*- coding: utf-8 -*-
###################################################################################
#
#  pdgeometrictools.py
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

from scipy.spatial.transform import Rotation

import FreeCAD as App

from . import pdmsgtranslator
PDMsgTranslator = pdmsgtranslator.PDMsgTranslator

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError


def registerToolList(pdServer):
    toolList = [("matrixPlacement", pdMatrixPlacement),
                ("ypr2rpy", pdYPRtoRPY),
                ("rotationadd", pdRotationAdd),
                ("rotationminus", pdRotationMinus),
                ("placementadd", pdPlacementAdd),
                ("placementminus", pdPlacementMinus),
                ]
    for word, func in toolList:
        pdServer.registerMessageHandler([word], func)


def pdMatrixPlacement(pdServer, words):
    # matrix as list -> Placement
    # or numpy.matrix -> Placement
    val, _ = PDMsgTranslator.valueFromStr(words[2:])
    val = val.value
    if hasattr(val, 'flatten'):
        # numpy array case
        return App.Placement(App.Matrix(*val.flatten()))
    return App.Placement(App.Matrix(*val))


def pdYPRtoRPY(pdServer, words):
    # FreeCAD rotations use ZYX convention in deg, return xyz one in rad
    # Rotation -> list
    val, _ = PDMsgTranslator.valueFromStr(words[2:])
    fcRot = val.value
    scipyRot = Rotation.from_quat(fcRot.Q)
    return list(scipyRot.as_euler('xyz'))


def pdRotationAdd(pdServer, words):
    # Rotation, Rotation -> Rotation
    _, val = PDMsgTranslator.popValues(words[2:], 2)
    r1 = val[0].value
    r2 = val[1].value
    return r1*r2


def pdRotationMinus(pdServer, words):
    # Rotation, Rotation -> Rotation
    _, val = PDMsgTranslator.popValues(words[2:], 2)
    r1 = val[0].value
    r2 = val[1].value
    return r1*r2.inverted()


def pdPlacementAdd(pdServer, words):
    # Placement, Placement -> Placement
    _, val = PDMsgTranslator.popValues(words[2:], 2)
    p1 = val[0].value
    p2 = val[1].value
    return p1*p2


def pdPlacementMinus(pdServer, words):
    # Placement, Placement -> Placement
    _, val = PDMsgTranslator.popValues(words[2:], 2)
    p1 = val[0].value
    p2 = val[1].value
    return p2.inverse()*p1
