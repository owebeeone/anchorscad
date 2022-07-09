
# Datatrees Proposal

Building complex hierarchical data objects using 
[`dataclasses`](https://docs.python.org/library/dataclasses.html) reduces
much of the needed boilerplate code. This obviously being the point of 
[`dataclasses`](https://docs.python.org/library/dataclasses.html). While 
using it to develop [AnchorSCAD](https://github.com/owebeeone/anchorscad)
I found it to be still a very verbose and repetitive when building 
complex 3D models.

# Introducing datatrees

[`datatrees`](https://github.com/owebeeone/anchorscad/blob/master/src/anchorscad/datatrees.py) extends (as a wrapper over `datatrees.datatree`) to include:

* Field injection
* Field binding
* `self` factory default

The [`datatrees`](https://github.com/owebeeone/anchorscad/blob/master/src/anchorscad/datatrees.py) link points to a working implementation including a dubious `override`
feature that is seldom use in debugging situations only.
