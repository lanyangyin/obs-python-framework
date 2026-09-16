"""工具模块测试：parseColor / addAliases / addClearCache。"""
from functools import lru_cache

from plugins.tool.parseColor import parse_color_value, int_to_color_str
from plugins.tool.addAliases import add_aliases, AliasMeta
from plugins.tool.addClearCache import add_clear_cache, ClearableCache


class TestParseColor:

    def test_parse_with_alpha(self):
        # 0xAARRGGBB
        value = 0x80FF8040
        r, g, b, a = parse_color_value(value, has_alpha=True)
        assert r == 0x40
        assert g == 0x80
        assert b == 0xFF
        assert a == 0x80

    def test_parse_without_alpha(self):
        value = 0x00FF8040
        r, g, b, a = parse_color_value(value, has_alpha=False)
        assert r == 0x40
        assert g == 0x80
        assert b == 0xFF
        assert a == 0xFF


class TestIntToColorStr:

    def test_basic(self):
        value = 0x80FF8040
        # 注意 int_to_color_str 的实现里 red/green/blue 的移位顺序
        # 0x80FF8040 -> alpha=0x80, red=0xFF, green=0x80, blue=0x40
        assert int_to_color_str(value) == "#FF8040 80"


class TestAddAliases:

    def test_alias_instance_method(self):
        class A(metaclass=AliasMeta):
            def __init__(self, n):
                self.n = n

            @add_aliases("alias1", "alias2")
            def original(self):
                return self.n

        a = A(42)
        assert a.original() == 42
        assert a.alias1() == 42
        assert a.alias2() == 42

    def test_alias_staticmethod(self):
        class B(metaclass=AliasMeta):
            @staticmethod
            @add_aliases("s_alias")
            def s_original():
                return "s"

        assert B.s_original() == "s"
        assert B.s_alias() == "s"


class TestAddClearCache:

    def test_clear_works(self):
        call_count = {"n": 0}

        class C(ClearableCache):
            @staticmethod
            @lru_cache(maxsize=None)
            @add_clear_cache
            def compute(x):
                call_count["n"] += 1
                return x * 2

        assert C.compute(5) == 10
        assert C.compute(5) == 10
        assert call_count["n"] == 1  # 第二次命中缓存

        C.clear()
        assert C.compute(5) == 10
        assert call_count["n"] == 2  # 清理后重新计算