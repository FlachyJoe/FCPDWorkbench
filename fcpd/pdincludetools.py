# -*- coding: utf-8 -*-
###################################################################################
#
#  pdincludetools.py
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

# this module translate pd message to action for PDInclude

import FreeCAD as App

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError


def registerToolList(pdServer):
    toolList = [("endedit", pdEndEdit)
                ]
    for word, func in toolList:
        pdServer.registerMessageHandler([word], func)


def pdEndEdit(pdServer, words):
    # find pdinclude object which use the given filename
    pyObjects = App.ActiveDocument.findObjects('App::FeaturePython')
    try:
        obj = [o for o in pyObjects if (hasattr(o, 'Proxy')
                                        and hasattr(o.Proxy, 'tmpFile')
                                        and o.Proxy.tmpFile.endswith(words[2])
                                        )][0]
        obj.Proxy.endEdit()
    except IndexError:
        return "ERROR given filename is not valid %s" % words[2]


