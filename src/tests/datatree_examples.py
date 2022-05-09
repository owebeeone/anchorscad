'''
Created on 11 Apr 2022

@author: gianni
'''
import inspect
import re

SP='[ \n\t]'
CLEANER_REGEX=re.compile(
    f'(?:{SP}*describe{SP}*\()?(?:{SP}*lambda{SP}*:)?((?:.|\n)*)(?:{SP}*)?[\)]')
def describe(func):
    src = inspect.getsource(func)
    mtch = CLEANER_REGEX.match(src)
    if mtch:
        src = mtch.group(1).strip()
    try:
        print(f'{src}\n  -> {func()}')
    except Exception as e:
        print(f'{src}\n  -> raises {e}')
        
def doc(msg):
    print('---' + msg)


from anchorscad.datatrees import datatree, Node, BindingDefault, dtfield, field, \
                                 dtargs, override


@datatree
class A:
    '''Demonstrates Python dataclasses default value
    functionality. Even though @datatree is used, this 
    example only uses the base Python @dataclass 
    functionality.
    '''
    v1: int
    v2: int=2
    v3: int=dtfield(default=3)
    v4: int=dtfield(default_factory=lambda: 7 - 3)
    #)

describe(A)
doc('Default construction fails because v1 is required since it has no default.')
describe(lambda: A())
doc('Construct with v1 provided..')
describe(lambda: A(v1=1))
describe(lambda: A(v1=2) == A(v1=2))

help(A)

V4_DEFAULT_FACTORY = lambda: 7 - 3
class A_NotDatatree:
    def __init__(self, v1: int, v2: int = 2, v3: int = 3, v4: int = None):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3
        self.v4 = V4_DEFAULT_FACTORY() if v4 is None else v4
        
    def __repr__(self):
        return f'{self.__class__.__name__}('\
               f'v1={self.v1}, v2={self.v2}, v3={self.v3}, v4={self.v4})'

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.v1 == other.v1 and self.v2 == other.v2 \
            and self.v3 == other.v3 and self.v4 == other.v4
            
describe(A_NotDatatree)
describe(lambda: A_NotDatatree(v1=1))
describe(lambda: A_NotDatatree(v1=2) == A_NotDatatree(v1=2))


@datatree
class Anode:
    '''Injects fields from class A and provides a 
    default value for A.v1. The a_node field becomes a 
    callable object that provides an instance of A
    with field values retrieved from self.
    '''
    v1: int=55
    a_node: Node=Node(A)

describe(Anode)
doc('Example of field injection,')
describe(lambda: Anode())
doc('Example of field binding,')
describe(lambda: Anode().a_node())
describe(lambda: Anode().a_node(v3=33))

@datatree
class Bind:
    '''Demonstrates the use of a computed default value.
    Often a value used in nodes should be computed with other parameters
    provided to this instance.'''
    v1: int=BindingDefault(lambda s: s.v2 + s.v3)
    a_node: Node=Node(A) # Injects v2, V3 and v4.

describe(Bind)
describe(lambda: Bind(v2=10))
describe(lambda: Bind(v2=10).v1)

@datatree
class BindComputed:
    '''Demonstrates the use of a computed default value.'''
    v1: int=1
    a_node: Node=Node(A) # Injects v2, V3 and v4.
    computed: int=BindingDefault(lambda s: s.v2 + s.v3)

describe(lambda: BindComputed(v2=10).computed)


def func_a(x: int=1, y:int=3):
    return x + y

@datatree
class BindFunc:
    '''Injected function parameters.'''
    a: int=1
    b: int=1
    lambda_node: Node=Node(lambda a, b: a + b)
    func_node: Node=Node(func_a)

describe(BindFunc)
describe(lambda: BindFunc().lambda_node())
describe(lambda: BindFunc(x=5).func_node())


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

describe(lambda: C())
describe(lambda: C(b_v2=44).computed)
describe(lambda: C().a_node())
describe(lambda: C(b_v2=22).b_node(v3=33))
describe(lambda: C().make_stuff())


@datatree
class D:
    '''Explicit field mapping.'''
    v1: int=111
    a_v2: int=222
    a_node: Node=dtfield(
        Node(A, 'v1', {'v2' : 'a_v2'}), repr=False, init=False,
            doc='Only v1 and a_v2 are injected.')

describe(D)
describe(lambda: D().a_node())

    
@datatree
class E:
    '''Using the dtfield() function to create a BindingDefault entry.'''
    v1: int=1
    v2: int=2
    v_computed: Node=dtfield(self_default=lambda s: s.v1 + s.v2)

describe(E)
describe(lambda: E(v_computed=55))

@datatree
class F(E, A):
    '''Inheritance of datatree classes is allowed, fields are merged.'''
    # )
    
describe(F)
describe(lambda: F(v4=44))


@datatree
class O:
    '''Deep tree of injected fields.'''
    c_node: Node=dtfield(Node(C, 'a_v1'), init=False, repr=False)

describe(O)
describe(lambda: O().c_node())
describe(lambda: O().c_node(computed=55))

print('Overriding parameters deep within a datatree.')
describe(lambda: O(
    override=override(
        c_node=dtargs(
            override=override(
                b_node=dtargs(v2=909090)
                )))).c_node().b_node(v2=55555))

    
    

if __name__ == "__main__":
    # #main()
    import sys
    sys.exit(0)
