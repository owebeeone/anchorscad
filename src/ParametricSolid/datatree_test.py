'''
Created on 8 Dec 2021

@author: gianni
'''

import unittest
from ParametricSolid.datatree import datatree, dtargs, override, Node
from dataclasses import dataclass, field

@datatree
class LeafType1():
    
    leaf_a: float=1
    leaf_b: float=2
    
@datatree
class LeafType2():
    
    leaf_a: float=10
    leaf_b: float=20

@datatree
class LeafType3():
    
    leaf_a: float=11
    leaf_b: float=22
    
@datatree
class LeafType4():
    
    leaf_a: float=111
    leaf_b: float=222
    
# Check for support of non dataclass/datatree types.
class LeafType5():
    
    def __init__(self, a=1111, b=2222):
        self.a = a
        self.b = b
        
    def __eq__(self, other):
        if isinstance(other, LeafType5):
            return self.a == other.a and self.b == other.b
        return False

@datatree
class Overridable:
    
    leaf_a: float=53  # Overrides the default value for all classes.
    
    # Only the nominated fields are mapped and leaf1_b
    leaf1: Node=Node(LeafType1, 'leaf_a', {'leaf_b': 'leaf1_b'})
    leaf1a: Node=Node(LeafType1, 'leaf_a', {'leaf_b': 'leaf1a_b'})
   
    leaf2: Node=Node(LeafType2) # All fields are mapped.
    leaf3: Node=Node(LeafType3, {}) # No fields are mapped.
    leaf4: Node=Node(LeafType4, use_defaults=False) # Default values are mapped from this.
    leaf5: Node=Node(LeafType5)
    
    def __post_init__(self):
        
        self.l1 = self.leaf1(leaf_a=99)
        self.l1a = self.leaf1a()
        self.l2 = self.leaf2()
        self.l3 = self.leaf3()
        self.l4 = self.leaf4()
        self.l5 = self.leaf5(b=3333)
        

OVERRIDER1=Overridable(
    leaf_a=3, 
    leaf1_b=44,
    override=override(
        leaf1=dtargs(leaf_b=7)),
    )

class Test(unittest.TestCase):

    def test_l1(self):
        self.assertEqual(OVERRIDER1.l1, LeafType1(leaf_a=99, leaf_b=7))
        
    def test_l1a(self):
        self.assertEqual(OVERRIDER1.l1a, LeafType1(leaf_a=3, leaf_b=2))
        
    def test_l2(self):
        self.assertEqual(OVERRIDER1.l2, LeafType2(leaf_a=3, leaf_b=20))
        
    def test_l3(self):
        self.assertEqual(OVERRIDER1.l3, LeafType3(leaf_a=11, leaf_b=22))
        
    def test_l4(self):
        self.assertEqual(OVERRIDER1.l4, LeafType4(leaf_a=3, leaf_b=20))
        
    def test_l5(self):
        self.assertEqual(OVERRIDER1.l5, LeafType5(a=1111, b=3333))
        
    def test_inherits(self):
        
        @dataclass
        class A:
            a: int = 1
            
        @datatree
        class B(A):
            b: int = 2
            
        ab = B(10, 20)
        self.assertEqual(ab.a, 10)
        self.assertEqual(ab.b, 20)
        
    def test_name_map(self):
        
        @datatree
        class A:
            anode: Node=Node(LeafType1, {'leaf_a': 'aa'}, expose_all=True)
            
            def __post_init__(self):
                self.lt1 = self.anode()
            
        ao = A()
        self.assertEqual(ao.lt1, LeafType1())
        self.assertEqual(ao.aa, LeafType1().leaf_a)
        self.assertEqual(ao.leaf_b, LeafType1().leaf_b)
        
    def test_ignore_default_bad(self):
        
        try:
            @datatree
            class A:
                anode: Node=Node(LeafType1, use_defaults=False)
            self.fail("Expected field order issue.")
        except TypeError:
            pass
        
    def test_additive_default(self):
        @datatree
        class A:
            anode: Node=Node(LeafType1)
            leaf_a: float=51
            leaf_b: float
            
        lt1 = A().anode()
        
        self.assertEqual(lt1, LeafType1(51, 2))
      
    def test_inheritance(self):
        
        @datatree
        class A():
            a: float=1
            leaf: Node=Node(LeafType2)
            s: list=field(default_factory=lambda : list())
            
            def __post_init__(self):
                self.s.append('A')
                
        
        @datatree
        class B(A):
            b: float=1
            leaf: Node=Node(LeafType2)
            s: list=field(default_factory=lambda : list())
            
            def __post_init__(self):
                self.s.append('B')
                
        self.assertEqual(B().s, ['A', 'B'])
        self.assertEqual(B().leaf(), LeafType2(leaf_a=10, leaf_b=20, override=None))
      
    def test_multiple_inheritance(self):
        
        @datatree
        class A1():
            a1: float=1
            s: list=field(default_factory=lambda : list())
            
            def __post_init__(self):
                self.s.append('A1')
                  
        @datatree
        class A2():
            a2: float=1
            leaf: Node=Node(LeafType2)
            s: list=field(default_factory=lambda : list())
            
            def __post_init__(self):
                self.s.append('A2')
                
        @datatree
        class B(A1, A2):
            b: float=1
            s: list=field(default_factory=lambda : list())
            
            def __post_init__(self):
                self.s.append('B')
                
        self.assertEqual(B().s, ['A1', 'A2', 'B'])
        self.assertEqual(B().leaf(), LeafType2(leaf_a=10, leaf_b=20, override=None))
        
    def test_multiple_inheritance_mix_dataclass_datatree(self):
        
        @datatree
        class A1():
            a1: float=1
            leaf: Node=Node(LeafType2)
            s: list=field(default_factory=lambda : list())
            
            def __post_init__(self):
                self.s.append('A1')
                  
        @dataclass
        class A2():
            a2: float=1
            s: list=field(default_factory=lambda : list())
            
            def __post_init__(self):
                self.s.append('A2')

        @datatree
        class B(A1, A2):
            b: float=1
            s: list=field(default_factory=lambda : list())
            
            def __post_init__(self):
                self.s.append('B')
                
        self.assertEqual(B().s, ['A1', 'A2', 'B'])
        self.assertEqual(B().leaf(), LeafType2(leaf_a=10, leaf_b=20, override=None))
        
       
    def test_multiple_inheritance_mix_dataclass_datatree_no_pi(self):
        
        @datatree
        class A1():
            a1: float=1
            leaf: Node=Node(LeafType2)
            s: list=field(default_factory=lambda : list())
            
            def __post_init__(self):
                self.s.append('A1')
                  
        @dataclass
        class A2():
            a2: float=1
            s: list=field(default_factory=lambda : list())
            
            def __post_init__(self):
                self.s.append('A2')

        @datatree
        class B(A1, A2):
            b: float=1
            s: list=field(default_factory=lambda : list())
            
        @datatree
        class C(B):
            b: float=1
            
            def __post_init__(self):
                self.s.append('C')
                
        self.assertEqual(C().s, ['A1', 'A2', 'C'])
        self.assertEqual(C().leaf(), LeafType2(leaf_a=10, leaf_b=20, override=None))
    
    def test_function(self):
        al = []
        bl = []
        def func(a:set='a', b:str='b'):
            al.append(a)
            bl.append(b)
            
        @datatree
        class A:
            b: str='clzA-b'
            funcNode: Node=Node(func)
            
        A().funcNode()
        self.assertEqual(al, ['a'])
        self.assertEqual(bl, ['clzA-b'])
        
    def test_prefix_node(self):
        al = []
        bl = []
        def func(a:set='a', b:str='b'):
            al.append(a)
            bl.append(b)
            
        @datatree
        class A:
            fb: str='clzA-b'
            funcNode: Node=Node(func, prefix='f')
            
        A().funcNode()
        self.assertEqual(al, ['a'])
        self.assertEqual(bl, ['clzA-b'])
        
        
    def test_nested_node(self):
        
        @datatree
        class A():
            a1: float=1
            leaf: Node=Node(LeafType2)
            s: list=field(default_factory=lambda : list())
            
            def __post_init__(self):
                self.s.append('A')

        @datatree
        class B():
            node_A: Node=Node(A)
            
            def __post_init__(self):
                self.s.append('B')    

        @datatree
        class C():
            node_B: Node=Node(B)
            
            def __post_init__(self):
                self.s.append('C')   
                
        c = C()
        self.assertEqual(c.leaf(), LeafType2(leaf_a=10, leaf_b=20, override=None))
        self.assertEqual(c.s, ['C'])
        c.node_B()
        self.assertEqual(c.s, ['C', 'B'])
        c.node_A()
        self.assertEqual(c.s, ['C', 'B', 'A'])
        
    def test_preserve(self):
        
        @datatree
        class A:
            a: int=1
            b: int=2
            keep1: int=3
            keep2: int=4
        
        # Names keep1 and keep2 are preserved.
        @datatree
        class B:
            nodeA: Node=Node(
                A, prefix='aa_', preserve={'keep1', 'keep2'})
            a_obj: A=None
            
            def __post_init__(self):
                self.a_obj = self.nodeA()
        
        self.assertEqual(B(), B(aa_a=1, aa_b=2, keep1=3, keep2=4))
    
    def test_if_avail(self):
        
        @datatree
        class A:
            a: int=1
            b: int=2
            keep1: int=3
            keep2: int=4
        
        # Name keep1 is exposed even if not specified.
        @datatree
        class B:
            nodeA: Node=Node(
                A, 'a', {'b': 'bb'}, prefix='aa_', 
                expose_if_avail={'keep1', 'NotThere'})
            a_obj: A=None
            
            def __post_init__(self):
                self.a_obj = self.nodeA()
        
        self.assertEqual(B(), B(aa_a=11, bb=44, aa_keep1=33))
        self.assertEqual(A(a=11, b=11, keep1=33), 
                         B(aa_a=11, bb=44, aa_keep1=33).a_obj)
        self.assertFalse(hasattr(B(), 'aa_b'))
        self.assertFalse(hasattr(B(), 'aa_keep2'))
        
    def test_exposed_node(self):
        s = []
        def f(a: int=3):
            s.append(a)
        
        @datatree
        class A:
            a: int=1
            f_node: Node=Node(f)
            
            def thing(self):
                self.f_node()
        
        @datatree
        class B:
            nodeA: Node=Node(A, 'f_node')
            a_obj: A=None
            
            def __post_init__(self):
                self.a_obj = self.nodeA()
                
        b = B()
        b.a_obj.f_node()
        self.assertEqual(b.a_obj, A(a=1))
        
        b.f_node(a=4)
        self.assertEqual(s, [1, 4])
        
    
    def test_exposed_node_different_names(self):
        s = []
        def f(a: int=3):
            s.append(a)
        
        @datatree
        class A:
            a: int=1
            f_node: Node=Node(f)
            
            def thing(self):
                self.f_node()
        
        @datatree
        class B:
            nodeA: Node=Node(A, 'f_node', {'a': 'a1'}, expose_all=True)
            a_obj: A=None
            
            def __post_init__(self):
                self.a_obj = self.nodeA()
                
        b = B()
        b.a_obj.f_node()
        self.assertEqual(b.a_obj, A(a=1))
        
        b.f_node(a=b.a1)  # TODO: Use mapping to automatically find a in b.
        self.assertEqual(s, [1, 1])
        
    
    def test_other_bound_nodes(self):
        s1 = []
        def f1(a: int=3):
            s1.append(a)
            
        s2 = []
        def f2(a: int=3):
            s2.append(a)
        
        @datatree
        class A:
            a: int=1
            f1_node: Node=Node(f1)
            
            def thing(self):
                self.f1_node()
        
        A().thing()
        self.assertEqual(s1, [1])  
        self.assertEqual(s2, [])  
        
        # If neither a Node or a BoundNode is passed a a node, it is just called.
        A(f1_node=f2).thing()
        self.assertEqual(s1, [1])  
        self.assertEqual(s2, [3]) 


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_exposed_node_different_names']
    unittest.main()
