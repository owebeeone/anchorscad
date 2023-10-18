# anchorscad
A Python 3D modelling API for generating [OpenSCAD](http://www.openscad.org/) source code. This library simplifies the creating of 3D models and contains a suite of completed models including Raspberry Pi cases and other models.

# AnchorSCAD Quick Start
Gianni Mariani	 Mar-2022

AnchorSCAD is a Python 3D modelling API for OpenSCAD. This document covers the minimal set of concepts to grasp in order to build AnchorSCAD shapes.

[This document can be found here](https://docs.google.com/document/d/1p-qAE5oR-BQ2jcotNhv5IGMNw_UzNxbYEiZat76aUy4/edit?usp=sharing) on Google Docs which contains figures that are not currently provided here. Unfortunately, exporting markdown from a Google Doc drops some content.

It’s assumed that the reader is familiar with the Python programming language, especially classes, inheritance, dataclasses and decorators.

For more information about why [AnchorSCAD](https://docs.google.com/document/u/0/d/1yz5QjYTP7aOi6IRqGXDXWZadRwJOYG2clJnmceQCqxg/edit), follow the [link](https://docs.google.com/document/u/0/d/1yz5QjYTP7aOi6IRqGXDXWZadRwJOYG2clJnmceQCqxg/edit).

### How do I get set up? ###

You can follow the [installation instructions](https://github.com/owebeeone/anchorscad/blob/master/docs/InstallingAnchorSCAD.md) to install AnchorSCAD and the prerequisite software.
# Simple Shape
AnchorSCAD provides tools to wrap your creations in its own Shape class but the example below is simplified purely to show how shapes are composed in AnchorSCAD.  The code below will print text of an OpenSCAD script to standard output that will render a box tube.

[See the source document for images.](https://docs.google.com/document/d/1p-qAE5oR-BQ2jcotNhv5IGMNw_UzNxbYEiZat76aUy4/edit#heading=h.6l6z7i8i9vyk)

	A simple composition example of a box tube using AnchorSCAD.
	
	import anchorscad as ad
	
	# Create a shape that we build upon.
	maker = ad.Box([20, 20, 40]).solid('box').at('centre')
	
	# Add a hole shape.
	hole = ad.Box([10, 10, 40.001]).hole('hole').at('centre')
	maker.add_at(hole, 'centre')
	
	# Render and print the OpenSCAD file for the shape.
	print(ad.render(maker).rendered_shape)

![AnchorScad example1](anchorscad/assets/quick_start_example1.png)


This code above demonstrates how to compose models as holes and solids but AnchorSCAD also supports the other OpenSCAD compositions like intersection, unions, hull etc..

Things to note from this example:

 * To compose a shape it must be given a name and a composition mode. In this case we have two shapes named ‘box’ and ‘hole’ and the compositions are solid() and hole().
 * Once a shape is named it is also given a frame of reference and this becomes a builder object which can have more shapes added. Note that once a builder is added to another builder it is copied, hence subsequent changes to the added builder will not be reflected in the final composition.

# Composite Shapes
The following code snippet also generates a similar box tube shape as demonstrated in the previous example, but as an AnchorSCAD Shape class. This demonstrates AnchorSCAD’s “parametric” tools. Running this code below will generate a file named “**`examples_out/anchorcad_SquarePipe_default_example.scad`**“ but it can also be imported into other Python programs to provide the "[SquarePipe](http://docs.google.com/document/d/1uTWqF82tEMreAwSKY09njCfgS8xrEtputkNFxwWj_bs/edit)" class as a reusable shape.

[See the source document for images.](https://docs.google.com/document/d/1p-qAE5oR-BQ2jcotNhv5IGMNw_UzNxbYEiZat76aUy4/edit#heading=h.g10req9fn53z)

    import anchorscad as ad
    EPSILON=1.0e-3
    @ad.shape
    @ad.datatree  # wrapper over dataclasses
	class SquarePipe(ad.CompositeShape):
	    '''Pipe with box section consisting of an outer box with an 
	    inner box hole.'''
	    size: tuple
	    wall_size: float=5.0
	     
	    EXAMPLE_SHAPE_ARGS=ad.args((70, 50, 30))
	    
	    def build(self) -> ad.Maker:
	        maker = ad.Box(self.size).solid('outer').at('centre')
	        # Make the inner box slightly larger to stop tearing 
	        # when rendered.
	        inner_size = (self.size[0] - 2 * self.wall_size,
	                      self.size[1] - 2 * self.wall_size,
	                      self.size[2] + EPSILON)
	        maker2 = ad.Box(inner_size).hole('hole').at('centre')
	        maker.add_at(maker2, 'centre')
	        return maker
    
	MAIN_DEFAULT=ad.ModuleDefault(True) # Set default for --write
	if __name__ == '__main__':
	    ad.anchorscad_main()

	![AnchorScad example2](quick_start_example2.png)

Note the build() function is called via the [dataclass](https://docs.python.org/3/library/dataclasses.html) generated __init__() constructor function. build() must return the final shape (maker) object representing the constructed shape.

While it is possible to use AnchorSCAD without the [dataclass](https://docs.python.org/3/library/dataclasses.html) decorator, it greatly simplifies the code when it’s used and it’s highly recommended it be used. AnchorSCAD also extends the functionality of [dataclass](https://docs.python.org/3/library/dataclasses.html) with the anchorscad [datatree](https://github.com/owebeeone/anchorscad/blob/master/src/anchorscad/datatree.py) decorator. Datatree is a wrapper over dataclass that provides automated parameter injection and binding allowing for the composition of many shapes without requiring the manual and error prone duplication of all the parameters, defaults and documentation. More information about [datatree](https://docs.google.com/document/d/1uTWqF82tEMreAwSKY09njCfgS8xrEtputkNFxwWj_bs/edit?usp=sharing) can be found [here](https://docs.google.com/document/d/1uTWqF82tEMreAwSKY09njCfgS8xrEtputkNFxwWj_bs/edit?usp=sharing).

# Use [template.py](https://github.com/owebeeone/anchorscad/blob/master/src/anchorscad/template.py) to Create New Shapes
The file in the anchorscad package named “[template.py](https://github.com/owebeeone/anchorscad/blob/master/src/anchorscad/template.py)” should be used as your base template whenever creating a new anchorscad shape Python module. This file contains a simple “CompositeShape” class. The name of the class, the docstring, fields and implementation of the build() function should all be specialised for the shape being coded. Of course, multiple shape classes can exist in the same Python module and it makes sense that exclusively related Shapes should exist within the same module. There also exists another template named [template_with_dt_node.py](https://github.com/owebeeone/anchorscad/blob/master/src/anchorscad/template_with_dt_node.py) that contains a template using [datatree](https://github.com/owebeeone/anchorscad/blob/master/src/anchorscad/datatree.py) nodes.

## **`anchorscad_main()`**
All AnchorSCAD shape modules should include the following lines at the end of the module. Running modules containing these lines will render, and therefore test the code for each shape class defined in the module.

    if __name__ == '__main__':
        ad.anchorscad_main()


By default, ad.anchorscad_main() does not write rendered files, however if the “--write” command line parameter is provided, files for each shape will be generated and placed in the “examples_out” directory in the current working directory. Alternatively, adding a module variable named MAIN_DEFAULT will change options defaults for anchorscad_main() so that files are written by default.

    MAIN_DEFAULT=ad.ModuleDefault(True)

ad.anchorscad_main() will also render a graph of the shape hierarchy if the “--graph_write” parameter is provided or MAIN_DEFAULT set to:

    MAIN_DEFAULT=ad.ModuleDefault(True, True, True)

## CompositeShape
The anchorscad.CompositeShape class is the most commonly used base class as it provides all the properties of an anchorscad.Shape class while also providing a scaffold for creating easy to use parameterized shapes with a complex shape hierarchy.

In general, it's best to keep the complexity of a single CompositeShape class to a minimum and build a deeper hierarchy of simple CompositeShapes shapes.

## EXAMPLE_SHAPE_ARGS
In order to create example models, the EXAMPLE_SHAPE_ARGS class variable will be used to create a single “default” example when anchorscad_main or the “anchorscad_runner” is executed. The example below passes a size of (70, 50, 30) to the constructor of the SquarePipe shape when the example is created.

Note that EXAMPLE_SHAPE_ARGS should not have a Python type annotated as it should not be a dataclass field.

	class SquarePipe(ad.CompositeShape):
	    ...
	    EXAMPLE_SHAPE_ARGS=ad.args((70, 50, 30))

Having anchors rendered on the example shapes also provides a powerful diagnostic tool which is supported by providing a list of EXAMPLE_ANCHORS to render. Results from the anchorscad.surface_args and inner_args functions can be used in the EXAMPLE_ANCHORS list. (Note: inner_args() will not render an anchor’s parameters while surface_args() will).

AnchorSCAD supports multiple additional example shapes using the (unannotated) EXAMPLES_EXTENDED class variable containing a dictionary of “example name” keys with anchorscad.ExampleParams values.

# Shape Building
AnchorSCAD has a primary “Shape” type. To use a shape in AnchorSCAD, a name for the shape is *required*. A name is usually a string literal (str object) but can be any immutable, hashable, [repr](https://docs.python.org/3/library/functions.html#repr)-izable object, commonly a tuple of str and int if not a simple str object. Providing a “name” and a Mode to a shape results in a “NamedShape” and other optional attributes can be applied, (like colour, debug or other inheritable attributes). Finally, an anchor can be applied to provide the orientation and position of the shape. A single instance of a shape could be used multiple times with a different name and at() location. Shapes are copied (if mutable) when added to a Maker. Below is an example of a simple Box shape being named and positioned.

![AnchorScad example2](quick_start_maker.png)

A Maker is also an anchorscad.Shape. A Maker in particular is a builder of a node in a shape hierarchy. Consider it a collection of other Maker objects. Shapes can have ‘anchors’ that are used to create frames of reference. i.e. Anchors have both position and orientation. The anchors in a Maker are found by looking up the name specified in the anchor with the named shapes in the Maker itself, and then applying the remaining anchor attributes to the resulting entry. There is a special case that if omitted, the first shape need not be named in the anchor, this can occasionally lead to naming ambiguity but is especially useful in preserving anchor validity when adding nodes to the shape hierarchy.

Note that the evaluated form of an anchor is represented as an anchorscad.GMatrix type defined in AnchorSCAD’s “linear” module (i.e. a [4x4 homogeneous matrix](https://www.brainvoyager.com/bv/doc/UsersGuide/CoordsAndTransforms/SpatialTransformationMatrices.html)). When adding another shape, you’re actually adding another Maker. The Maker.add_at() allows the specification of where (position + orientation) is placed relative to the shape being modified.

Note the terms “shape” and  “model” are used interchangeably since an AnchorSCAD model that consists of composing many “shapes” is itself also an AnchorSCAD “Shape”.

An AnchorSCAD shape is a subclass of the anchorscad.Shape class. The constructor parameters are arbitrary and specific to the implemented shape. Most AnchorSCAD models use the Python dataclass or anchorscad.datatree decorators to simplify the generation of Shape classes.

[See the source document for images.](https://docs.google.com/document/d/1p-qAE5oR-BQ2jcotNhv5IGMNw_UzNxbYEiZat76aUy4/edit#heading=h.o82ht1woamx1)

## An Hello World / SquarePipe Example
The anchorscad.models.basic.SquarePipe model demonstrates the basic construction of a CompositeShape. The CompositeShape will likely be the most used base class in anchorscad because most shapes are built from other shapes.

The resultant shape will consist of a Box with a smaller Box “hole” aligned at the centres, hence a “square pipe”.

	import anchorscad as ad
	EPSILON=1.0e-3
     
	@ad.shape
	@ad.datatree
	class SquarePipe(ad.CompositeShape):
	    '''Pipe with box section consisting of an outer box with an 
	    inner box hole.'''
	    size: tuple=ad.dtfield(doc='Overall size of SquarePipe shape.')
	    wall_size: float=ad.dtfield(5.0, 'Wall thickness of SquarePipe shape')
	    
	    EXAMPLE_SHAPE_ARGS=ad.args((70, 50, 30))
	    EXAMPLE_ANCHORS=(ad.surface_args('face_centre', 5),
	                     ad.surface_args('inner', 'face_centre', 2),)
	    
	    def build(self) -> ad.Maker:
	        maker = ad.Box(self.size).solid('outer').at('centre')
	        # Make the inner box slightly larger to stop tearing
		    # when rendered.
	        inner_size = (self.size[0] - 2 * self.wall_size,
	                      self.size[1] - 2 * self.wall_size,
	                      self.size[2] + EPSILON)
	        maker2 = ad.Box(inner_size).hole('hole').at('centre')
	        maker.add_at(maker2, 'centre')
	        return maker
	
	    @ad.anchor('Inner hole.')
	    def inner(self, *args, **kwds):
	        # Make Z axis point out in holes.
	        return self.maker.at('hole', *args, **kwds) * ad.ROTX_180
     
	#MAIN_DEFAULT=ad.ModuleDefault(True) # Set default for -write
	if __name__ == '__main__':
	    ad.anchorscad_main() 

The build() function (called by the dataclass/datatree generated constructor) after the constructor has populated the instance fields is used to create the composite shape then return the Maker object. The returned shape will have its anchors exposed as the CompositeShape object’s anchors.

AnchorSCAD modules should call ad.anchorscad_main() as its main function call. (use the –write command line argument or add a “MAIN_DEFAULT=ad.ModuleDefault(True)” definition in the module to generate the .scad files in the “examples_out” directory.)  When the module is run as a main program, it will identify all shapes decorated with the “@ad.shape” function and execute and render the shapes with the configured example parameters. These shape python modules can still be imported by other shape python modules to allow for complex multi-python module hierarchical shapes.

Defining shape specific anchors is done using the @ad.anchor as shown with the “inner(self, *args, **kwds)“ function. The function name becomes the anchor name. In this case, “inner” anchor references the 'hole' shape within the maker’s frame of reference and rotates along the X axis so that the resulting surface anchor has the Z axis pointing out of the shape’s surface which is the AnchorSCAD convention.

The maker.add_at() function is used to anchor a shape at an anchor point in the maker. Chaining .add_at() calls is possible since the return value is the maker object being called but chaining .add_at() calls is not always desirable.

The result of running the SquarePipe module (with EXAMPLE_ANCHORS removed) is the following OpenSCAD file.

	// 'None : _combine_solids_and_holes'
	union() {
	  // '_combine_solids_and_holes'
	  difference() {
	    // 'default : _combine_solids_and_holes'
	    union() {
	      // 'default'
	      multmatrix(m=[[1.0, 0.0, 0.0, -35.0], [0.0, 1.0, 0.0, -25.0], [0.0, 0.0, 1.0, -15.0], [0.0, 0.0, 0.0, 1.0]]) {
	        // 'outer : _combine_solids_and_holes'
	        union() {
	          // 'outer'
	          cube(size=[70.0, 50.0, 30.0]);
	        }
	      }
	    }
	    // 'default'
	    multmatrix(m=[[1.0, 0.0, 0.0, -30.0], [0.0, 1.0, 0.0, -20.0], [0.0, 0.0, 1.0, -15.0005], [0.0, 0.0, 0.0, 1.0]]) {
	      // 'hole : _combine_solids_and_holes'
	      union() {
	        // 'hole'
	        cube(size=[60.0, 40.0, 30.001]);
	      }
	    }
	  }
	}

Below is an image of the resulting OpenSCAD render (including EXAMPLE_ANCHORS).

[See the source document for images.](https://docs.google.com/document/d/1p-qAE5oR-BQ2jcotNhv5IGMNw_UzNxbYEiZat76aUy4/edit#heading=h.tmi9129nbyll)

[See how to keep holes when composing shapes.](https://docs.google.com/document/d/1dzWQPXcKU3TKnAUiqt6m0hTi0N4WW7o3GempQX9IVjQ/edit?usp=sharing)
