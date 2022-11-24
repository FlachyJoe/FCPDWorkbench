#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  pd-beautician.py
#
#  Copyright 2022 Florian Foinant <ffw@2f2v.fr>
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

from os import path
from os.path import dirname, basename, splitext, join
import argparse

from PdParser import *

# where to look for text around sockets
MAX_TEXT_DISTANCE = 50

# Labels dimensions
SOCKET_HEIGHT = 2
SOCKET_WIDTH = 10
LABEL_HEIGHT = 10
LABEL_WIDTH = 75

TITLE_HEIGHT = 15

# template for socket & socket's label
def cnvSocket(x, y):
    return Canvas(x=x, y=y, width=SOCKET_WIDTH, height=SOCKET_HEIGHT,
                  background="#000000", boxSize=SOCKET_HEIGHT)

def cnvLabel(x, y, text):
    return Canvas(x=x, y=y, width=LABEL_WIDTH, height=LABEL_HEIGHT, dX=5, dY=6,
                  text=text, textSize=8, boxSize=LABEL_HEIGHT,
                  background="#000000", foreground="#ffffff")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# process the input file and print the result in stdout
def main():
    parser = argparse.ArgumentParser(description='Beautify a PureData patch')
    parser.add_argument('--icon', type=str, help='GIF to show as icon', dest='icon')
    parser.add_argument('input', type=str, help='file to process')
    parser.add_argument('output', type=str, help='file to store result', default='-')

    args = parser.parse_args()

    filename: str = args.input
    patch = Patch.fromFile(filename)
    title, _ = splitext(basename(filename))

    if patch.coords and int(patch.coords[0].gop) > 0:
        eprint("GOP already set, pass.")
        return 0

    # retrieve objects
    allTexts = patch.getDefOfType("text")
    inlets = patch.getDefOfType("inlet") + patch.getDefOfType("inlet~")
    outlets = patch.getDefOfType("outlet") + patch.getDefOfType("outlet~")

    if (not allTexts
    or (not inlets and not outlets)):
        eprint("nothing to show, pass.")
        return 0

    # GraphOnParent dimensions
    gopWidth = max(len(title)*7 + 16, LABEL_WIDTH * max(len(inlets), len(outlets)) + 10)
    gopHeight = 2 * LABEL_HEIGHT + TITLE_HEIGHT + 10

    gopLeft = min(patch.definitions, key=byX).x - gopWidth - 20
    gopTop = min(patch.definitions, key=byY).y + 20

    # FIRST
    patch.addDef(Text(x=gopLeft, y=gopTop - 30, value="Autogen GUI >>>"))

    # beautify inlets
    labelDeltaX = ((gopWidth - LABEL_WIDTH) / (len(inlets) - 1)) if len(inlets) > 1 else 0
    socketDeltaX = ((gopWidth - SOCKET_WIDTH) / (len(inlets) - 1)) if len(inlets) > 1 else 0
    for i, inlet in enumerate(sorted(inlets, key=byX)):
        comment = f'Inlet {i}'

        # look for comment on top of inlet
        for text in allTexts:
            if text.inRect(inlet.x - MAX_TEXT_DISTANCE, inlet.x + MAX_TEXT_DISTANCE,
                           inlet.y - MAX_TEXT_DISTANCE, inlet.y):
                comment = text.value

        patch.addDef(cnvSocket(gopLeft + socketDeltaX*i, gopTop))
        patch.addDef(cnvLabel(gopLeft + labelDeltaX*i, gopTop + SOCKET_HEIGHT, comment))


    # set title
    patch.addDef(Canvas(x=gopLeft + (gopWidth - len(title)*7)/2,
                        y=gopTop + LABEL_HEIGHT+5,
                        width=10, height=TITLE_HEIGHT,
                        dX=5, dY=8,
                        text=title, textSize=12,
                        boxSize=6, background="#ffffff", foreground="#000000"))

    # add args display if almost one arg is used
    argsTop = gopTop + gopHeight + 30
    lastTop = argsTop
    if (patch.getDefOfType("\$1")
        or any(['\$1' in str(arg)
                for obj in patch.definitions
                if isinstance(obj, Object)
                for arg in obj.args])
        ):
        gopHeight += 30
        # display
        patch.addDef(Canvas(x=gopLeft + 5, y=gopTop + LABEL_HEIGHT + TITLE_HEIGHT + 10,
                            width=gopWidth - 10, height=20, boxSize=1,
                            textSize=12, dX=10, dY=14,
                            receive='\\$0-argsdisplay'))
        patch.addDef(Canvas(x=gopLeft + 5, y=gopTop + LABEL_HEIGHT + TITLE_HEIGHT + 10,
                            width=1, height=1, boxSize=1,
                            text='args:', textSize=8, dX=0, dY=6))
        # code
        patch.chainConnect([patch.addDef(Object(gopLeft, argsTop + 10, type='loadbang')),
                            patch.addDef(Message(gopLeft, argsTop + 40, value='args')),
                            patch.addDef(Object(gopLeft, argsTop + 70, type='pdcontrol')),
                            patch.addDef(Object(gopLeft, argsTop + 100, type='l2s')),
                            patch.addDef(Message(gopLeft, argsTop + 130, value='label \\$1')),
                            patch.addDef(Object(gopLeft, argsTop + 160, type='s \\$0-argsdisplay'))
                            ])
        lastTop = argsTop + 190

    # beautify outlets
    labelDeltaX = ((gopWidth - LABEL_WIDTH) / (len(outlets) - 1)) if len(outlets) > 1 else 0
    socketDeltaX = ((gopWidth - SOCKET_WIDTH) / (len(outlets) - 1)) if len(outlets) > 1 else 0
    for i, outlet in enumerate(sorted(outlets, key=byX)):
        comment = f'Outlet {i}'

        # look for comment on bottom of outlet
        for text in allTexts:
            if text.inRect(outlet.x - MAX_TEXT_DISTANCE, outlet.x + MAX_TEXT_DISTANCE,
                           outlet.y, outlet.y + MAX_TEXT_DISTANCE):
                comment = text.value

        patch.addDef(cnvSocket(gopLeft + socketDeltaX*i, gopTop + gopHeight - SOCKET_HEIGHT))
        patch.addDef(cnvLabel(gopLeft + labelDeltaX*i,
                              gopTop + gopHeight - LABEL_HEIGHT - SOCKET_HEIGHT,
                              comment))

    # LAST
    patch.addDef(Text(x=gopLeft, y=lastTop, value="<<< Autogen GUI"))

    # set GraphOnParent
    patch.setCoords(left=gopLeft, top=gopTop, width=gopWidth, height=gopHeight)

    # output result patch
    if args.output != "-" :
        output_stream = open(args.output, 'w')
    else:
        output_stream = sys.stdout

    print(str(patch), file=output_stream)
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
