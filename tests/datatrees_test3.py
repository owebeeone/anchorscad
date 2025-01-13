'''
Created on 2024-01-20

@author: gianni
'''

import unittest

from frozendict import frozendict
from datatrees import datatree, Node
from dataclasses import InitVar, field


class TestInitVar(unittest.TestCase):
    def test_basic_initvar(self):
        """Test basic InitVar functionality"""

        @datatree
        class A:
            init_param: InitVar[str] = None
            value: str = ''

            def __post_init__(self, init_param):
                if init_param:
                    self.value = f"Initialized with {init_param}"

        a = A(init_param="test")
        self.assertEqual(a.value, "Initialized with test")

        # Test with default None
        a2 = A()
        self.assertEqual(a2.value, "")

    def test_multiple_initvars_single_class(self):
        """Test multiple InitVars in a single class"""

        @datatree
        class Config:
            name: InitVar[str] = None
            value: InitVar[int] = None
            description: str = ''
            total: int = 0

            def __post_init__(self, name, value):
                if name:
                    self.description = f"Name: {name}"
                if value:
                    self.total = value * 2

        c = Config(name="test", value=10)
        self.assertEqual(c.description, "Name: test")
        self.assertEqual(c.total, 20)

    def test_initvar_with_field_options(self):
        """Test InitVar with field options"""

        @datatree
        class Settings:
            debug: InitVar[bool] = field(default=False, repr=False)
            verbose: InitVar[bool] = field(default=True, repr=False)
            log_level: str = 'INFO'

            def __post_init__(self, debug, verbose):
                if debug:
                    self.log_level = 'DEBUG'
                elif not verbose:
                    self.log_level = 'ERROR'

        s1 = Settings(debug=True)
        self.assertEqual(s1.log_level, 'DEBUG')

        s2 = Settings(verbose=False)
        self.assertEqual(s2.log_level, 'ERROR')

    def test_deep_inheritance_chain(self):
        """Test InitVars through a deep inheritance chain"""

        @datatree(chain_post_init=True)
        class Base:
            base_init: InitVar[str] = None
            base_value: str = ''

            def __post_init__(self, base_init):
                if base_init:
                    self.base_value = f"Base: {base_init}"

        @datatree(chain_post_init=True)
        class Middle(Base):
            middle_init: InitVar[str] = None
            middle_value: str = ''

            def __post_init__(self, base_init, middle_init):
                if middle_init:
                    self.middle_value = f"Middle: {middle_init}"

        @datatree(chain_post_init=True)
        class Derived(Middle):
            derived_init: InitVar[str] = None
            derived_value: str = ''

            def __post_init__(self, base_init, middle_init, derived_init):
                if derived_init:
                    self.derived_value = f"Derived: {derived_init}"

        d = Derived(base_init="base", middle_init="middle", derived_init="derived")

        self.assertEqual(d.base_value, "Base: base")
        self.assertEqual(d.middle_value, "Middle: middle")
        self.assertEqual(d.derived_value, "Derived: derived")

    def test_initvar_with_node_chain(self):
        """Test InitVars with chained Node fields"""

        @datatree
        class Inner:
            setup: InitVar[dict] = None
            config: dict = field(default_factory=dict)

            def __post_init__(self, setup):
                if setup:
                    self.config.update(setup)

        @datatree
        class Middle:
            inner_node: Node = Node(Inner, 'setup')
            settings: InitVar[dict] = None

            def __post_init__(self, settings):
                self.inner = self.inner_node(setup=settings)

        @datatree
        class Outer:
            middle_node: Node = Node(Middle, 'settings')
            config: InitVar[dict] = None

            def __post_init__(self, config):
                self.middle = self.middle_node(settings=config)

        test_config = {'key': 'value'}
        o = Outer(config=test_config)
        self.assertEqual(o.middle.inner.config, test_config)

    def test_initvar_with_default_factory(self):
        """Test InitVar with default_factory"""

        def get_default_config():
            return {'default': 'config'}

        @datatree
        class ConfigHolder:
            config: InitVar[dict] = frozendict({'default': 'config'})
            settings: dict = field(default_factory=dict)

            def __post_init__(self, config):
                self.settings.update(config)

        c1 = ConfigHolder()
        self.assertEqual(c1.settings, {'default': 'config'})

        c2 = ConfigHolder({'custom': 'value'})
        self.assertEqual(c2.settings, {'custom': 'value'})

    def test_initvar_with_node_injection(self):
        """Test InitVar being injected through Node with different prefixes"""

        @datatree
        class Config:
            init_param: InitVar[str] = None
            other_param: InitVar[int] = 0
            value: str = ''

            def __post_init__(self, init_param, other_param):
                if init_param:
                    self.value = f"{init_param}-{other_param}"

        @datatree
        class Wrapper:
            config_node: Node = Node(Config, 'init_param', {'other_param': 'count'}, prefix='cfg_')
            cfg_init_param: str = "default"
            count: int = 42

            def __post_init__(self):
                self.config = self.config_node()

        w = Wrapper(cfg_init_param="test", count=10)
        self.assertEqual(w.config.value, "test-10")

    def test_initvar_with_multiple_nodes(self):
        """Test multiple Nodes with InitVar fields"""

        @datatree
        class Base:
            setup: InitVar[str] = None
            name: str = ''

            def __post_init__(self, setup):
                if setup:
                    self.name = f"Base-{setup}"

        @datatree
        class Extension:
            init: InitVar[str] = None
            value: str = ''

            def __post_init__(self, init):
                if init:
                    self.value = f"Ext-{init}"

        @datatree
        class Container:
            base_node: Node = Node(Base, 'setup')
            ext_node: Node = Node(Extension, {'init': 'setup'})
            setup: str = "default"

            def __post_init__(self):
                self.base = self.base_node()
                self.ext = self.ext_node()

        c = Container(setup="test")
        self.assertEqual(c.base.name, "Base-test")
        self.assertEqual(c.ext.value, "Ext-test")

    def test_initvar_with_frozen(self):
        """Test InitVar with frozen dataclass"""

        @datatree(frozen=True)
        class FrozenConfig:
            init_param: InitVar[str] = None
            value: str = ''

            def __post_init__(self, init_param):
                # Need to use object.__setattr__ for frozen classes
                if init_param:
                    object.__setattr__(self, 'value', f"Frozen-{init_param}")

        f = FrozenConfig(init_param="test")
        self.assertEqual(f.value, "Frozen-test")


if __name__ == "__main__":
    unittest.main()
