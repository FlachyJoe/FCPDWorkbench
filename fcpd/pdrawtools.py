# -*- coding: utf-8 -*-
###################################################################################
#
#  pdrawtools.py
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

# this module translate pd message to action for [fc_giveme] object and [raw( messages

import os
import inspect
import re

import FreeCAD as App

import fcpdwb_locator as locator
from fcpdwb_utils import _S

from . import pdmsgtranslator

PDMsgTranslator = pdmsgtranslator.PDMsgTranslator

# shortcuts of FreeCAD console
Log = App.Console.PrintLog
Msg = App.Console.PrintMessage
Wrn = App.Console.PrintWarning
Err = App.Console.PrintError


def registerToolList(pdServer):
    toolList = [
        ("giveme", pdGiveMe),
        ("raw", pdRaw),
        ("str", pdStr),
        ("objectmethod", pdObjectMethod),
    ]
    for word, func in toolList:
        pdServer.registerMessageHandler([word], func)


def text(x, y, string):
    return f"#X text {_S(x, y, string)};\n"


def simpleObj(x, y, typ):
    return f"#X obj {_S(x, y, typ)};\n"


def canvas(x, y, width, height, label, background, foreground):
    return f"#X obj {x} {y} cnv {width} {height} {y} empty empty {label} 8 12 0 13 {background} {foreground} 0;\n"


def triggerAB(x, y, count):
    return f"#X obj {x} {y} t a {'b ' * count};\n"


def connect(id1, outlet, id2, inlet):
    return f"#X connect {_S(id1,outlet,id2,inlet)};\n"


def isInteger(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).isInteger()


def getParameters(func):
    clean_params = []
    try:
        clean_params = list(inspect.signature(func).parameters.keys())
    except ValueError:
        # parse __doc__
        docstr = "\n".join(func.__doc__.split("\n")[1:])
        if docstr:
            leftpar = docstr.find("(") + 1
            rightpar = docstr.find(")", leftpar)
            if rightpar > 0:
                paramstr = docstr[leftpar:rightpar]
                paramstr = paramstr.replace("[", "")
                paramstr = paramstr.replace("]", "")
                paramstr = paramstr.replace("\n", "")
                params = paramstr.split(",")

            else:
                params = []
            clean_params = []
            for p in params:
                e = p.find("=")
                if e > 0:
                    p = p[:e]
                p = p.strip()
                if p:
                    clean_params.append(p)
        else:
            # try to call the func
            try:
                func()
            except TypeError as err:
                # get info from error msg
                msg = str(err).replace(" an ", " one ").replace(" a ", " one ")
                msgParse = re.search(r"(\S*) argument", msg)
                if msgParse:
                    numbers = [
                        "one",
                        "two",
                        "three",
                        "four",
                        "five",
                        "six",
                        "seven",
                        "eight",
                        "nine",
                        "ten",
                    ]
                    strCount = msgParse.group(1)
                    if isInteger(strCount):
                        count = int(strCount)
                    else:
                        try:
                            count = numbers.index(strCount) + 1
                        except ValueError:
                            count = -1
                    clean_params = ["arg_" + numbers[i] for i in range(count)]
            else:
                clean_params = []  # OK with no params
    return clean_params


def getCleanDoc(func):
    """return PD printable func.__doc__"""
    docstr = func.__doc__
    dash = docstr.find("--") + 2
    docLines = docstr.split("\n")
    if dash > 1:
        docStart = docLines[0]
        docEnd = docstr[dash:]
        docstr = docStart + docEnd
    else:
        docstr = docLines[0]
    return docstr.replace(",", " \\, ").replace("\n", " \\; ")


def generate(func, call, dirname, paramCount=-1):
    """generate a pd patch to overlay a python function"""
    func_name = func.__name__
    if not func_name.startswith("_"):
        pdname = func_name
        params = getParameters(func)
        if paramCount == -1:
            paramCount = len(params)
        if paramCount:
            cnv = "#N canvas 750 350 500 500 12;\n"  # objId
            cnv += text(10, 10, params[0])  # 0
            cnv += simpleObj(10, 30, "inlet")  # 1
            if paramCount > 1:
                cnv += triggerAB(10, 60, paramCount)  # 2
                for i in range(paramCount):
                    if i <= len(params):
                        p = params[i]
                    else:
                        p = ""
                    cnv += text(100 * (i + 1), 10, p)  # 3+4*i
                    cnv += simpleObj(100 * (i + 1), 30, "inlet")  # 4+4*i
                    cnv += simpleObj(100 * (i + 1), 90 + 30 * i, "any")  # 5+4*i
                    cnv += simpleObj(
                        100 * (i + 1), 120 + 30 * i, "list append"
                    )  # 6+4*i
            last = 2 + 4 * paramCount
            cnv += simpleObj(10, 300, f"list prepend raw {call}")  # last +1
            cnv += simpleObj(10, 330, "fc_process 0")  # last +2
            cnv += simpleObj(10, 360, "route ERROR")  # last +3
            cnv += simpleObj(10, 390, "print FreeCAD Error")  # last +4
            cnv += simpleObj(120, 390, "outlet")  # last +5

            cnv += connect(1, 0, 2, 0)  # inlet -> trigger
            if paramCount > 1:
                for i in range(paramCount):
                    cnv += connect(2, i + 1, 5 + 4 * i, 0)  # trigger i+1 -> any 0
                    cnv += connect(4 + 4 * i, 0, 5 + 4 * i, 1)  # inlet 0 -> any 1
                    cnv += connect(5 + 4 * i, 0, 6 + 4 * i, 1)  # any 0 -> list append 1
                    if i == 0:
                        cnv += connect(
                            2, 0, 6 + 4 * i, 0
                        )  # trigger 0 -> list append 0 (bang to drop arg)
                    else:
                        cnv += connect(
                            6 + 4 * (i - 1), 0, 6 + 4 * i, 0
                        )  # list append 0 -> list append 0 (arg -> next arg)
                cnv += connect(last, 0, last + 1, 0)  # last list append -> list prepend
            cnv += connect(last + 1, 0, last + 2, 0)  # list prepend -> fc_process
            cnv += connect(last + 2, 0, last + 3, 0)  # fc_process -> route
            cnv += connect(last + 3, 0, last + 4, 0)  # route -> print
            cnv += connect(last + 3, 1, last + 5, 0)  # route -> outlet

        else:
            # no params
            cnv = "#N canvas 750 350 500 500 12;\n"
            cnv += simpleObj(10, 30, "inlet")
            cnv += simpleObj(10, 100, "bang")
            cnv += simpleObj(10, 300, f"list prepend raw {call}")
            cnv += simpleObj(10, 330, "fc_process 0")
            cnv += simpleObj(10, 360, "route ERROR")
            cnv += simpleObj(10, 390, "print FreeCAD Error")
            cnv += simpleObj(120, 390, "outlet")
            cnv += connect(0, 0, 1, 0)
            cnv += connect(1, 0, 2, 0)
            cnv += connect(2, 0, 3, 0)
            cnv += connect(3, 0, 4, 0)
            cnv += connect(4, 0, 5, 0)
            cnv += connect(4, 1, 6, 0)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        with open(os.path.join(dirname, pdname) + ".pd", "w") as file:
            file.write(cnv)
        return True


def generateHelp(func, objectName, dirname, paramCount=-1):
    """generate a pd help patch to document a python function"""
    func_name = func.__name__
    if not func_name.startswith("_"):
        pdname = func_name
        params = getParameters(func)
        if paramCount == -1:
            paramCount = len(params)
        hlp = "#N canvas 436 36 550 620 10;\n"
        hlp += canvas(
            0, 0, 15, 550, f"{objectName.lower()}/{pdname}", "#c4dcdc", "#000000"
        )
        hlp += simpleObj(400, 10, f"{objectName.lower()}/{pdname}")
        # DESC
        doc = getCleanDoc(func)
        hlp += text(10, 50, doc)
        descHeight = 50 + 20 * len(doc.split("\\;"))
        # INLETS
        hlp += canvas(0, descHeight, 3, 550, "inlets", "#dcdcdc", "#000000")
        for i in range(paramCount):
            hlp += canvas(78, descHeight + 20 + 30 * i, 17, 3, i, "#dcdcdc", "#9c9c9c")
            if i <= len(params):
                p = params[i]
            else:
                p = ""
            hlp += text(100, descHeight + 20 + 30 * i, p)
        # OUTLETS
        hlp += canvas(
            0,
            descHeight + 20 + 30 * paramCount,
            3,
            550,
            "outlets",
            "#dcdcdc",
            "#000000",
        )
        hlp += canvas(
            78, descHeight + 50 + 30 * paramCount, 17, 3, "0", "#dcdcdc", "#9c9c9c"
        )
        hlp += text(100, descHeight + 50 + 30 * paramCount, "Result of the operation")
        # ARGUMENTS
        hlp += canvas(
            0,
            descHeight + 110 + 30 * paramCount,
            3,
            550,
            "arguments",
            "#dcdcdc",
            "#000000",
        )
        # MORE INFO
        hlp += canvas(
            0,
            descHeight + 170 + 30 * paramCount,
            3,
            550,
            "more_info",
            "#dcdcdc",
            "#000000",
        )
        hlp += text(
            10,
            descHeight + 190 + 30 * paramCount,
            "This object and its help was autogenerated by FCPD_Workbench",
        )
        # FOOTER
        hlp += canvas(
            0, descHeight + 230 + 30 * paramCount, 15, 550, "", "#dcdcdc", "#404040"
        )

        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        with open(os.path.join(dirname, pdname) + "-help.pd", "w") as file:
            file.write(hlp)


# TODO : keyword args


def pdRaw(pdServer, words):
    """raw Module.Object.Func"""
    modFunc = words[2].split(".")
    objectName = ".".join(modFunc[:-1])
    funcName = modFunc[-1]
    try:
        exec("import %s" % objectName)
    except ModuleNotFoundError:
        if modFunc[:-2]:
            try:
                className = ".".join(modFunc[:-2])
                exec("import %s" % className)
            except ModuleNotFoundError as e:
                Wrn("FCPD", f"Error : {e}\n")
                return f"ERROR module not found {className}"
    obj = eval(objectName)
    func = getattr(obj, funcName)
    _, values = PDMsgTranslator.popValues(words[3:])
    args = [val.value for val in values]
    try:
        return func(*args)
    except AttributeError:
        return "ERROR AttributeError"


def pdGiveMe(pdServer, words):
    """giveme Module.Object.Func [arg_count]
    dynamically create a PD object to overlay a python function"""
    args = words[2].split(".")
    moduleName = ".".join(args[:-1])
    objectName = "/".join(args[:-1])
    funcName = args[-1]

    if len(words) > 3:
        paramCount = int(words[3])
    else:
        paramCount = -1

    pdLibPath = os.path.join(locator.PD_PATH, "pdautogen")
    pdHelpPath = os.path.join(locator.PD_PATH, "pdautogenhelp")
    modulePath = os.path.join(pdLibPath, objectName.lower())
    moduleHelpPath = os.path.join(pdHelpPath, objectName.lower())
    filePath = os.path.join(modulePath, funcName)

    if not os.path.isfile(filePath):
        Log("FCPD", f"PDServer : add {filePath}\n")
        try:
            Log("FCPD", f"PDServer : try to import {moduleName}\n")
            exec(f"import {moduleName}")
            Log("FCPD", "PDServer : import ok\n")
        except ModuleNotFoundError:
            if args[:-2]:
                try:
                    className = ".".join(args[:-2])
                    Log("FCPD", f"PDServer : try to import {className}\n")
                    exec(f"import {className}")
                    Log("FCPD", "PDServer : import ok\n")
                except ModuleNotFoundError as e:
                    Wrn("FCPD", f"Error : {e}\n")
                    return f"ERROR module not found {className}"
        try:
            obj = eval(moduleName)
        except Exception as e:
            Wrn("FCPD", f"Error : {e}\n")
        if hasattr(obj, funcName):
            func = getattr(obj, funcName)
            if not generate(func, words[2], modulePath, paramCount):
                return "ERROR unable to generate the object"
            generateHelp(func, objectName, moduleHelpPath, paramCount)
        else:
            return f"ERROR {moduleName} has no function {funcName}"
    return f"{objectName.lower()}{funcName}"


def pdStr(pdServer, words):
    """str [list]
    convert a pd list to a string"""
    return str(PDMsgTranslator.valueFromStr(words[2:])[0].value)


def pdObjectMethod(pdServer, words):
    """objectmethod Object Method [args]
    call an object method with given arguments"""
    obj = PDMsgTranslator.valueFromStr(words[2])[0].value
    methodName = words[3]

    if not hasattr(obj, methodName):
        return f"ERROR {obj} has no method {methodName}"

    method = getattr(obj, methodName)
    _, values = PDMsgTranslator.popValues(words[4:])
    args = [val.value for val in values]
    try:
        return method(*args)
    except AttributeError:
        return "ERROR AttributeError"
