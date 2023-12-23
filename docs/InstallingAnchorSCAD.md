# Installing AnchorSCAD

AnchorSCAD can be downloaded using Git from the [AnchorSCAD Github](https://github.com/owebeeone/anchorscad.git) repository. It will also require the [PythonOpenScad Git](https://github.com/owebeeone/pythonopenscad.git) repository and a number of other easily downloadable tools.

This software is provided under the terms of the LGPL V2.1 license. See the [License](#_f2cn9t1bbfvs) section in this document for more information.
# Requirements
All the required PIP packages are provided in the [requirements.txt](https://github.com/owebeeone/anchorscad/blob/master/src/anchorscad/requirements.txt) in the [AnchorSCAD Github](https://github.com/owebeeone/anchorscad.git) repository.

Non [PyPi PIP](https://pypi.org/project/pip/) packages required are:

- [Python](https://www.python.org/) 3.9 or higher
- [OpenSCAD](https://openscad.org/) 2021.01 or higher
- [Graphviz](https://graphviz.org/) 2.30.2 or higher (likely works with earlier versions)

[Git](https://git-scm.com/) is also required for downloading the [AnchorSCAD](https://github.com/owebeeone/anchorscad.git) and [PythonOpenScad](https://github.com/owebeeone/pythonopenscad.git) repositories and also for contributing any models to [AnchorSCAD](https://github.com/owebeeone/anchorscad.git)‘s .models package or bug fixes or improvements.

It is highly recommended that a Python IDE be used. While not endorsing any IDE in particular, I have found LiClipse (or Eclipse + Pydev) and VS Code work sufficiently well. An old fashioned simple editor and command line execution of shape modules may be used if that is a preference.
## Linux (Debian, Ubuntu, Raspberry Pi OS)

On Linux (Debian, Ubuntu, Raspberry Pi etc based distros), the following commands pasted into a terminal running bash should result in a working environment.


	sudo apt install openscad graphviz python3 git
	mkdir -p ~/git
	cd ~/git
	git clone https://github.com/owebeeone/anchorscad.git
	cd anchorscad
	git clone https://github.com/owebeeone/pythonopenscad.git
 	pip3 install -r src/anchorscad/requirements.txt

	### If you want the "stable" branch, use this after running the above.
	git fetch origin stable:stable
	git checkout stable


## Windows
Download and install the latest versions of:

- [Python](https://www.python.org/) 3.9 or higher
- [OpenSCAD](https://openscad.org/) 2021.01 or higher
- [Graphviz](https://graphviz.org/) 2.30.2 or higher (likely works with earlier versions)

After installing those packages, start a new “cmd” shell terminal and run the following:

	cd %USERPROFILE%
	mkdir git   # Don’t run if the git directory already exists.
	cd git
	git clone https://github.com/owebeeone/anchorscad.git
	cd anchorscad
	git clone https://github.com/owebeeone/pythonopenscad.git
	pip3 install -r src/anchorscad/requirements.txt

	REM ### If you want the "stable" branch, use this after running the above.
	git fetch origin stable:stable
	git checkout stable

 
## Testing The Installation
To verify that it is installed you can run a module like so:


	python3 src/anchorscad/run.py src/anchorscad/extrude.py

Or you can run a longer test where every shape is run and images of all example shapes are created.

	python3 src/anchorscad/run.py src/anchorscad/runner/anchorscad\_runner.py ../..

The generated files will reside in “src/anchorscad/runner/generated”.
# Running AnchorSCAD Modules

Once everything is installed, you can open your favourite IDE but you will need to set the appropriate PYTHONPATH environment variable.

You can also use the “python3 src/anchorscad/run.py” command to run Python modules that depend on AnchorSCAD or PythonOpenSCAD which only sets the PYTHONPATH environment variable and current directory to the appropriate locations.

You can now check out the [Quick Start](https://docs.google.com/document/u/0/d/1p-qAE5oR-BQ2jcotNhv5IGMNw_UzNxbYEiZat76aUy4/edit) instructions to start building your models.

# License
[AnchorSCAD](https://github.com/owebeeone/anchorscad.git) is available under the terms of the [GNU LESSER GENERAL PUBLIC LICENSE](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html#SEC1).

Copyright (C) 2022 Gianni Mariani

[AnchorSCAD](https://github.com/owebeeone/anchorscad.git) and [PythonOpenScad](https://github.com/owebeeone/pythonopenscad.git) is free software; you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation; either version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this library; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

