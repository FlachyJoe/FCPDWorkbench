# -*- coding: utf-8 -*-
###################################################################################
#
#  pdcontrolertools.py
#
#  Copyright 2021 Flachy Joe
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
import pdcontroler
from pdmsgtranslator import PDMsgTranslator

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError


def registerToolList(pdServer):
    toolList = [("ctrlr", pdCtrlr),
                ("newctrlr", pdNewCtrlr)
                ]

    for word, func in toolList:
        pdServer.registerMessageHandler([word], func)


def pdCtrlr(pdServer, words):
    pdControler = pdcontroler.get()
    _, values = PDMsgTranslator.popValues(words[2:])
    ret = []
    for ind, (val, typ) in enumerate(values):
        ret += pdControler.Proxy.setProperty(ind, typ, val)
    return '\n'.join(ret)


def pdNewCtrlr(pdServer, words):
    pdControler = pdcontroler.create(pdServer, words[0])
    try:
        outStart = words.index('|')
    except ValueError:
        outStart = len(words)
    inTyp = [PDMsgTranslator.fcType(w) for w in words[2:outStart]]
    outTyp = [PDMsgTranslator.fcType(w) for w in words[outStart+1:]]

    for ind, t in enumerate(inTyp):
        pdControler.Proxy.setIncommingPropertyType(ind, t)
    for ind, t in enumerate(outTyp):
        pdControler.Proxy.setOutgoingPropertyType(ind, t)

    return 'SERVICE %i %i' % (len(inTyp), len(outTyp))
