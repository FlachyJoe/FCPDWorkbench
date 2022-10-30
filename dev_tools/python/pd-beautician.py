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

from PdParser import Patch, Object, Canvas, Coords, byX, byY, Text

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


# process the input file and print the result in stdout
def main():
    parser = argparse.ArgumentParser(description='Beautify a PureData patch')
    parser.add_argument('--icon', type=str, help='GIF to show as icon', dest='icon')
    parser.add_argument('input', type=str, help='file to process')
    parser.add_argument('output', type=str, help='file to store result', default='-')

    args = parser.parse_args()

    filename: str = args.input
    patch = Patch.fromFile(filename)

    # retrieve objects
    allTexts = patch.getDefOfType("text")
    inlets = patch.getDefOfType("inlet") + patch.getDefOfType("inlet~")
    outlets = patch.getDefOfType("outlet") + patch.getDefOfType("outlet~")

    # look for icon
    if args.icon:
        icon = args.icon
    else:
        icon = path.splitext(filename)[0] + ".gif"

    if not path.exists(icon):
        icon = False

    # GraphOnParent dimensions
    gopWidth = LABEL_WIDTH * max(len(inlets), len(outlets)) + 10
    gopHeight = 2 * LABEL_HEIGHT + TITLE_HEIGHT + (34 if icon else 10)

    gopLeft = min(patch.definitions, key=byX).x - gopWidth - 20
    gopTop = min(patch.definitions, key=byY).y + 20

    patch.addDef(Text(x=gopLeft, y=gopTop - 10, value="Autogen GUI >>>"))

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

    # set title
    title, _ = splitext(basename(filename))
    patch.addDef(Canvas(x=gopLeft + (gopWidth - len(title)*7)/2,
                        y=gopTop + LABEL_HEIGHT+5,
                        width=80, height=TITLE_HEIGHT,
                        dX=5, dY=8,
                        text=title, textSize=12,
                        boxSize=6, background="#ffffff", foreground="#000000"))

    # set icon
    if icon:
        patch.addDef(Object(x=gopLeft + gopWidth / 2,
                            y=gopTop + LABEL_HEIGHT + TITLE_HEIGHT + 19,
                            type="ggee/image",
                            args=icon))

    patch.addDef(Text(x=gopLeft, y=gopTop + gopHeight + 10, value="<<< Autogen GUI"))

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
