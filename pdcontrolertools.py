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

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError


def registerToolList(pdServer):
    toolList = [("ctrlr", pdCtrlr)
                ]

    for word, func in toolList:
        pdServer.registerMessageHandler([word], func)


def pdCtrlr(pdServer, words):
    pdControler = pdcontroler.create()
    _, values = pdServer.popValues(words[2:])
    for ind, (val, typ) in enumerate(values):
        pdControler.Proxy.controlerInput.Proxy.setProperty('DataFlow_%i' % ind, typ, val)
