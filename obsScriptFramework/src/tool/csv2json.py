import csv
import json
import os
from csv import excel
from typing import Dict, List, Any, Optional
from collections import defaultdict


class ControlTemplateParser:
    def __init__(self):
        self.templates = {}  # 存储每种控件的模板
        self.group_boundaries = []  # 存储分组的边界索引

    def parse_csv(self, csv_path: str) -> Dict[str, Any]:
        """解析CSV文件，提取模板并解析数据"""

        # 读取CSV文件
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            return {"error": "Empty CSV file"}

        # 解析列标题
        headers = rows[0]

        # 检测分组边界
        self._detect_group_boundaries(headers)

        # 解析模板行
        template_rows = []
        for row in rows[1:]:
            if not any(row):  # 空行，模板部分结束
                break
            if row[0] == '-':  # 模板行
                template_rows.append(row)

        # 构建模板
        self._build_templates(headers, template_rows)

        # 解析数据行（从模板行之后开始）
        data_start_idx = len(template_rows) + 2  # 跳过标题和模板行
        data_rows = rows[data_start_idx:]

        # 解析数据
        controls = self._parse_data_rows(headers, data_rows)

        # 构建层次结构
        tree = self._build_hierarchy(controls)

        return {
            "templates": self.templates,
            "controls": controls,
            "tree": tree
        }

    def _detect_group_boundaries(self, headers: List[str]) -> None:
        """检测分组边界"""
        boundaries = [0]  # 从第一列开始

        for i, header in enumerate(headers):
            if header == '|':
                boundaries.append(i + 1)  # 下一个分组开始
            elif header == '||':
                boundaries.append(i)  # 二级分组，不从||开始

        boundaries.append(len(headers))  # 结束边界
        self.group_boundaries = boundaries

    def _build_templates(self, headers: List[str], template_rows: List[List[str]]) -> None:
        """构建控件模板"""

        for row in template_rows:
            widget_type = row[1]  # widget_category

            # 初始化模板
            template = {
                "required_fields": [],
                "optional_fields": [],
                "field_info": {}  # 存储每个字段的详细信息
            }

            # 解析每个字段
            for i, (header, value) in enumerate(zip(headers, row)):
                if not header or header in ['|', '||']:
                    continue

                if value == 'O':
                    template["required_fields"].append(header)
                elif value == 'X':
                    continue  # 不包含在模板中

                # 存储字段在哪个分组
                group_idx = self._find_group_index(i)
                template["field_info"][header] = {
                    "group": group_idx,
                    "index": i,
                    "required": value == 'O'
                }

            self.templates[widget_type] = template

    def _find_group_index(self, col_index: int) -> int:
        """查找列属于哪个分组"""
        for i in range(len(self.group_boundaries) - 1):
            start = self.group_boundaries[i]
            end = self.group_boundaries[i + 1]
            if start <= col_index < end:
                return i
        return -1

    def _parse_data_rows(self, headers: List[str], rows: List[List[str]]) -> List[Dict[str, Any]]:
        """解析数据行"""
        controls = []

        for row in rows:
            if not any(row):  # 跳过空行
                continue

            object_name = row[0].strip()
            widget_type = row[1]  # widget_category

            # 计算缩进级别
            level = 0
            original_name = object_name
            while object_name.startswith('→'):
                level += 1
                object_name = object_name[1:]

            # 获取模板
            if widget_type not in self.templates:
                raise TypeError(f"Warning: No template for widget type {widget_type}")
                continue

            template = self.templates[widget_type]

            # 构建控件数据
            control = {
                "object_name": object_name,
                "original_name": original_name,
                "level": level,
                "widget_category": widget_type,
                "properties": {},
                "group_properties": defaultdict(dict)
            }

            # 根据模板解析属性
            for header, info in template["field_info"].items():
                col_index = info["index"]
                if col_index >= len(row):
                    continue

                value = row[col_index].strip()

                # 处理特殊值
                if value == 'X':
                    continue  # 跳过不需要的属性

                # 处理空值和空字符串
                if not value:
                    processed_value = None  # 空单元格为 null
                elif value.startswith('"') and value.endswith('"'):
                    # 处理带引号的字符串
                    processed_value = value[1:-1].replace('""', '"')
                else:
                    # 尝试解析其他类型
                    processed_value = self._parse_value(value)

                # 根据分组存储属性
                group_idx = info["group"]
                if group_idx == 0:  # 基本属性组
                    control["properties"][header] = processed_value
                else:
                    group_key = f"group_{group_idx}"
                    control["group_properties"][group_key][header] = processed_value

            controls.append(control)

        return controls

    def _parse_value(self, value: str) -> Any:
        """解析字符串值为合适的数据类型"""

        if not value or value == 'null':
            return None

        # 布尔值
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'

        # 数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # 十六进制颜色值
        if value.startswith('0x'):
            try:
                return int(value, 16)
            except ValueError:
                pass

        # 数组（JSON格式）
        if value.startswith('[') and value.endswith(']'):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        # 默认返回字符串
        return value

    def _build_hierarchy(self, controls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """根据缩进级别构建层次结构"""

        if not controls:
            return []

        # 按原始顺序构建树
        root_controls = []
        stack = []  # 用于追踪父节点

        for control in controls:
            level = control["level"]

            # 调整栈以匹配当前层级
            while len(stack) > level:
                stack.pop()

            # 设置父节点
            if stack:
                parent = stack[-1]
                if "children" not in parent:
                    parent["children"] = []
                parent["children"].append(control)
            else:
                root_controls.append(control)

            # 如果有子节点，压入栈
            if "children" not in control:
                control["children"] = []
            stack.append(control)

        return root_controls

    def export_to_json(self, data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """导出为JSON"""

        json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str


# 使用示例
if __name__ == "__main__":
    parser = ControlTemplateParser()

    # 解析CSV文件
    csv_path = "../../testData.csv"
    result = parser.parse_csv(csv_path)

    # 导出为JSON
    json_output = parser.export_to_json(result, "parsed_controls.json")

    # 打印摘要信息
    print("=" * 60)
    print(f"解析完成！")
    print(f"找到 {len(result['templates'])} 种控件模板:")
    for widget_type in result['templates'].keys():
        print(f"  - {widget_type}")

    print(f"\n解析了 {len(result['controls'])} 个控件")
    print(f"构建了 {len(result['tree'])} 个根节点")


    # 打印树形结构
    def print_tree(nodes, indent=0):
        for node in nodes:
            prefix = "  " * indent
            level = node.get('level', 0)
            widget_type = node.get('widget_category', 'UNKNOWN')
            name = node.get('object_name', '')
            print(f"{prefix}→" * level + f"{name} ({widget_type})")

            if 'children' in node and node['children']:
                print_tree(node['children'], indent + 1)


    print("\n控件树形结构:")
    print_tree(result['tree'])

    print("\n完整JSON已保存到 parsed_controls.json")