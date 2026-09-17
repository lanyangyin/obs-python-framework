"""variant_registry 单元测试。"""
from editor.model.variant_registry import (
    list_variants_for, default_variant_for,
)


class TestKnownCategories:

    def test_digitalbox_variants(self):
        variants = list_variants_for("DIGITALBOX")
        assert "INT" in variants
        assert "FLOAT" in variants
        assert "INT_SLIDER" in variants
        assert "FLOAT_SLIDER" in variants

    def test_textbox_variants(self):
        variants = list_variants_for("TEXTBOX")
        assert "DEFAULT" in variants
        assert "INFO" in variants
        assert "MULTILINE" in variants
        assert "PASSWORD" in variants

    def test_button_variants(self):
        variants = list_variants_for("BUTTON")
        assert "DEFAULT" in variants
        assert "URL" in variants

    def test_group_variants(self):
        variants = list_variants_for("GROUP")
        assert "NORMAL" in variants
        assert "CHECKABLE" in variants

    def test_checkbox_empty(self):
        assert list_variants_for("CHECKBOX") == []

    def test_fontbox_empty(self):
        assert list_variants_for("FONTBOX") == []


class TestUnknown:

    def test_unknown_category(self):
        assert list_variants_for("UNKNOWN_CATEGORY") == []

    def test_default_for_known(self):
        assert default_variant_for("DIGITALBOX") in list_variants_for("DIGITALBOX")

    def test_default_for_unknown(self):
        assert default_variant_for("XYZ") == ""