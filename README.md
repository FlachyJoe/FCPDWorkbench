## PureData connection workbench for FreeCAD

The [FCPD](https://github.com/FlachyJoe/FCPD) workbench bridges [FreeCAD](https://github.com/FreeCAD/FreeCAD) (FC), an open source CAD program with [Pure-Data](https://github.com/pure-data/pure-data) (PD), a real-time computer music system.

## Aim

FreeCAD is more than just a CAD program and Pure-Data is more than just *"a free real-time computer music system"*.
Using a real-time visual programming language to control FreeCAD can results in an orchestrated animation system or a procedural modeling one. Vice-versa, imagine a real-time performance with visual/musical effects controlled by FreeCAD virtual objects.

As you can start to see, imagination and programming skills are one's only limitation when using FCPD.

## Status: WIP

This workbench is under development. Feel free to test, report bugs, provide feedback, and participate. Thank you!

## Feedback

Bugs, feature requests, and inquiries? Please open tickets in the repo's issue queue. You can also follow progress via the [dicussion thread](https://forum.freecadweb.org/viewtopic.php?f=24&t=51429) on the FreeCAD forum.

## Install

 * Clone the git repository in your FreeCAD Mod path
 * Install Pure-Data and [required external libraries](#Requirements).
 * Launch FreeCAD
 * Load the FCPD workbench
 * Set your Pure-Data binary path in the workbench preference page

## First steps

 * Open a FreeCAD document
 * Load the FCPD workbench
 * Start Pure-Data and internal FreeCAD server by clicking Launch Pure-Data in the FCPD menu or toolbar
 * The opening client.pd window implements the connection to FC, don't close it.
 * Create a new patch from PD File menu
 * Add your needed [fc_…] objects, they are automatically connected to FreeCAD

Take a look in the *pdlib* directory for available objects. Some of them are pd-documented (RMB/Help in PD) and/or listed in the *FCPD-help.pd* file.

## Samples

Please see [FCPDWorkbench_Samples](https://github.com/FlachyJoe/FCPDWorkbench_Samples)

## Requirements

The PySide2 (or PySide6) Python bindings for Qt5 (or Qt6) Network is required. Linux users can install python3-pyside2.qtnetwork (or python3-pyside6.qtnetwork) package.

External libraries are needed for Pure-Data :
* [list-abs](https://puredata.info/downloads/list-abs)
* [iemlib](https://puredata.info/downloads/iemlib)

See Pure-Data documentation to install them with the Deken package system
**OR** install a system package from your distribution repository (e.g. `sudo apt install pd-list-abs pd-iemlib`)
**OR** use an already populated Pure-Data clone as [Purr-Data](http://l2ork.music.vt.edu/main/make-your-own-l2ork/software/) or [PlugData](https://plugdata.org/).

Inverse kinematic features request [ikpy](https://github.com/Phylliade/ikpy).

## License

Copyright 2020-2025 @flachyjoe and other contributors

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

## Background / How it works ?

The FreeCAD workbench is codded with Python, it implements a TCP server to get FUDI message from Pure-Data.

The Pure-Data part is coded in Pure-Data language. Thus it require some extra-libraries : list-abs and iemlib you can find easly in Pure-Data repositories.

As FUDI protocol can only deal with text, all the FreeCAD data are converted to be usable in Pure-Data. Some objects are still not string-representable. These ones are simply keeped in FreeCAD and Pure-Data can refer to them by reference indexes.

Due to the latency in client/server communication and FreeCAD stuff, `fc_` Pure-Data objects are **asynchronous**. So you can't know when outlets trigger. Nevertheless outlets are still triggered right to left.
This breaks the usual PD codding and require some more work to let other objects wait for FC datas.
