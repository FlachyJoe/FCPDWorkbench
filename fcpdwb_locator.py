
import os
PATH = os.path.dirname(__file__)
ICONS_PATH = os.path.join(PATH, 'Icons')

def icon(filename):
    return os.path.join(ICONS_PATH, filename)

def getFCPDWorkbench():
    import FreeCADGui
    return FreeCADGui.getWorkbench('FCPDWorkbench')
