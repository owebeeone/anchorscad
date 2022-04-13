'''
Created on 11 Apr 2022

@author: gianni
'''
import inspect
import re

CLEANER_REGEX=re.compile('(?: *describe *\()?(?: *lambda *:)?(.*)(?: *)?[\)]')
def describe(func):
    src = inspect.getsource(func)
    mtch = CLEANER_REGEX.match(src)
    src = mtch.group(1).strip()
    try:
        print(f'{src} -> {func()}')
    except Exception as e:
        print(f'{src} -> raises {e}')


from anchorscad.datatree import datatree, Node, BindingField, dtfield, field


@datatree
class A:
    '''Demonstrates Python dataclasses default value functionality.
    Even though @datatree is used, this uses the base Python @dataclass 
    functionality.
    '''
    v1: int
    v2: int=2
    v3: int=field(default=3)
    v4: int=field(default_factory=lambda: 7 - 3)
    
describe(lambda: A())
describe(lambda: A(v1=1))


@datatree
class Anode:
    '''Injects fields from class A and provides new default for v1.'''
    v1: int=55
    a_node: Node=Node(A)

describe(lambda: Anode())
describe(lambda: Anode().a_node())
describe(lambda: Anode().a_node(v3=33))


@datatree
class Bind:
    '''Demonstrates the use of a computed default value.'''
    v1: int=1
    a_node: Node=Node(A) # Injects v2, V3 and v4.
    computed: int=BindingField(lambda s: s.v2 + s.v3)

describe(lambda: Bind(v2=10))
describe(lambda: Bind(v2=10).computed)

@datatree
class BindComputed:
    '''Demonstrates the use of a computed default value.'''
    v1: int=1
    a_node: Node=Node(A) # Injects v2 and v3.
    computed: int=BindingField(lambda s: s.v2 + s.v3)

describe(lambda: BindComputed(v2=10).computed)

def func_a(x: int=1, y:int=3):
    return x + y

@datatree
class BindFunc:
    '''Demonstrates the use of injected function parameters.'''
    a: int=1
    b: int=1
    lambda_node: Node=Node(lambda a, b: a + b)
    func_node: Node=Node(func_a)
    
describe(lambda: BindFunc())
describe(lambda: BindFunc().lambda_node())
describe(lambda: BindFunc(x=5).func_node())

@datatree
class C:
    a_v1: int=11
    a_node: Node=field(default=Node(A, prefix='a_'), repr=False)
    b_v1: int=12
    b_node: Node=field(default=Node(A, prefix='b_'), repr=False)
    computed: int=BindingField(lambda s: s.a_v2 + s.b_v2)
    
    def __post_init__(self):
        pass # Called after initialization is complete.
        
    def make_stuff(self):
        return self.a_node(v2=22), self.b_node(), self.computed

describe(lambda: C())
describe(lambda: C(b_v2=44).computed)
describe(lambda: C().a_node())
describe(lambda: C(b_v2=22).b_node(v3=33))


@datatree
class D:
    v1: int=111
    v2: int=None
    a_node: Node=dtfield(
        Node(A, 'v1'), repr=False, init=False)

describe(lambda: D())
describe(lambda: D().a_node())

    
@datatree
class E:
    v1: int=1
    v2: int=2
    v_computed: Node=dtfield(
        self_default=lambda s: s.v1 + s.v2)

describe(lambda: E())
describe(lambda: E(v_computed=55))
    

if __name__ == "__main__":
    pass #main()
