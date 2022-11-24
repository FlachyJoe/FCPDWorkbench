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


def unescape(source: str) -> str:
    '''
        remove PD escape characters from a string
    '''
    return str(source).replace(r'\ ', ' ')


def escape(source: str) -> str:
    '''
        add PD escape characters to a string
    '''
    return unescape(source).replace(' ', r'\ ')


# helpers for sorting
def byX(o):
    return o.x


def byY(o):
    return o.y


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

    def __getattr__(self, attr):
        return getattr(self.string, attr)

    def checkAndSplit(self):
        if self.endswith(';'):
            self.string = self.string[:-1]
        return self.string.split()


class Definition:
    '''
        Represents a PD 'box'
    '''
    def __init__(self, x: int, y: int, index: int=-1, type: str='nothing'):
        self.index = index
        self.x = int(x)
        self.y = int(y)
        self.type = type

    def __int__(self):
        return self.index

    def inRect(self, xMin, xMax, yMin, yMax) -> bool:
        return (self.x in range(xMin, xMax)
                and self.y in range(yMin, yMax))

    @staticmethod
    def fromLine(code: FileLine):
        words = code.split()
        if words[1] == 'obj':
            return Object.fromLine(code)
        if words[1] == 'msg':
            return Message.fromLine(code)
        if words[1] == 'text':
            return Text.fromLine(code)
        if words[1] == 'floatatom':
            return FloatAtom.fromLine(code)
        if words[1] == 'symbolatom':
            return SymbolAtom.fromLine(code)

        raise ValueError(f'not an object definition : {str(code)}')


class Object(Definition):
    '''
        a PureData object
        see https://puredata.info/docs/developer/PdFileFormat#r36
    '''
    def __init__(self, x: int, y: int, type: str, index=-1, args=""):
        super().__init__(x, y, index, type)
        if not isinstance(args, list):
            args = [args]
        self.args = args

    def __str__(self):
        return (f"#X obj {self.x} {self.y} {self.type}"
                f"{' ' if self.args else ''}{' '.join([escape(s) for s in self.args])};")

    @staticmethod
    def fromLine(code: FileLine):
        words = code.checkAndSplit()
        if words[1] != 'obj':
            raise ValueError('This is not an object definition.')

        return Object(words[2], words[3], words[4], int(code), [unescape(s) for s in words[5:]])


class Coords:
    '''
        the visual range of a frameset
        see https://puredata.info/docs/developer/PdFileFormat#r33
    '''
    def __init__(self, xFrom, yTo, xTo, yFrom, width, height, gop, left=0, top=0):
        self.xFrom = xFrom
        self.yTo = yTo
        self.xTo = xTo
        self.yFrom = yFrom
        self.width = width
        self.height = height
        self.gop = gop
        self.left = left
        self.top = top

    def __str__(self):
        return (f"#X coords {self.xFrom} {self.yTo} {self.xTo} {self.yFrom}"
                f" {self.width} {self.height} {self.gop} {self.left} {self.top};")

    @staticmethod
    def fromLine(code: FileLine):
        words = code.checkAndSplit()
        if words[1] != 'coords':
            raise ValueError('This is not a coords definition.')

        return Coords(*words[2:])


class Message(Definition):
    '''
        a PureData message
        see https://puredata.info/docs/developer/PdFileFormat#r35
    '''
    def __init__(self, x: int, y: int, index: int=-1, value: str='empty'):
        super().__init__(x, y, index, 'msg')
        self.value = value

    def __str__(self):
        return f"#X msg {self.x} {self.y} {self.value};"

    @staticmethod
    def fromLine(code: FileLine):
        words = code.checkAndSplit()
        if words[1] != 'msg':
            raise ValueError('This is not a message definition.')

        return Message(words[2], words[3], int(code), ' '.join(words[4:]))


class Text(Definition):
    '''
        a PureData comment
        see https://puredata.info/docs/developer/PdFileFormat#r3B
    '''

    def __init__(self, x: int, y: int, index: int=-1, value: str='empty'):
        super().__init__(x, y, index, 'text')
        self.value = value

    def __str__(self):
        return f"#X text {self.x} {self.y} {self.value};"

    @staticmethod
    def fromLine(code: FileLine):
        words = code.checkAndSplit()
        if words[1] != 'text':
            raise ValueError('This is not a text definition.')

        return Text(words[2], words[3], int(code), ' '.join(words[4:]))


class Struct:
    '''
        a PureData structure definition
    '''
    def __init__(self, index: int, name: str, args: str):
        self.index = index
        self.name = name
        self.args = args

    def __str__(self):
        return f"#N struct {self.name} {self.args};"

    @staticmethod
    def fromLine(code: FileLine):
        words = code.checkAndSplit()
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
        words = code.checkAndSplit()
        if words[1] != 'connect':
            raise ValueError('This is not a connect definition.')

        return Connect(int(code), words[2], words[3], words[4], words[5])

class Patch:
    '''
        a PureData patch
    '''

    def __init__(self, definitions, connects, structs, coords, canvas, subPatches, arrays):
        self.definitions = definitions
        self.connects = connects
        self.structs = structs
        self.coords = coords
        self.canvas = canvas
        self.subPatches = subPatches
        self.arrays = arrays

        self.reindex()

    def reindex(self):
        # Reindex definitions and subpatches
        #  as puredata doesn't refer to linenumber but definition order
        for i, obj in enumerate(sorted(self.definitions + self.subPatches, key=byLine)):
            obj.index = i

    def __str__(self):
        contents = ([self.canvas] + self.structs
                    + sorted(self.definitions + self.subPatches , key=byLine)
                    + self.connects + self.coords)
        return '\n'.join([str(s) for s in contents])

    def setCoords(self, xFrom=0, yTo=0, xTo=1, yFrom=1,
                  width=100, height=100, gop=2, left=0, top=0):
        self.coords = [Coords(xFrom, yTo, xTo, yFrom, width, height, gop, left, top)]

    def getDefOfType(self, type: str) -> list[Definition]:
        return [obj for obj in self.definitions if obj.type == type]

    def addDef(self, obj: Definition) -> Definition:
        if obj.index < 0:
            obj.index = max([o.index for o in self.definitions]) + 1
        self.definitions.append(obj)
        return obj

    def connect(self, obj1, outlet, obj2, inlet):
        obj = Connect(max([o.index for o in self.connects]) + 1, int(obj1), outlet, int(obj2), inlet)
        self.connects.append(obj)
        return obj

    def chainConnect(self, objList):
        for i, obj1 in enumerate(objList[:-1]):
            self.connect(obj1, 0, objList[i + 1], 0)

    @staticmethod
    def fromLines(code: list[FileLine]):

        mainStructs = {l for l in code if l.startswith('#N struct')}

        # Split subpatches and arrays
        subPatchesLinesNumber = []
        currentLevel = 0
        arraysLinesNumber = []
        for l in sorted(code, key=lambda l: l.lineNumber):
            if l.startswith('#X array'):
                arraysLinesNumber.append(int(l))
            if l.startswith('#N canvas'):
                subPatchesLinesNumber.append((currentLevel, int(l), len(code)))
                currentLevel += 1
            if l.startswith('#X restore'):
                if currentLevel > 0:
                    currentLevel -= 1
                    subPatchesLinesNumber[-1] = (subPatchesLinesNumber[-1][0],
                                                 subPatchesLinesNumber[-1][1],
                                                 int(l)+1)
                else:
                    raise ValueError('Error in subpatch definition.')

        firstLine = int(code[0])

        # sub-patches
        subPatchesCode = [code[start - firstLine:end - firstLine]
                          for lvl, start, end in subPatchesLinesNumber
                          if lvl == 1]
        subPatchesLines = set(l for lines in subPatchesCode for l in lines)
        subPatches = []
        for lines in subPatchesCode:
            subPatches.append(SubPatch.fromLines(lines))

        # arrays
        arraysCode = [code[start - firstLine:start - firstLine + 2] for start in arraysLinesNumber]
        arraysLines = set(l for lines in arraysCode for l in lines)
        arrays = []
        for lines in arraysCode:
            arrays.append(Array.fromLines(lines))

        # main patch
        main = set(code) - subPatchesLines - arraysLines
        mainCanvas = list(sorted(main))[0]
        mainConnects = {l for l in main if l.startswith('#X connect')}
        mainCoords = {l for l in main if l.startswith('#X coords')}
        mainObjects = {l for l in main if l.startswith('#X')} - mainConnects - mainCoords

        canvas = mainCanvas + ';'
        structs = [Struct.fromLine(l) for l in mainStructs]
        definitions = [Definition.fromLine(l) for l in mainObjects]
        connects = [Connect.fromLine(l) for l in mainConnects]
        coords = [Coords.fromLine(l) for l in mainCoords]

        return Patch(definitions, connects, structs, coords, canvas, subPatches, arrays)

    @staticmethod
    def fromFile(filename: str):
        with open(filename, 'r') as hFile:
            contents = PdFile(hFile.read().split(';\n'))

        if not contents.isValid():
            raise ValueError(f"{filename} is not in a valid Pure-Data format.")

        return Patch.fromLines(sorted(contents.lines(), key=lambda l: l.lineNumber))


class SubPatch(Definition):
    '''
        a PureData sub-patch
    '''

    def __init__(self, x: int, y: int, index: int, width: int, height: int,
                 winX: int, winY: int, name: str, args: str, contents: Patch):
        super().__init__(x, y, index, 'subpatch')
        self.width = width
        self.height = height
        self.winX = winX
        self.winY = winY
        self.name = name
        self.args = args
        self.contents = contents

    def __str__(self):
        header = f"#N canvas {self.width} {self.height} {self.winX} {self.winY} {self.name} 1;"
        if self.name == "graph":
            footer = f"#X restore {self.x} {self.y} graph;"
        else:
            footer = f"#X restore {self.x} {self.y} pd {self.name} {' '.join(self.args)};"
        return f"{header}\n{str(self.contents)}\n{footer}"

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

        if len(fWords)>5:
            return SubPatch(fWords[2], fWords[3], int(code[0]),
                            hWords[2], hWords[3], hWords[4], hWords[5],
                            fWords[5], fWords[6:], defContents)
        # graph case, only 5 words
        return SubPatch(fWords[2], fWords[3], int(code[0]),
                        hWords[2], hWords[3], hWords[4], hWords[5],
                        'graph', None, defContents)


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


class FloatAtom(Definition):
    '''
        a floatatom
        see https://puredata.info/docs/developer/PdFileFormat#r34
    '''
    def __init__(self, x, y, index=-1, width=5, lowerLimit=0, upperLimit=0, labelPos=0,
                 label='-', receive='-', send='-', size='0'):
        super().__init__(x, y, index, 'floatatom')
        self.values = [width, lowerLimit, upperLimit, labelPos, label, receive, send, size]

    def __str__(self):
        return f"#X floatatom {self.x} {self.y} {' '.join(self.values)};"

    @staticmethod
    def fromLine(code: FileLine):
        words = code.checkAndSplit()
        if words[1] != 'floatatom':
            raise ValueError('This is not a FloatAtom definition.')

        return FloatAtom(words[2], words[3], int(code), *words[4:])


class SymbolAtom(Definition):
    '''
        a symbolatom
        see https://puredata.info/docs/developer/PdFileFormat#r3A
    '''
    def __init__(self, x, y, index=-1, width=10, lowerLimit=0, upperLimit=0, labelPos=0,
                 label='-', receive='-', send='-', size='0'):
        super().__init__(x, y, index, 'symbolatom')
        self.values = [width, lowerLimit, upperLimit, labelPos, label, receive, send, size]

    def __str__(self):
        return f"#X symbolatom {self.x} {self.y} {' '.join(self.values)};"

    @staticmethod
    def fromLine(code: FileLine):
        words = code.checkAndSplit()
        if words[1] != 'symbolatom':
            raise ValueError('This is not a SymbolAtom definition.')

        return SymbolAtom(words[2], words[3], int(code), *words[4:])


class ListBox(Definition):
    '''
        a listbox
        see https://puredata.info/docs/developer/PdFileFormat#r3A
    '''
    def __init__(self, x, y, index=-1, width=20, lowerLimit=0, upperLimit=0, labelPos=0,
                 label='-', receive='-', send='-', size='0'):
        super().__init__(x, y, index, 'listbox')
        self.values = [width, lowerLimit, upperLimit, labelPos, label, receive, send, size]

    def __str__(self):
        return f"#X listbox {self.x} {self.y} {' '.join(self.values)};"

    @staticmethod
    def fromLine(code: FileLine):
        words = code.checkAndSplit()
        if words[1] != 'symbolatom':
            raise ValueError('This is not a SymbolAtom definition.')

        return SymbolAtom(words[2], words[3], int(code), *words[4:])

class Array:
    '''
        an array
        see https://puredata.info/docs/developer/PdFileFormat#r31
    '''

    def __init__(self, index: int, name: str, size: int, saveFlag: int, datas: list):
        self.index = index
        self.name = name
        self.size = size
        self.saveFlag = saveFlag
        self.datas = datas

    def __str__(self):
        lines = (f"#X array {self.name} {self.size} float {self.saveFlag};\n#A"
                ' '.join(self.datas))
        return lines

    @staticmethod
    def fromLines(code: list[FileLine]):
        header = code[0]
        contents = code[1:]

        if header.endswith(';'):
            header = header[:-1]
        if contents[-1].endswith(';'):
            contents[-1] = contents[-1][:-1]

        hWords = header.split()
        if hWords[1] != 'array':
            raise ValueError('This is not an array definition.')

        datas = [l for line in contents for l in str(line).split()]
        datas.remove('#A')

        return Array(int(code[0]), hWords[2], hWords[3], hWords[5], datas)


class Canvas (Object):
    '''
        helper for canvas creation
    '''
    def __init__(self, x=100, y=100, index=-1,
                 boxSize=15, width=100, height=60, send='empty', receive='empty',
                 text='empty', dX=20, dY=12, font=0, textSize=14,
                 background="#e0e0e0", foreground="#404040"):
        super().__init__(x, y, "cnv", index, [boxSize, width, height, send, receive,
                         escape(text), dX, dY, font, textSize, background, foreground])
