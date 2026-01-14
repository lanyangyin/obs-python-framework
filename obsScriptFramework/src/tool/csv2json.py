import csv
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict


class ControlTemplateParser:
    def __init__(self):
        """初始化控件模板解析器"""
        self.templates = {}  # 存储每种控件的模板
        self.group_boundaries = []  # 存储分组的边界索引
        self.group_props_name_col_idx = None  # group_props_name列索引

    def parse_csv(self, csv_path: str, initial_props_name: str = "default_props") -> Dict[str, Any]:
        """
        解析CSV文件，提取模板并解析数据
        :param csv_path:
        :param initial_props_name: 默认的props名称，用于第0层控件
        :return:
        """
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

        # 找到group_props_name列的索引
        self.group_props_name_col_idx = None
        for i, header in enumerate(headers):
            if header == 'group_props_name':
                self.group_props_name_col_idx = i
                break

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

        # 解析数据并构建层次结构
        root_controls, all_controls = self._parse_data_rows_with_props(headers, data_rows, initial_props_name)

        return {
            "templates": self.templates,
            "all_controls": all_controls,
            "tree": root_controls,
            "initial_props_name": initial_props_name
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

    def _parse_data_rows_with_props(self, headers: List[str], rows: List[List[str]], initial_props_name) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        解析数据行，并处理props_name层级关系

        Returns:
            tuple: (根控件列表, 所有控件列表)
        """
        all_controls = []

        # 栈用于追踪层级和group_props_name
        # 每个栈元素: (level, props_name, node)
        stack = []
        root_controls = []

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

            # 获取group_props_name（如果有的话）
            group_props_name = None
            if self.group_props_name_col_idx is not None and self.group_props_name_col_idx < len(row):
                group_props_name_value = row[self.group_props_name_col_idx].strip()
                if group_props_name_value and group_props_name_value != 'X':
                    # 处理带引号的字符串
                    if group_props_name_value.startswith('"') and group_props_name_value.endswith('"'):
                        group_props_name = group_props_name_value[1:-1].replace('""', '"')
                    else:
                        group_props_name = group_props_name_value

            # 确定当前的props_name
            current_props_name = initial_props_name  # 默认值

            # 查找父级的group_props_name
            if stack:
                # 找到当前层级最近的父级
                for stack_level, stack_props_name, stack_node in reversed(stack):
                    if stack_level < level:
                        # 如果父级是GROUP控件，使用父级的group_props_name
                        if stack_node.get('widget_category') == 'GROUP' and stack_node.get('group_props_name'):
                            current_props_name = stack_node['group_props_name']
                        else:
                            current_props_name = stack_node.get('props_name', initial_props_name)
                        break

            # 获取模板
            if widget_type not in self.templates:
                raise TypeError(f"Warning: No template for widget type {widget_type}")
                # continue

            template = self.templates[widget_type]

            # 构建控件数据
            control = {
                "object_name": object_name,
                "original_name": original_name,
                "level": level,
                "widget_category": widget_type,
                "props_name": current_props_name,  # 添加props_name属性
                "group_props_name": group_props_name,  # 存储自身的group_props_name
                "properties": {},
                "group_properties": defaultdict(dict),
                "children": []
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

            # 添加到层级结构
            all_controls.append(control)

            # 处理层级关系
            # 弹出栈顶元素直到找到父级
            while stack and stack[-1][0] >= level:
                stack.pop()

            # 添加到父级或根节点
            if stack:
                parent_node = stack[-1][2]
                parent_node["children"].append(control)
            else:
                root_controls.append(control)

            # 将当前控件压入栈
            stack.append((level, current_props_name, control))

        return root_controls, all_controls

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

        # 字典（JSON格式）
        if value.startswith('{') and value.endswith('}'):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        # 默认返回字符串
        return value

    def export_to_json(self, data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """导出为JSON"""

        json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str

    def generate_summary_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成摘要报告"""

        all_controls = data.get('all_controls', [])

        # 统计信息
        control_count_by_type = defaultdict(int)
        props_name_groups = defaultdict(list)

        for control in all_controls:
            widget_type = control.get('widget_category', 'UNKNOWN')
            props_name = control.get('props_name', 'UNKNOWN')

            control_count_by_type[widget_type] += 1
            props_name_groups[props_name].append({
                "name": control.get('object_name'),
                "type": widget_type,
                "level": control.get('level', 0)
            })

        return {
            "total_controls": len(all_controls),
            "control_types": dict(control_count_by_type),
            "props_name_groups": {
                props_name: {
                    "count": len(controls),
                    "controls": controls[:5]  # 只显示前5个
                }
                for props_name, controls in props_name_groups.items()
            }
        }


# 使用示例
if __name__ == "__main__":
    # 使用默认的props_name
    parser = ControlTemplateParser()

    # 解析CSV文件
    csv_path = "../../testData.csv"
    result = parser.parse_csv(csv_path, initial_props_name="props")

    # 导出为JSON
    json_output = parser.export_to_json(result, "parsed_controls_with_props.json")

    # 生成摘要报告
    summary = parser.generate_summary_report(result)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


    # 打印树形结构，显示props_name
    def print_tree_with_props(nodes, indent=0):
        for node in nodes:
            prefix = "  " * indent
            level = node.get('level', 0)
            widget_type = node.get('widget_category', 'UNKNOWN')
            name = node.get('object_name', '')
            props_name = node.get('props_name', '')
            group_props_name = node.get('group_props_name', '')

            # 构建显示字符串
            display_str = f"{prefix}→" * level + f"{name} ({widget_type})"
            if props_name:
                display_str += f" [props: {props_name}]"
            if group_props_name:
                display_str += f" [group: {group_props_name}]"

            print(display_str)

            if 'children' in node and node['children']:
                print_tree_with_props(node['children'], indent + 1)


    print("\n控件树形结构（显示props_name）:")
    print_tree_with_props(result['tree'])