Installing AnchorSCAD



[Requirements](#_s7psdxljcaf0)

[Linux (Debian, Ubuntu, Raspberry Pi OS)](#_2p4dgxlq5vbn)

[Windows](#_8m9jpsadi5i8)

[Testing The Installation](#_399xlwdmo5lb)

[Running AnchorSCAD Modules](#_x3z9y3464ed4)

[License](#_f2cn9t1bbfvs)



AnchorSCAD can be downloaded using Git from the [AnchorSCAD BitBucket Git](https://bitbucket.org/owebeeone/anchorscad/src/master/) repository. It will also require the [PythonOpenScad Git](https://bitbucket.org/owebeeone/pythonopenscad/src/master/) repository and a number of other tools easily downloadable.

This software is provided under the terms of the LGPL V2.1 license. See the [License](#_f2cn9t1bbfvs) section below for more information.
# Requirements

Non [PyPi PIP](https://pypi.org/project/pip/) packages

- [Python](https://www.python.org/) 3.9 or higher
- [OpenSCAD](https://openscad.org/) 2021.01 or higher
- [Graphviz](https://graphviz.org/) 2.30.2 or higher (likely works with earlier versions)

[Git](https://git-scm.com/) is also required for downloading the [AnchorSCAD](https://bitbucket.org/owebeeone/anchorscad/src/master/) and [PythonOpenScad](https://bitbucket.org/owebeeone/pythonopenscad/src/master/) repositories and also for contributing any suggested [AnchorSCAD](https://bitbucket.org/owebeeone/anchorscad/src/master/) improvements or models.

It is highly recommended that a Python IDE be used. While not endorsing any IDE in particular, I have found LiClipse (Eclipse + Pydev) and VS Code work sufficiently well. An old fashioned simple editor and command line execution of shape modules may be used if that is a preference.

All the required PIP packages are provided in the [requirements.txt](https://bitbucket.org/owebeeone/anchorscad/src/dev/src/anchorscad/requirements.txt) in the [AnchorSCAD BitBucket](https://bitbucket.org/owebeeone/anchorscad/src/master/) repository.
## Linux (Debian, Ubuntu, Raspberry Pi OS)

On Linux (Debian, Ubuntu, Raspberry Pi etc based distros), the following commands pasted  into a terminal running bash should result in a working environment.


|<p>sudo apt install openscad graphviz python3 git</p><p>mkdir -p ~/git</p><p>cd ~/git</p><p>git clone <https://owebeeone@bitbucket.org/owebeeone/anchorscad.git></p><p>cd anchorscad</p><p>git clone https://owebeeone@bitbucket.org/owebeeone/pythonopenscad.git</p><p>pip3 install -r src/anchorscad/requirements.txt</p>|
| :- |


## Windows
Download and install the latest versions of:

- [Python](https://www.python.org/) 3.9 or higher
- [OpenSCAD](https://openscad.org/) 2021.01 or higher
- [Graphviz](https://graphviz.org/) 2.30.2 or higher (likely works with earlier versions)

After installing those packages, start a new “cmd” shell terminal and run the following:

|<p>cd %USERPROFILE%</p><p>mkdir git   # Don’t run if the git directory already exists.</p><p>cd git</p><p>git clone <https://owebeeone@bitbucket.org/owebeeone/anchorscad.git></p><p>cd anchorscad</p><p>git clone https://owebeeone@bitbucket.org/owebeeone/pythonopenscad.git</p><p>pip3 install -r src/anchorscad/requirements.txt</p>|
| :- |
## Testing The Installation
To verify that it is installed you can run a module like so:


|python3 src/anchorscad/run.py src/anchorscad/extrude.py|
| :- |

Or you can run a longer test like where every shape is run and images of all example shapes are created.

|python3 src/anchorscad/run.py src/anchorscad/runner/anchorscad\_runner.py ../..|
| :- |

The generated files will reside in “src/anchorscad/runner/generated”.
# Running AnchorSCAD Modules

Once everything is installed, you can open your favourite IDE but you will need to set the appropriate PYTHONPATH environment variable.

You can also use the “python3 src/anchorscad/run.py” command to run Python modules that depend on AnchorSCAD or PythonOpenSCAD which only sets the PYTHONPATH environment variable and current directory to the appropriate locations.

You can now check out the [Quick Start](https://docs.google.com/document/u/0/d/1p-qAE5oR-BQ2jcotNhv5IGMNw_UzNxbYEiZat76aUy4/edit) instructions and build your shapes.
# License
[AnchorSCAD](https://bitbucket.org/owebeeone/anchorscad/src/master/) is available under the terms of the [GNU LESSER GENERAL PUBLIC LICENSE](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html#SEC1).

Copyright (C) 2022 Gianni Mariani

[AnchorSCAD](https://bitbucket.org/owebeeone/anchorscad/src/master/) and [PythonOpenScad](https://bitbucket.org/owebeeone/pythonopenscad/src/master/) is free software; you can redistribute it and/or

modify it under the terms of the GNU Lesser General Public

License as published by the Free Software Foundation; either

version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,

but WITHOUT ANY WARRANTY; without even the implied warranty of

MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU

Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public

License along with this library; if not, write to the Free Software

Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

