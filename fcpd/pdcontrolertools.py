# -*- coding: utf-8 -*-
###################################################################################
#
#  pdcontrolertools.py
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
###################################################################################

# this module translate pd message to action for [fc_controler]

import FreeCAD as App
from . import pdcontroler

from . import pdmsgtranslator

PDMsgTranslator = pdmsgtranslator.PDMsgTranslator

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError


def registerToolList(pdServer):
    toolList = [("ctrlr", pdCtrlr), ("newctrlr", pdNewCtrlr)]

    for word, func in toolList:
        pdServer.registerMessageHandler([word], func)


def pdCtrlr(pdServer, words):
    pdControler = pdcontroler.create(pdServer, words[0])
    _, values = PDMsgTranslator.popValues(words[2:])
    # create a list of (ind, ROValue)
    duplet = [(values[i].value, values[i + 1]) for i in range(0, len(values), 2)]

    for ind, val in duplet:
        pdControler.Proxy.setProperty(ind, val.type, val.value)


def pdNewCtrlr(pdServer, words):
    pdControler = pdcontroler.create(pdServer, words[0])
    pdControler.Proxy.resetIncommingProperties()
    pdControler.Proxy.resetOutgoingProperties()

    try:
        outStart = words.index("|")
    except ValueError:
        outStart = len(words)
    inTyp = [PDMsgTranslator.fcType(w) for w in words[2:outStart]]
    outTyp = [PDMsgTranslator.fcType(w) for w in words[outStart + 1 :]]

    for ind, t in enumerate(inTyp):
        pdControler.Proxy.setIncommingPropertyType(ind, t)
    for ind, t in enumerate(outTyp):
        pdControler.Proxy.setOutgoingPropertyType(ind, t)
