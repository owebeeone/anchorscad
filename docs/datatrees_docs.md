# Datatrees

Building complex hierarchical data objects using 
[`dataclasses`](https://docs.python.org/library/dataclasses.html) reduces
much of the otherwise needed boilerplate code. This obviously being the point of 
[`dataclasses`](https://docs.python.org/library/dataclasses.html). While 
using [`dataclasses`](https://docs.python.org/library/dataclasses.html)
to develop [AnchorSCAD](https://github.com/owebeeone/anchorscad)
I found it to be still a very verbose and repetitive and subsequently
fragile when building complex 3D models.

# Introducing datatrees

[`datatrees`](https://github.com/owebeeone/anchorscad/blob/master/src/anchorscad/datatrees.py) 
extends (as a wrapper over `datatlasses.dataclass`) to include:

* Field injection
* Field binding
* `self` factory default

[`datatrees`](https://github.com/owebeeone/anchorscad/blob/master/src/anchorscad/datatrees.py)
can dramatically reduce the overall boilerplate code, however, one still needs to be careful
that the datatrees bindings produce the desired outcomes particularly when
a multiple classes being injected may cause undesriable name collission.

# Field injection and Field binding

Often one desires building dataclass objects containing other dataclass objects
from within the `__post_init__` function potentially with many instances of the
same dataclass type. When creating [AnchorSCAD](https://github.com/owebeeone/anchorscad) 
models in particular 
it may be necessary to build many instances of a dataclass type. For example a 3D 
model of hole gauge, a plate with multiple holes with different sizes. The height (z)
parameter may be shared with all the contained holes while the radius of each 
individual hole would be specific to that hole. Such a model can be found here
([`hole_guage`](https://github.com/owebeeone/anchorscad/blob/master/src/anchorscad/models/tools/hole_gauge.py)).

# Datatree Wraps Dataclass

```
@datatree
class A:
    '''Demonstrates Python dataclasses default value
    functionality. Even though @datatree is used, this
    example only uses the base Python @dataclass
    functionality.
    '''
    v1: int
    v2: int=2
    v3: int=field(default=3)
    v4: int=field(default_factory=lambda: 7 - 3)
```

Construct with v1 provided..

```
A(v1=1)
  -> A(v1=1, v2=2, v3=3, v4=4)
```

Comparison of two different instances with the same value.

```
A(v1=2) == A(v1=2)
  -> True
```

## Help for Class A

```
class A(builtins.object)
 |  A(v1: int, v2: int = 2, v3: int = 3, v4: int = <factory>, override: anchorscad.datatrees.Overrides = None) -> None
 |
 |  Demonstrates Python dataclasses default value
 |  functionality. Even though @datatree is used, this
 |  example only uses the base Python @dataclass
 |  functionality.
 | …
```

## Datatree Inject and Bind

```
@datatree
class Anode:
    '''Injects fields from class A and provides a
    default value for A.v1. The a_node field becomes a
    callable object that provides an instance of A
    with field values retrieved from self.
    '''
    v1: int=55
    a_node: Node=Node(A)  # Inject field names from A
```

### Injected Fields

Datatree uses the `a_node` field in `class Anode` above to inject `class A` constructor parameters as fields in the containing class (`class Anode`). Node allows specification of name mappings with mapping dictionaries, prefixes, suffixes or specific exclusion of
specific parameters.

In the `class Anode` example above, the field `v1` is specified so the field `v1` from `class A`
will not be injected and the default parameters specified in `class Anode` will remain.
However the remaining parameters (`v2`, `v3` and `v4`) will be injected with the 
default values specified in `class A`.

Constructing a default `class Anode` will demonstrate the injected values, see parameters
`v2`, `v3` and `v4` below:

```
Anode()
  -> Anode(v1=55, a_node=BoundNode(node=Node(clz_or_func=A, use_defaults=True, suffix='', prefix='', expose_all=True, node_doc=None)), v4=4, v2=2, v3=3)     
```

Note how the `a_node` field is transformed into a `BoundNode`. This is a factory for 
A objects that will pull all constructor parameters from the `Anode` object that created it.
The example below shows how the `a_node` constructs a ` class A` object pulling all 
parameters from the instance containing it.


# Example of field binding,

```
Anode().a_node()
  -> A(v1=55, v2=2, v3=3, v4=4)
```

The `BoundNode` factory also allows all the parameters provided in the associated 
class (or function) from the corresponding Node. In this case, the `v3` parameter
is overridden with the value `33`.

# Example of overriding the field binding.

```
Anode().a_node(v3=33)
  -> A(v1=55, v2=2, v3=33, v4=4)
```

# Binding Parameters In `self default` Fields

`dataclasses.field` provides field attributes `default` and `factory_default` parameters, the
latter being evaluated at object initialization. datatree.dtfield wraps `dataclasses.field`
providing a `self_default` parameter that takes a function object with a single parameter. 
At class initialization, these functions are evaluated with the object instance as its value.

The order of evaluation is the order in which they are declared in the class additionally they
are evaluated after all the `Node` fields have been bound (transformed into BoundNode factories). 
This allows fields specified with a `self_default` attribute to use any field specified with `Node` 
as long as invoking `BoundNodes` factories (bindings) do not attempt to access `self_default` 
fields that are not yet evaluated.

# Injecting Computed Defaults

In the example below, `class Bind` defines the field `v1` as a computed sum `v2 + v3`.


```
@datatree
class Bind:
    '''Demonstrates the use of a computed default value.
    Often a value used in nodes should be computed with other parameters
    provided to this instance.'''
    v1: int=dtfield(self_default=lambda s: s.v2 + s.v3)
    a_node: Node=field(default=Node(A), repr=False, init=False
```

The default value of `class Bind` is `Bind(v1=5, v2=2, v4=4, v3=3)`. Note the value of
`v1` being the specified sum.

This demonstrates the value of `v1` is evaluated with the values of `v2` and `v2` that are
provided in the constructor.

```
Bind(v2=10)
  -> Bind(v1=13, v2=10, v4=4, v3=3)
```

# Injecting Function Parameters

The example below shows that any function (or lambda) can be used as a `datatrees.Node`.
In the example below, the fields `lamba_node` and `func_node` use different declaration of
essentially the same function but the parameter names from `func_a` are also injected.

```
def func_a(x: int=1, y:int=3):
    return x + y

@datatree
class BindFunc:
    '''Injected function parameters.'''
    a: int=1
    b: int=1
    lambda_node: Node=Node(lambda a, b: a + b)
    func_node: Node=Node(func_a)
```

The lambda_node will bind the values `a` and `b` and pass it to the lambda in the
in the class declaration.

```
BindFunc().lambda_node()
  -> 2
```

This demonstrates the default value for `x` being overridden and the default value for `y` being used in the call to `func_a`.

```
BindFunc(x=5).func_node()
  -> 8
```

# Inheritance with Datatrees

```
@datatree
class E:
    '''Using the dtfield() function to create a BindingDefault entry.'''
    v1: int=1
    v2: int=2
    v_computed: Node=dtfield(self_default=lambda s: s.v1 + s.v2)


@datatree
class F(E, A):
    '''Inheritance of datatree classes is allowed, fields are merged.
    in the same way as dataclasses.'''
```


```
F()
  -> F(v1=1, v2=2, v3=3, v4=4, v_computed=3)

F(v4=44)
  -> F(v1=1, v2=2, v3=3, v4=44, v_computed=3)
```

# Mapping Injected Names with a Prefix or Suffix

It is often important to inject the same or similar class with identical field names. 
`datatree.Node` provides for `prefix=` and `suffix=` specifiers that can be used to
map injected parameter names.

```
@datatree
class C:
    '''Multiple nodes of the same type with parameter name mapping.'''
    a_v1: int=11
    a_node: Node=field(default=Node(A, prefix='a_'), repr=False)
    b_v1: int=12
    b_node: Node=field(default=Node(A, prefix='b_'), repr=False)
    computed: int=BindingDefault(lambda s: s.a_v2 + s.b_v2)
    
    def __post_init__(self):
        pass # Called after initialization is complete.
        
    def make_stuff(self):
        return self.a_node(v2=22), self.b_node(), self.computed
```

Note the call below to `make_stuff()` that returns a tuple of the result of invoking 
`a_node()` and `b_node()` from a default `class C` instance. The fields `a_v1` and `b_v1`
are injected into calls for `a_node()` and `b_node()` respectively and hence the
difference in the instances of the instances of `class A` being created.

```
C().make_stuff()
  -> (A(v1=11, v2=22, v3=3, v4=4), A(v1=12, v2=2, v3=3, v4=4), 4)
```

# Override

As mentioned earlier, the `override` parameter should only be used for debugging
purposes. This uses the `datatrees.override` function to generate a `datatrees.Override`
instance. The parameters to `datatrees.override` are simply parameters to override
that will replace any provided value including explicit values. Since the override
parameter is passed down, it also is able to hierarchically provide override values
for contained bound nodes.


```
@datatree
class O:
    '''Deep tree of injected fields.'''
    c_node: Node=dtfield(Node(C, 'a_v1'), init=False, repr=False
```

Note that `class O` has only one injected parameter, `a_v1`. The default constructor demonstrates the only provided parameter. The default of `a_v1` is from `class C`’s 
default value for `a_v1`,

```
O()
  -> O(a_v1=11)
```

This demonstrates the node generating an instance of `class C`.

```
O().c_node()
  -> C(a_v1=11, a_v2=2, a_v4=4, a_v3=3, b_v1=12, b_v2=2, b_v4=4, b_v3=3, computed=4)
```

This demonstrates using the override parameter with an `Override` specifier that overrides
multiple layers within the `class O` datatree class.  Node how the `b_node` override specifier
for `v2=909090` is reflected in the resulting value of `A()` while `b_node` is called with 
a value for `v2` that is ignored.

```
O(
    override=override(
        c_node=dtargs(
            override=override(
                b_node=dtargs(v2=909090)
                )))).c_node().b_node(v2=55555)
  -> A(v1=12, v2=909090, v3=3, v4=4)
```

Overriding values in this way can cause code to be fragile as disregarding parameter 
values with those provided by some unrelated function will inevitably cause unexpected
and silent issues to appear which are difficult to diagnose. This is why the `override`
parameter should only be used for debugging purposes and not otherwise used. 

# Hole Gauge Example

The `hole_guage.py` code below (found in
[`hole_guage`](https://github.com/owebeeone/anchorscad/blob/master/src/anchorscad/models/tools/hole_gauge.py))
demonstrates how two `anchorscad.CompositeShape` 3D models can be used where one
shape class instance consists of multiple instances of another 3D model and the parameters
can be shared. It also demonstrates how `self_default` bindings can be used in conjunction
with `BoundNode` factories.


To demonstrate the doc field attribute, the following is the `pydoc` generated for 
`HoleGuage`. Note the fields `fn`, `fa` and `fs` are used in AnchorSCAD and it’s desirable
to pass these attributes to constructors of contained classes as these are used by the 
rendering engine to determine the complexity of the polyhedrons approximations of curved 
surfaces. This is a feature of the `anchorscad.ShapeNode` subclass of `datatrees.Node`.

```
    class HoleGauge(anchorscad.core.CompositeShape)
     |  HoleGauge(hole_rss: Tuple[Tuple[float]], sep: float = 5, fn: int = None, epsilon: float = 0.005, fa: float = None, h: float = 5, fs: float = None, override: anchorscad.datatrees.Overrides = None) -> None
     |  
     |  A plate with a matrix of holes of different radii provided in hole_rss.
     |  Args:
     |      hole_rss: Tuple of tuple of hole radii
     |      sep: None: Margin of separation between holes and edges
     |      fn: None: None: fixed number of segments. Overrides fa and fs
     |      epsilon: None: Fudge factor to remove aliasing
     |      fa: None: None: minimum angle (in degrees) of each segment
     |      h: None: Depth of plate
     |      fs: None: None: minimum length of each segment
     |  Other args:
     |      override
   …
```


### From: [`hole_guage`](https://github.com/owebeeone/anchorscad/blob/master/src/anchorscad/models/tools/hole_gauge.py)

The code below is a 3D model using AnchorSCAD that generates a plate of holes.
The `SingleHoleGauge` class generates a single row of holes with radii specified by the 
hole_rs parameter and the thickness of the plate specified by the `h` parameter. The 
`HoleGauge` class is similar but generates a grid of holes specified by a tuple of tuples of hole radii via parameter `hole_rss`.

`HoleGauge` generates a number of `SingleHoleGauge` shapes and stitches them together
but also creates an overall plate sized to contain all the `SingleHoleGauge` shapes  in a single ‘assembly’ plate.

```
import anchorscad as ad
from typing import Tuple

@ad.shape
@ad.datatree(frozen=True)
class SingleHoleGauge(ad.CompositeShape):
    '''A plate with a line of holes of different radii provided in hole_rs.'''
    hole_rs: Tuple[float]=ad.dtfield(doc='Tuple of hole radii')
    h: float=ad.dtfield(5, 'Depth of plate')
    sep: float=ad.dtfield(5, 'Margin of separation between holes and edges')
    x: float=ad.dtfield(doc='Width (x) of plate', 
                        self_default=lambda s: 
                            sum(s.hole_rs) * 2 + (len(s.hole_rs) + 1) * s.sep)
    y: float=ad.dtfield(doc='Depth (y) of plate', 
                        self_default=lambda s: max(s.hole_rs) * 2 + 2 * s.sep)
    plate_size: Tuple[float]=ad.dtfield(doc='The (x, y, z) size of the plate Box shape',
                                 self_default=lambda s: (s.x, s.y, s.h - 2 * s.epsilon))
    plate_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='plate_'), init=False)
    hole_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Cylinder, 'h'), init=False)
    epsilon: float=ad.dtfield(0.005, 'Fudge factor to remove aliasing')
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64, hole_rs=(3, 4, 5, 6, 10))
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        maker = self.plate_node().solid('plate').at('centre')
        
        offset = self.sep
        for i, r in enumerate(self.hole_rs):
            hole = self.hole_node(r=r)
            offset += r
            maker.add_at(
                hole.hole(('hole', i))
                    .at('base', post=ad.translate((0, -offset, -self.epsilon))),
                'face_edge', 'base', 1)
            offset += r + self.sep
        return maker
    

@ad.shape
@ad.datatree(frozen=True)
class HoleGauge(ad.CompositeShape):
    '''A plate with a matrix of holes of different radii provided in hole_rss.'''
    hole_rss: Tuple[Tuple[float]]=ad.dtfield(doc='Tuple of tuple of hole radii')
    
    single_hole_gauge: ad.Node=ad.dtfield(
        ad.ShapeNode(SingleHoleGauge,
                     exclude=('hole_rs', 'x', 'y', 'plate_size')),
                     init=False)
    shapes: Tuple[ad.Shape]=ad.dtfield(
            doc='Tuple of shapes placed in the hole gauge plate',
            self_default=lambda s: tuple(s.single_hole_gauge(hole_rs=rs) for rs in s.hole_rss),
            init=False)
    plate_size: Tuple[float]=ad.dtfield(
            doc='The (x, y, z) size of the plate Box shape',
            self_default=lambda s:(
                max(sh.x for sh in s.shapes),
                sum(sh.y for sh in s.shapes) - (len(s.shapes) - 1) * s.sep,
                s.h - 2 * s.epsilon),
            init=False)
    plate_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='plate_'),
                                   doc='The plate node factory',
                                   init=False)
        
    EXAMPLE_SHAPE_ARGS=ad.args(
        fn=64, 
        hole_rss=((3, 4, 5, 6, 8, 10), (16, 14, 12)))
    
    def build(self) -> ad.Maker:
        # Create a builder plate the size of the entire assembly.
        maker = self.plate_node().solid('plate').at('centre')
        
        # Adds all shapes into the assembly plate.
        offset = 0
        for i, shape in enumerate(self.shapes):
            maker.add_at(shape.composite(('inner_plate', i))
                         .at('face_edge', 'base', 0, post=ad.tranY(-offset)),
                         'face_edge', 'base', 0)
            offset += shape.y - self.sep
        return maker

MAIN_DEFAULT=ad.ModuleDefault(True)  # Default to --write

if __name__ == "__main__":
    ad.anchorscad_main()
```
