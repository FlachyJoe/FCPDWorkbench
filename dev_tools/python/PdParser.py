#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  PdParser.py
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

DEBUG = False

if DEBUG:
    import sys
    def eprint(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)
else:
    def eprint(*args, **kwargs): pass


MULTILINE_ERROR = ValueError('\';\' found. Only one object can be convert. \
 Please split before convert.')

def unescape(source: str) -> str:
    '''
        remove PD escape characters from a string
    '''
    return str(source).replace('\ ',' ')

def escape(source: str) -> str:
    '''
        add PD escape characters to a string
    '''
    return unescape(source).replace(' ', '\ ')

# helpers for sorting
def byX(o):
    return o.x

def byY(o):
    return o.Y

def byLine(o):
    return int(o)


class FileLine:
    '''
        Represents a line of a PD file
        acts as string or int depend on context
    '''
    def __init__(self, numberedLine: tuple[int, str]):
        self.lineNumber = numberedLine[0]
        self.string = numberedLine[1]

        self.__len__ = self.string.__len__
        self.__getitem__ = self.string.__getitem__

    def __str__(self):
        return self.string

    def __repr__(self):
        return f"{self.lineNumber} : {self.string}"

    def __int__(self):
        return self.lineNumber

    def __lt__(self, attr):
        if isinstance(attr, FileLine):
            return self.lineNumber < attr.lineNumber
        return self.lineNumber.__lt__(attr)

    def __gt__(self, attr):
        if isinstance(attr, FileLine):
            return self.lineNumber > attr.lineNumber
        return self.lineNumber.__gt__(attr)

    def __lte__(self, attr):
        return self.lineNumber.__lt__(attr)

    def __gte__(self, attr):
        return self.lineNumber.__gt__(attr)

    def __add__(self, attr):
        if isinstance(attr, str):
            return self.string.__add__(attr)
        return self.lineNumber.__add__(attr)

    def __radd__(self, attr):
        if isinstance(attr, str):
            return attr + self.string
        return self.lineNumber.__radd__(attr)

    def __getattr__ (self, attr):
        return getattr(self.string, attr)


class Definition:
    '''
        Represents a PD 'box'
    '''
    def __init__(self, index: int, x: int, y: int):
        self.index = index
        self.x = int(x)
        self.y = int(y)

    def __int__(self):
        return self.index

    def inRect(self, xMin, xMax, yMin, yMax)-> bool:
        return (self.x in range(xMin, xMax)
                and self.y in range(yMin, yMax))

    @staticmethod
    def fromLine(code: FileLine):
        words = code.split()
        if words[1] == 'obj':
            return Object.fromLine(code)
        elif words[1] == 'msg':
            return Message.fromLine(code)
        elif words[1] == 'text':
            return Text.fromLine(code)
        elif words[1] == 'coords':
            return Coords.fromLine(code)
        else:
            raise ValueError(f'not an object definition : {str(code)}')

class Object(Definition):
    '''
        a PureData object
        see https://puredata.info/docs/developer/PdFileFormat#r36
    '''
    def __init__(self, index: int, x: int, y: int, type: str, args):
        super().__init__(index, x, y)
        self.type = type
        if not isinstance(args, list):
            args = [args]
        self.args = args

    def __str__(self):
        return f"#X obj {self.x} {self.y} {self.type}{' ' if self.args else ''}{' '.join([escape(s) for s in self.args])};"

    @staticmethod
    def fromLine(code: FileLine):
        if code.endswith(';'):
            code = code[:-1]
        if ';' in str(code):
            raise MULTILINE_ERROR

        words = code.split()
        if words[1] != 'obj':
            raise ValueError('This is not an object definition.')

        return Object(int(code), words[2], words[3], words[4], [unescape(s) for s in words[5:]])

class Coords:
    '''
        the visual range of a frameset
        see https://puredata.info/docs/developer/PdFileFormat#r33
    '''
    def __init__(self, xFrom, yTo, xTo, yFrom, width, height, gop):
        self.xFrom = xFrom
        self.yTo = yTo
        self.xTo = xTo
        self.yFrom = yFrom
        self.width = width
        self.height = height
        self.gop = gop

    def __str__(self):
        return f"#X coords {self.xFrom} {self.yTo} {self.xTo} {self.yFrom} {self.width} {self.height} {self.gop} 0 0;"

    @staticmethod
    def fromLine(code: FileLine):
        if code.endswith(';'):
            code = code[:-1]
        if ';' in str(code):
            raise MULTILINE_ERROR

        words = code.split()
        if words[1] != 'coords':
            raise ValueError('This is not a coords definition.')

        return Coords(*words[2:9])

class Message(Definition):
    '''
        a PureData message
        see https://puredata.info/docs/developer/PdFileFormat#r35
    '''
    def __init__(self, index: int, x: int, y: int, value: str):
        super().__init__(index, x, y)
        self.type = 'msg'
        self.value = value

    def __str__(self):
        return f"#X msg {self.x} {self.y} {self.value};"

    @staticmethod
    def fromLine(code: FileLine):
        if code.endswith(';'):
            code = code[:-1]
        if ';' in str(code):
            raise MULTILINE_ERROR

        words = code.split()
        if words[1] != 'msg':
            raise ValueError('This is not a message definition.')

        return Message(int(code), words[2], words[3], ' '.join(words[4:]))

class Text(Definition):
    '''
        a PureData comment
        see https://puredata.info/docs/developer/PdFileFormat#r3B
    '''

    def __init__(self, index: int, x: int, y: int, value: str):
        super().__init__(index, x, y)
        self.type = 'text'
        self.value = value

    def __str__(self):
        return f"#X text {self.x} {self.y} {self.value};"

    @staticmethod
    def fromLine(code: FileLine):
        if code.endswith(';'):
            code = code[:-1]
        if ';' in str(code):
            raise MULTILINE_ERROR

        words = code.split()
        if words[1] != 'text':
            raise ValueError('This is not a text definition.')

        return Text(int(code), words[2], words[3], ' '.join(words[4:]))

class Struct:
    '''
        a PureData structure definition
    '''
    def __init__(self, index: int, name: str, args: str):
        self.name = name
        self.args = args

    def __str__(self):
        return f"#N struct {self.name} {self.args};"

    @staticmethod
    def fromLine(code: FileLine):
        if code.endswith(';'):
            code = code[:-1]
        if ';' in str(code):
            raise MULTILINE_ERROR

        words = code.split()
        if words[1] != 'struct':
            raise ValueError('This is not a struct definition.')

        return Struct(int(code), words[2], ' '.join(words[3:]))

class Connect:
    '''
        a PureData wire
        see https://puredata.info/docs/developer/PdFileFormat#r32
    '''
    def __init__(self, index: int, obj1: int, outlet: int, obj2: int, inlet: int):
        self.index = index
        self.firstObject = obj1
        self.outlet = outlet
        self.secondObject = obj2
        self.inlet = inlet

    def __str__(self):
        return f"#X connect {self.firstObject} {self.outlet} {self.secondObject} {self.inlet};"

    @staticmethod
    def fromLine(code: FileLine):
        if code.endswith(';'):
            code = code[:-1]
        if ';' in str(code):
            raise MULTILINE_ERROR

        words = code.split()
        if words[1] != 'connect':
            raise ValueError('This is not a connect definition.')

        return Connect(int(code), words[2], words[3], words[4], words[5])

class Patch:
    '''
        a PureData patch
    '''

    def __init__(self, definitions: list[Definition], connects: list[Connect],
                 structs: list[Struct] = None, coords: list[Coords] = None, canvas = None):
        self.definitions = definitions
        self.connects = connects
        self.structs = structs
        self.coords = coords
        self.canvas = canvas

    def __str__(self):
        contents = [self.canvas] + self.structs + sorted(self.definitions, key=byLine) + self.connects + [self.coords]
        return '\n'.join([str(s) for s in contents])

    def getDefOfType(self, type: str)-> list[Definition]:
        return [obj for obj in self.definitions if obj.type == type]

    def addDef(self, obj: Definition)-> Definition:
        if obj.index < 0:
            obj.index = max([o.index for o in self.definitions])
        self.definitions.append(obj)
        return obj

    @staticmethod
    def fromLines(code: list[FileLine]):

        mainStructs = {l for l in code if l.startswith('#N struct')}
        eprint(f"mainStructs : {mainStructs}\n")

        #Split subpatches
        rawSP = {}
        currentLevel = 0
        for l in sorted(code, key=lambda l : l.lineNumber):
            if l.startswith('#N canvas'):
                rawSP[currentLevel] = (int(l), len(code))
                currentLevel += 1
            if l.startswith('#X restore'):
                if currentLevel > 0:
                    currentLevel -= 1
                    rawSP[currentLevel] = (rawSP[currentLevel][0],int(l))
                else:
                    raise ValueError('Error in subpatch definition.')

        eprint(f"rawSP : {rawSP}\n")

        eprint( [code[start: end+1] for lvl,(start,end) in rawSP.items() if lvl > 0])

        main = set(code) - { code[val[0]:val[1]] for lvl,val in rawSP.items() if lvl > 0}

        eprint(f"main : {sorted(main)}\n")

        mainCanvas = list(sorted(main))[0]
        mainConnects = {l for l in main if l.startswith('#X connect')}
        mainCoords =  {l for l in main if l.startswith('#X coords')}
        mainObjects =  {l for l in main if l.startswith('#X')} - mainConnects - mainCoords

        eprint(f"mainObjects : {sorted(mainObjects)}\n"
            f"mainConnects : {sorted(mainConnects)}\n"
        )

        canvas = mainCanvas + ';' # TODO
        structs = [Struct.fromLine(l) for l in mainStructs]
        definitions = [Definition.fromLine(l) for l in mainObjects]
        connects = [Connect.fromLine(l) for l in mainConnects]
        coords = [Coords.fromLine(l) for l in mainCoords]

        return Patch(definitions, connects, structs, coords, canvas)

    @staticmethod
    def fromFile(filename: str):
        with open(filename, 'r') as hFile:
            contents = PdFile(hFile.read().split(';\n'))

        if not contents.isValid():
            raise ValueError(f"{filename} is not in a valid Pure-Data format.")

        return Patch.fromLines(sorted(contents.lines(), key=lambda l : l.lineNumber))


class SubPatch(Definition):
    '''
        a PureData sub-patch
    '''

    def __init__(self, index: int, x: int, y: int, width: int, height: int,
                 winX: int, winY: int, name: str, args: str, contents: Patch):
        super().__init__(index, x, y)
        self.width = width
        self.height = height
        self.winX = winX
        self.winY = winY
        self.name = name
        self.args = args
        self.contents = contents

    def __str__(self):
        header = f"#N canvas {self.width} {self.height} {self.winX} {self.winY} {self.name} 1;"
        footer = f"#X restore {self.x} {self.y} pd {self.name} {self.args};"
        contents = ""
        for obj in sorted(self.contents):
            contents += f"{obj}\n"
        return f"{header}\n{contents}\n{footer}"

    @staticmethod
    def fromLines(code: list[FileLine]):
        header = code[0]
        footer = code[-1]
        contents = code[1:-1]

        if header.endswith(';'):
            header = header[:-1]
        if footer.endswith(';'):
            footer = footer[:-1]

        hWords = header.split()
        fWords = footer.split()
        if hWords[1] != 'canvas' or fWords[1] != 'restore':
            raise ValueError('This is not a subpatch definition.')

        defContents = Patch.fromLines(contents)

        return SubPatch(int(code[0]), fWords[2], fWords[3],
                        hWords[2], hWords[3], hWords[4], hWords[5],
                        fWords[5], fWords[6:], defContents)


class PdFile:
    '''
        a PureData file
    '''
    def __init__(self, code: list[str]):
        self.contents = [FileLine(l) for l in enumerate(code)]

    def strings(self):
        return [str(l) for l in self.contents]

    def lines(self):
        return self.contents

    def isValid(self):
        return (self.contents[0].startswith('#N struct ')
        or self.contents[0].startswith('#N canvas '))

    def __len__(self):
        return len(self.contents)


class Canvas (Object):
    '''
        helper for canvas creation
    '''
    def __init__(self, index=-1, x=100, y=100,
                boxSize=15, width=100, height=60, send='empty', receive='empty',
                text='empty', dX=20, dY=12, font=0, textSize=14,
                background="#e0e0e0", foreground="#404040"):
        super().__init__(index, x, y, "cnv", [boxSize, width, height, send, receive,
                escape(text), dX, dY, font, textSize, background, foreground])
