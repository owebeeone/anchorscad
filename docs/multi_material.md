
# Multi-Material Support in AnchorSCAD

## Introduction
The current development version of OpenSCAD has minimal support for generating multiple models
from a single .scad file. This is called "Lazy Union". The implicit union for all top level shapes 
are rendered as separate models into 3mf files. AnchorSCAD now uses this experimental openscad
"lazy union" feature together with new material and material_map attributes to create Lazy Union enabled files.

(Note that the lazy-union feature needs to be enabled in the Preferences->Features menu or
the '--enable lazy-union' CLI option.)


## Material and MaterialMap Classes
The new `anchorscad.Material` class provides for a name, priority and material kind (type). 
Shapes assigned Materials of a higher priority and a "physical" kind are "subtracted" from shapes 
of materials with a physical kind and lower priority. This gives rudimentary support for removing 
overlapping areas in the design but also supports "meta" models that may be used in the slicer
to provide support controls or regions for special settings. A `Material` is only selected by name
so if two materials but with different priority or kind is selected, only one will apply in an
undefined way. (This may become a fatal error in future versions.)

The `anchorscad.MaterialMap` class is intended for use on a shape that already makes use of
multiple materials but the material assignments need to be adjusted for the containg shape.

All example shapes are generated with the material named `"default"` and priority 5. Example
anchors are rendered with the material named `"anchor"`. This will allow the separation of the model proper and the anchors. By using a different material and "priority", all models with materials of a lower priorty will be made to not overlap in space by using the OpenSCAD difference operator where higher priority models being removed from lower priority models.

## Rendering Multi-Material Models
Material can be assigned to a model using the "material" attribute function. The model below
is a simple "sphere on box" where the material is being selected. Notably, the box is given
a higher priority than the sphere and hence will be take precedence over the sphere where 
they overlap.

The EXAMPLE_ANCHOR is rendered using the "anchor" material and hence will have both the box
and sphere removed.

```python
@ad.shape
@ad.datatree
class MultiMaterialTest(ad.CompositeShape):
    '''
    A basic test of multi-material support. Basically a box with a sphere on top.
    The box and sphere are different materials.
    '''
    xy: float=30
    z: float=10
    
    size: tuple=ad.dtfield(
        doc='The (x,y,z) size of ShapeName',
        self_default=lambda s: (s.xy, s.xy, s.z))
    
    # A node that builds a box from the size tuple. See:
    # https://github.com/owebeeone/anchorscad/blob/master/docs/datatrees_docs.md
    box_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, 'size'))
    
    sphere_r: float=ad.dtfield(self_default=lambda s: s.xy/2)
    
    shpere_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Sphere, prefix='sphere_'))
    
    EXAMPLE_SHAPE_ARGS=ad.args(xy=20, z=10)
    EXAMPLE_ANCHORS=(
        ad.surface_args('sphere', 'top'),)

    def build(self) -> ad.Maker:
        
        box_shape = self.box_node()
        maker = box_shape.solid('box') \
                .material(ad.Material('box', priority=10)) \
                .at('face_centre', 'base', post=ad.ROTX_180)
        maker.add_at(
            self.shpere_node()
                    .solid('sphere')
                    .material(ad.Material('sphere', priority=9))
                    .at('top', rh=1.4),
            'face_centre', 'top')

        return maker
```

The following openscad code is generated. Notably the EXAMPLE_ANCHORS are disabled here
and hence it consists of just box and sphere-box. Notably this uses the "lazy union" feature
that allows the generation of 3mf files with multiple models.


```openscad
// Start: lazy_union
// "pop - Material(name='box', priority=10):solid"
union() {
  // 'None : _combine_solids_and_holes'
  union() {
    // 'default : _combine_solids_and_holes'
    union() {
      // 'box'
      multmatrix(m=[[1.0, 0.0, 0.0, -10.0], 
                    [0.0, 1.0, 0.0, -10.0], 
                    [0.0, 0.0, 1.0, 0.0], 
                    [0.0, 0.0, 0.0, 1.0]]) {
        // 'box : _combine_solids_and_holes'
        union() {
          // 'box'
          cube(size=[20.0, 20.0, 10.0]);
        }
      }
    }
  }
}
// "pop - Material(name='sphere', priority=9):solid"
union() {
  // "priority_cured_Material(name='sphere', priority=9)"
  difference() {
    // 'None : _combine_solids_and_holes'
    union() {
      // 'default : _combine_solids_and_holes'
      union() {
        // 'sphere'
        multmatrix(m=[[1.0, 0.0, 0.0, 0.0], 
                      [0.0, 1.0, 0.0, 0.0], 
                      [0.0, 0.0, 1.0, 14.0], 
                      [0.0, 0.0, 0.0, 1.0]]) {
          // 'sphere : _combine_solids_and_holes'
          union() {
            // 'sphere'
            sphere(r=10.0);
          }
        }
      }
    }
    // 'None : _combine_solids_and_holes'
    union() {
      // 'default : _combine_solids_and_holes'
      union() {
        // 'box'
        multmatrix(m=[[1.0, 0.0, 0.0, -10.0], 
                      [0.0, 1.0, 0.0, -10.0], 
                      [0.0, 0.0, 1.0, 0.0], 
                      [0.0, 0.0, 0.0, 1.0]]) {
          // 'box : _combine_solids_and_holes'
          union() {
            // 'box'
            cube(size=[20.0, 20.0, 10.0]);
          }
        }
      }
    }
  }
}
// End: lazy_union
```

## Slicer Support

Both Prusa and Orca slicers will import geometry from an OpenSCAD generated 3mf file, however to ensure the Z axis is not broken when loading the file you must respond "Yes" to the dialog that says: 

```
This file contains several objects positioned at multiple heights.
Instead of considering them as multiple objects, should 
the file be loaded as a single object having multiple parts?
```

Sadly, this limits the ability to turn off and on various parts of the model. For example, example-anchors should in theory not be sliced as they're just for a visual cues however the
"part type" setting can be used to cause it not to be rendered in the final gcode.

Also, Orca's method for selecting a part is somewhat unintuitive compared to Prusa slicer. Some more serious UI work needs to be done here.

Here is a screenshot of Orca showing the sliced test model.

![Multi Material](assets/multu-material-examp.png?raw=true)

## Future

If OpenSCAD keeps the experimental lazy-union support into the next release, I think this
level of material support is sufficient for AnchorSCAD to be useful.

I want to automate the workflow even more. AnchorSCAD has a generic 3mf file reader/writer 
that extends the datatrees/dataclasses module into xdatatrees. The goal is to make it simpler
to generate 3mf project files directly. I'm hoping to one day render directly to printer
without having to fire up the GUI for the slicer. In particular, filament to material mapping
somewhat difficult since material names are lost using the lazy-union feature.

