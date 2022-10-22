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

from os.path import dirname, basename, splitext, join
from glob import glob

from PdParser import Patch, Object, Canvas, Coords, byX

# where to look for text around sockets
MAX_TEXT_DISTANCE = 50

# Labels dimensions
LABEL_HEIGHT = 10
LABEL_WIDTH = 75

TITLE_HEIGHT = 15

# template for socket label
def cnvLabel(x, y, text):
    return Canvas(x=x, y=y, width=LABEL_WIDTH, height=LABEL_HEIGHT, dX=5, dY=6,
                  text=text, textSize=8, boxSize=6, background="#000000", foreground="#ffffff")

# process the input file and print the result in stdout
def main(args):
    filename: str = args[1]
    patch = Patch.fromFile(filename)

    # retrieve objects
    allTexts = patch.getDefOfType("text")
    inlets = patch.getDefOfType("inlet") + patch.getDefOfType("inlet~")
    outlets = patch.getDefOfType("outlet") + patch.getDefOfType("outlet~")

    # look for icon
    icons = glob(join(dirname(filename),'*.gif'))

    # GraphOnParent dimensions
    gopWidth = LABEL_WIDTH * len(inlets) + 10
    gopHeight = 2 * LABEL_HEIGHT + TITLE_HEIGHT + (34 if icons else 10)

    # beautify inlets
    inletDeltaX = ((gopWidth - LABEL_WIDTH) / (len(inlets) - 1)) if len(inlets) > 1 else 0
    for i, inlet in enumerate(sorted(inlets, key=byX)):
        comment = f'Inlet {i}'

        # look for comment on top of inlet
        for text in allTexts:
            if text.inRect(inlet.x - MAX_TEXT_DISTANCE, inlet.x + MAX_TEXT_DISTANCE,
                           inlet.y - MAX_TEXT_DISTANCE, inlet.y):
                comment = text.value

        patch.addDef(cnvLabel(inletDeltaX*i, 0, comment))

    # beautify outlets
        outletDeltaX = ((gopWidth - LABEL_WIDTH) / (len(outlets) - 1)) if len(outlets) > 1 else 0
        for i, inlet in enumerate(sorted(outlets, key=byX)):
            comment = f'Outlet {i}'

            # look for comment on bottom of outlet
            for text in allTexts:
                if text.inRect(inlet.x - MAX_TEXT_DISTANCE, inlet.x + MAX_TEXT_DISTANCE,
                               inlet.y, inlet.y + MAX_TEXT_DISTANCE):
                    comment = text.value

            patch.addDef(cnvLabel(outletDeltaX*i, gopHeight - LABEL_HEIGHT, comment))

    # set title
    title, _ = splitext(basename(filename))
    patch.addDef(Canvas(x=(gopWidth - 80)/2, y=LABEL_HEIGHT+5, width=80, height=TITLE_HEIGHT, dX=5, dY=8,
                  text=title, textSize=12, boxSize=6, background="#ffffff", foreground="#000000"))

    # set icon
    if icons:
        patch.addDef(Object(-1, gopWidth / 2, LABEL_HEIGHT + TITLE_HEIGHT + 19 , "ggee/image", icons[0]))

    # set GraphOnParent
    patch.coords = Coords(0, 0, 1, 1, gopWidth, gopHeight, 2)

    # output result patch
    print(str(patch))

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
