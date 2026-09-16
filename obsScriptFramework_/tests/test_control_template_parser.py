"""
ControlTemplateParser 单元测试。
覆盖：正常解析、错误场景、层级结构、source_line 行号。
"""
import csv
from pathlib import Path

import pytest

from src.tool.scriptCsv2Json import ControlTemplateParser


# ---------- CSV 表头（与真实 widgetData.csv 保持一致的分组标记） ----------
HEADER = [
    "control_name", "widget_category", "|",
    "object_name", "description", "long_description",
    "widget_variant", "modified_callback_enabled", "modified_callback",
    "||",
    "suffix", "click_callback", "filter_str", "default_path", "group_props_name",
    "|",
    "visible", "enabled",
    "||",
    "url", "checked", "min_val", "max_val", "step", "digital",
    "info_type", "text", "label", "value", "items",
    "color_alpha", "color_red", "color_green", "color_blue",
    "font_face", "font_size", "font_style", "font_bold", "font_italic",
    "font_underline", "font_strikeout", "path_text",
    "|",
    "load_order", "props", "obj",
    "||",
    "group_props", "folding_control_obj", "folding_visible", "folding_enabled",
    "color_value", "font_data", "font_flags",
]


def _row(**kwargs):
    """按 HEADER 生成一行，未指定列填空字符串。"""
    row = [""] * len(HEADER)
    for k, v in kwargs.items():
        if k not in HEADER:
            raise KeyError(f"{k} 不在 HEADER 中")
        row[HEADER.index(k)] = v
    return row


def _write_csv(path: Path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for r in rows:
            writer.writerow(r)


def _merged(ctrl: dict) -> dict:
    """把 properties 和所有 group_properties 合并成一个大字典，方便断言。"""
    merged = dict(ctrl.get("properties", {}))
    for group_props in ctrl.get("group_properties", {}).values():
        merged.update(group_props)
    return merged


# ---------- 构造最小属性定义文件 ----------
def _make_attr_def(tmp_path: Path) -> Path:
    """定义 CHECKBOX / GROUP / DIGITALBOX 三种类型的模板行。"""
    checkbox = ["-"] + ["X"] * (len(HEADER) - 1)
    checkbox[1] = "CHECKBOX"
    checkbox[3] = "O"  # object_name 必填
    checkbox[4] = "O"  # description 必填
    checkbox[16] = "O"  # visible
    checkbox[17] = "O"  # enabled
    checkbox[20] = "O"  # checked 必填

    group = ["-"] + ["X"] * (len(HEADER) - 1)
    group[1] = "GROUP"
    group[3] = "O"
    group[4] = "O"
    group[14] = "O"     # group_props_name 必填

    digital = ["-"] + ["X"] * (len(HEADER) - 1)
    digital[1] = "DIGITALBOX"
    digital[3] = "O"
    digital[4] = "O"
    digital[21] = "O"   # min_val
    digital[22] = "O"   # max_val
    digital[23] = "O"   # step
    digital[24] = "O"   # digital

    path = tmp_path / "attr_def.csv"
    _write_csv(path, [HEADER, checkbox, group, digital])
    return path


def _make_data(tmp_path: Path, rows) -> Path:
    path = tmp_path / "data.csv"
    _write_csv(path, [HEADER] + rows)
    return path


# ---------- 正常解析 ----------
class TestParseSuccess:

    def test_minimal_checkbox(self, tmp_path):
        attr = _make_attr_def(tmp_path)
        data = _make_data(tmp_path, [
            _row(control_name="cb1", widget_category="CHECKBOX",
                 object_name="cb1", description="勾选框", checked="true"),
        ])

        parser = ControlTemplateParser()
        result = parser.parse_csv_files(str(attr), str(data), initial_props_name="props")

        assert len(result["all_controls"]) == 1
        ctrl = result["all_controls"][0]
        assert ctrl["widget_category"] == "CHECKBOX"
        assert ctrl["object_name"] == "cb1"
        assert ctrl["source_line"] == 2  # 表头第 1 行，第一条数据第 2 行

        merged = _merged(ctrl)
        assert merged["control_name"] == "cb1"
        assert merged["description"] == "勾选框"
        assert merged["checked"] is True  # 字符串 "true" 被 _parse_value 解析成 bool

    def test_group_props_name_and_hierarchy(self, tmp_path):
        attr = _make_attr_def(tmp_path)
        data = _make_data(tmp_path, [
            _row(control_name="g1", widget_category="GROUP",
                 object_name="g1", description="分组",
                 group_props_name="my_props"),
            _row(control_name="cb1", widget_category="CHECKBOX",
                 object_name="→cb1", description="子控件", checked="true"),
            _row(control_name="cb2", widget_category="CHECKBOX",
                 object_name="→cb2", description="子控件2", checked="true"),
        ])

        parser = ControlTemplateParser()
        result = parser.parse_csv_files(str(attr), str(data), initial_props_name="props")

        all_controls = result["all_controls"]
        assert len(all_controls) == 3

        g1 = all_controls[0]
        assert g1["widget_category"] == "GROUP"
        assert g1["props_name"] == "props"
        assert g1["group_props_name"] == "my_props"
        assert g1["level"] == 0

        cb1 = all_controls[1]
        assert cb1["object_name"] == "cb1"      # 解析后已去掉 → 前缀
        assert cb1["original_name"] == "→cb1"   # 原始名保留
        assert cb1["level"] == 1
        assert cb1["props_name"] == "my_props"

        cb2 = all_controls[2]
        assert cb2["object_name"] == "cb2"
        assert cb2["level"] == 1
        assert cb2["props_name"] == "my_props"

        # 树结构：1 个根节点 g1，其下有 2 个子节点
        assert len(result["tree"]) == 1
        assert len(result["tree"][0]["children"]) == 2
        child_names = [c["object_name"] for c in result["tree"][0]["children"]]
        assert child_names == ["cb1", "cb2"]

    def test_source_line_increments(self, tmp_path):
        attr = _make_attr_def(tmp_path)
        data = _make_data(tmp_path, [
            _row(control_name="a", widget_category="CHECKBOX",
                 object_name="a", description="A", checked="true"),
            _row(control_name="b", widget_category="CHECKBOX",
                 object_name="b", description="B", checked="true"),
            _row(control_name="c", widget_category="CHECKBOX",
                 object_name="c", description="C", checked="true"),
        ])

        parser = ControlTemplateParser()
        result = parser.parse_csv_files(str(attr), str(data))
        assert [c["source_line"] for c in result["all_controls"]] == [2, 3, 4]

    def test_free_properties_grouped(self, tmp_path):
        """visible / enabled / checked 应被解析到 group_properties 里。"""
        attr = _make_attr_def(tmp_path)
        data = _make_data(tmp_path, [
            _row(control_name="cb", widget_category="CHECKBOX",
                 object_name="cb", description="X",
                 checked="checked_func",
                 visible="visible_func", enabled="enabled_func"),
        ])

        parser = ControlTemplateParser()
        result = parser.parse_csv_files(str(attr), str(data))
        ctrl = result["all_controls"][0]

        # 检查这三个字段被正确分组
        # visible / enabled 在 group_3；checked 在 group_4
        assert ctrl["group_properties"]["group_3"].get("visible") == "visible_func"
        assert ctrl["group_properties"]["group_3"].get("enabled") == "enabled_func"
        assert ctrl["group_properties"]["group_4"].get("checked") == "checked_func"

        # 合并后也应有对应值
        merged = _merged(ctrl)
        assert merged["visible"] == "visible_func"
        assert merged["enabled"] == "enabled_func"
        assert merged["checked"] == "checked_func"


# ---------- 错误场景 ----------
class TestParseErrors:

    def test_empty_attr_file(self, tmp_path):
        attr = tmp_path / "empty.csv"
        attr.write_text("", encoding="utf-8")
        data = _make_data(tmp_path, [])

        with pytest.raises(ValueError, match="属性定义文件为空"):
            ControlTemplateParser().parse_csv_files(str(attr), str(data))

    def test_empty_data_file(self, tmp_path):
        attr = _make_attr_def(tmp_path)
        data = tmp_path / "empty.csv"
        data.write_text("", encoding="utf-8")

        with pytest.raises(ValueError, match="数据文件为空"):
            ControlTemplateParser().parse_csv_files(str(attr), str(data))

    def test_header_mismatch(self, tmp_path):
        attr = _make_attr_def(tmp_path)
        bad_header = HEADER.copy()
        bad_header[0] = "wrong_header"
        data = tmp_path / "bad_data.csv"
        _write_csv(data, [bad_header])

        with pytest.raises(ValueError, match="表头与属性定义文件"):
            ControlTemplateParser().parse_csv_files(str(attr), str(data))

    def test_unknown_widget_type(self, tmp_path):
        attr = _make_attr_def(tmp_path)
        data = _make_data(tmp_path, [
            _row(control_name="x", widget_category="UNKNOWN",
                 object_name="x", description="X"),
        ])

        with pytest.raises(ValueError, match="未知控件类型 'UNKNOWN'"):
            ControlTemplateParser().parse_csv_files(str(attr), str(data))

    def test_row_too_short(self, tmp_path):
        attr = _make_attr_def(tmp_path)
        data = tmp_path / "short.csv"
        _write_csv(data, [HEADER, ["a", "CHECKBOX", "|"]])

        with pytest.raises(ValueError, match="列数不足"):
            ControlTemplateParser().parse_csv_files(str(attr), str(data))

    def test_empty_object_name_after_arrow(self, tmp_path):
        attr = _make_attr_def(tmp_path)
        data = _make_data(tmp_path, [
            _row(control_name="x", widget_category="CHECKBOX",
                 object_name="→", description="X", checked="true"),
        ])

        with pytest.raises(ValueError, match="object_name 为空"):
            ControlTemplateParser().parse_csv_files(str(attr), str(data))