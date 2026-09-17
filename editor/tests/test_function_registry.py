"""function_registry 单元测试。"""
from editor.model.function_registry import (
    list_control_functions,
    list_button_functions,
    list_all_function_names,
)


class TestListing:

    def test_list_control_functions_returns_list(self):
        result = list_control_functions()
        assert isinstance(result, list)
        # 插件可导入时应该返回非空
        assert all(isinstance(n, str) for n in result)

    def test_list_button_functions_returns_list(self):
        result = list_button_functions()
        assert isinstance(result, list)
        assert all(isinstance(n, str) for n in result)

    def test_no_private_names(self):
        for name in list_all_function_names():
            assert not name.startswith("_"), f"私有方法泄露: {name}"

    def test_merged_deduplicated(self):
        combined = list_all_function_names()
        assert combined == sorted(set(combined))


class TestResilience:

    def test_import_failure_returns_empty(self, monkeypatch):
        """即使 plugins 不可导入，也只返回空列表，不抛异常。"""
        import builtins
        original_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name.startswith("plugins."):
                raise ImportError("simulated")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        assert list_control_functions() == []
        assert list_button_functions() == []