
import os
import FreeCADGui

PATH = os.path.dirname(__file__)
RESOURCES_PATH = os.path.join(PATH, 'resources')
ICONS_PATH = os.path.join(RESOURCES_PATH, 'icons')
TRANSLATIONS_PATH = os.path.join(RESOURCES_PATH, 'translations')
PD_PATH = os.path.join(PATH, 'pure-data')


def icon(filename):
    return os.path.join(ICONS_PATH, filename)

def resource(filename):
    return os.path.join(RESOURCES_PATH, filename)

def getFCPDWorkbench():
    return FreeCADGui.getWorkbench('FCPDWorkbench')

def getFCPDCore():
    return getFCPDWorkbench().core
