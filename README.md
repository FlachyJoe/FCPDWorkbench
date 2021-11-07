## PureData connection workbench for FreeCAD
[![Total alerts](https://img.shields.io/lgtm/alerts/g/FlachyJoe/FCPDWorkbench.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/FlachyJoe/FCPDWorkbench/alerts/) [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/FlachyJoe/FCPDWorkbench.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/FlachyJoe/FCPDWorkbench/context:python)

The [FCPD](https://github.com/FlachyJoe/FCPD) workbench bridges [FreeCAD](https://github.com/FreeCAD/FreeCAD) (FC), an open source CAD program with [Pure-Data](-data/pure-data) (PD), a real-time computer music system.

## Aim

FreeCAD is more than just a CAD program and Pure-Data is more than just *"a free real-time computer music system"*.
Using a real-time visual programming language to control FreeCAD can results in an orchestrated animation system or a procedural modeling one. Vice-versa, imagine a real-time performance with visual/musical effects controlled by FreeCAD virtual objects.

As you can start to see, imagination and programming skills are one's only limitation when using FCPD.

<p align=center>
    <i>Sample</i></br>
    <img src="https://raw.githubusercontent.com/FlachyJoe/FCPD/main/doc/sample-animate.gif" width=800/>
</p>

## Requirements

The PySide2 Python bindings for Qt5 Network is required. Linux users ca install python3-pyside2.qtnetwork

External libraries are needed for Pure-Data :
* [list-abs](https://puredata.info/downloads/list-abs)
* [iemlib](https://puredata.info/downloads/iemlib)

See Pure-Data documentation to install them or use an already populated distribution as [Purr-Data](http://l2ork.music.vt.edu/main/make-your-own-l2ork/software/).

## Status: WIP

This workbench is under development. Feel free to test, report bugs, provide feedback, and participate. Thank you!

## Feedback

Bugs, feature requests, and inquiries? Please open tickets in the repo's issue queue. You can also follow progress via the [dicussion thread](https://forum.freecadweb.org/viewtopic.php?f=24&t=51429) on the FreeCAD forum.

## License

Copyright 2020 @flachyjoe and other contributors

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
