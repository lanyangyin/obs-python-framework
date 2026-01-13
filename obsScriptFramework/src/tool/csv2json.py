import csv
import json
import re
from typing import Dict, List, Any, Optional


class WidgetCSVParser:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.templates = {}  # 控件类型模板
        self.widgets = []  # 所有控件（扁平列表）
        self.groups = {}  # 按object_name索引的GROUP控件

    def parse(self):
        """解析CSV文件"""
        with open(self.csv_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)

        if not rows:
            raise ValueError("CSV文件为空")

        # 表头
        header = rows[0]

        # 识别列索引
        col_indices = self._analyze_columns(header, rows)

        # 解析模板行
        template_row_idx = 1  # 假设模板从第2行开始
        while template_row_idx < len(rows) and rows[template_row_idx][0] == '-':
            self._parse_template(rows[template_row_idx], col_indices)
            template_row_idx += 1

        # 跳过空行
        while template_row_idx < len(rows) and not rows[template_row_idx][0]:
            template_row_idx += 1

        # 解析数据行
        for i in range(template_row_idx, len(rows)):
            if rows[i] and rows[i][0]:
                self._parse_data_row(rows[i], col_indices)

    def _analyze_columns(self, header: List[str], rows: List[List[str]]) -> Dict[str, int]:
        """分析列结构，返回列名到索引的映射"""
        col_indices = {}

        for i, col_name in enumerate(header):
            if col_name:  # 跳过空列名
                col_indices[col_name] = i

        # 验证关键列是否存在
        required_cols = ['object_name', 'widget_category']
        for col in required_cols:
            if col not in col_indices:
                raise ValueError(f"缺少必需列: {col}")

        return col_indices

    def _parse_template(self, row: List[str], col_indices: Dict[str, int]):
        """解析模板行"""
        widget_type = row[col_indices['widget_category']]

        if not widget_type or widget_type == '-':
            return

        template = {}

        # 解析每个属性组
        for col_name, col_idx in col_indices.items():
            if col_idx < len(row):
                value = row[col_idx]
                if value == 'O':
                    template[col_name] = True  # 有这个属性
                elif value == 'X':
                    template[col_name] = False  # 没有这个属性
                elif value == '|' or value == '||':
                    template[col_name] = 'separator'  # 分隔符

        self.templates[widget_type] = template

    def _parse_data_row(self, row: List[str], col_indices: Dict[str, int]):
        """解析数据行"""
        # 解析object_name和层级
        raw_name = row[col_indices['object_name']]
        level = 0
        clean_name = raw_name

        if raw_name.startswith('→'):
            arrow_count = 0
            while arrow_count < len(raw_name) and raw_name[arrow_count] == '→':
                arrow_count += 1
            level = arrow_count
            clean_name = raw_name[arrow_count:].strip()

        widget_type = row[col_indices['widget_category']]

        # 创建控件对象
        widget = {
            'object_name': clean_name,
            'widget_category': widget_type,
            'level': level,
            'attributes': {}
        }

        # 获取该类型的模板
        template = self.templates.get(widget_type, {})

        # 解析所有属性
        for col_name, col_idx in col_indices.items():
            if col_idx >= len(row):
                continue

            value = row[col_idx]

            # 根据模板决定是否包含这个属性
            if col_name in template:
                if template[col_name] is True:  # 模板标记为O，有这个属性
                    parsed_value = self._parse_cell_value(value)
                    if parsed_value is not None:
                        widget['attributes'][col_name] = parsed_value
                # 模板标记为False或separator的属性跳过
            else:
                # 没有模板信息，但列有值
                parsed_value = self._parse_cell_value(value)
                if parsed_value is not None:
                    widget['attributes'][col_name] = parsed_value

        # 特殊处理：GROUP类型的控件
        if widget_type == 'GROUP':
            widget['children'] = []  # 只有GROUP有children
            self.groups[clean_name] = widget

        self.widgets.append(widget)

    def _parse_cell_value(self, value: str) -> Any:
        """解析单元格值，区分null和空字符串"""
        if not value:  # 空单元格
            return None

        if value == '""':  # 空字符串
            return ""

        if value.upper() == 'X':
            return None

        if value.upper() == 'O':
            return None

        # 处理带引号的字符串
        if value.startswith('"') and value.endswith('"'):
            unquoted = value[1:-1]
            # 检查是否是JSON
            if (unquoted.startswith('[') and unquoted.endswith(']')) or \
                    (unquoted.startswith('{') and unquoted.endswith('}')):
                try:
                    return json.loads(unquoted)
                except:
                    return unquoted
            return unquoted

        # 处理数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # 处理布尔值
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False

        return value

    def build_hierarchy(self) -> List[Dict]:
        """构建控件层级关系（只有GROUP可以有children）"""
        # 首先，找到所有根节点（level=0）
        root_widgets = [w for w in self.widgets if w['level'] == 0]

        # 按level分组，便于查找
        widgets_by_level = {}
        for widget in self.widgets:
            level = widget['level']
            widgets_by_level.setdefault(level, []).append(widget)

        # 构建层级关系
        for level in sorted(widgets_by_level.keys(), reverse=True):
            if level == 0:
                continue  # 根节点没有父节点

            current_widgets = widgets_by_level[level]
            parent_widgets = widgets_by_level.get(level - 1, [])

            # 为每个当前层级的控件找父GROUP
            for widget in current_widgets:
                # 查找前一个层级的GROUP作为父节点
                parent_found = False
                for parent in reversed(parent_widgets):
                    if parent['widget_category'] == 'GROUP':
                        # 添加到父GROUP的children
                        parent.setdefault('children', []).append(widget)
                        parent_found = True
                        break

                if not parent_found:
                    # 如果没有找到GROUP父节点，添加到最近的根节点
                    for root in root_widgets:
                        if root['widget_category'] == 'GROUP':
                            root.setdefault('children', []).append(widget)
                            break

        return root_widgets

    def find_parent_group(self, widget: Dict, all_widgets: List[Dict]) -> Optional[Dict]:
        """查找控件的父GROUP"""
        if widget['level'] == 0:
            return None

        # 查找上一个层级的GROUP
        target_level = widget['level'] - 1

        # 从当前widget往前找
        widget_index = all_widgets.index(widget)

        for i in range(widget_index - 1, -1, -1):
            candidate = all_widgets[i]
            if candidate['level'] == target_level and candidate['widget_category'] == 'GROUP':
                return candidate

        return None

    def export_to_json(self, output_path: str):
        """导出为JSON"""
        hierarchy = self.build_hierarchy()

        result = {
            'templates': self.templates,
            'widgets': self.widgets,  # 扁平列表
            'hierarchy': hierarchy  # 层级结构
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        stats = {
            'total_widgets': len(self.widgets),
            'by_type': {},
            'groups': len([w for w in self.widgets if w['widget_category'] == 'GROUP']),
            'max_level': max([w['level'] for w in self.widgets]) if self.widgets else 0
        }

        # 按类型统计
        for widget in self.widgets:
            widget_type = widget['widget_category']
            stats['by_type'][widget_type] = stats['by_type'].get(widget_type, 0) + 1

        return stats

    def find_widgets_by_type(self, widget_type: str) -> List[Dict]:
        """查找指定类型的控件"""
        return [w for w in self.widgets if w['widget_category'] == widget_type]

    def get_widget_tree(self, include_attributes: bool = False) -> List[Dict]:
        """获取树形结构的控件（便于显示）"""

        def build_tree_node(widget: Dict) -> Dict:
            node = {
                'name': widget['object_name'],
                'type': widget['widget_category'],
                'level': widget['level']
            }

            if include_attributes:
                node['attributes'] = widget.get('attributes', {})

            if widget['widget_category'] == 'GROUP' and 'children' in widget:
                node['children'] = [build_tree_node(child) for child in widget['children']]

            return node

        hierarchy = self.build_hierarchy()
        return [build_tree_node(widget) for widget in hierarchy]


def visualize_widget_tree(widget_tree: List[Dict], max_depth: int = 10):
    """可视化控件树"""

    def print_node(node: Dict, depth: int = 0, is_last: bool = True, prefix: str = ""):
        if depth > max_depth:
            return

        # 计算当前节点的前缀
        connector = "└── " if is_last else "├── "
        type_symbol = "📁" if node['type'] == 'GROUP' else "📄"

        print(f"{prefix}{connector}{type_symbol} {node['name']} ({node['type']})")

        # 更新前缀用于子节点
        new_prefix = prefix + ("    " if is_last else "│   ")

        # 递归打印子节点
        if node.get('children'):
            for i, child in enumerate(node['children']):
                is_last_child = i == len(node['children']) - 1
                print_node(child, depth + 1, is_last_child, new_prefix)

    print("控件层级结构:")
    print("=" * 60)

    for i, root in enumerate(widget_tree):
        is_last_root = i == len(widget_tree) - 1
        print_node(root, is_last=is_last_root)

if __name__ == '__main__':

    # 使用解析器
    parser = WidgetCSVParser("../../testData.csv")
    parser.parse()

    # 获取统计信息
    stats = parser.get_statistics()
    print("控件统计:")
    print(f"  总数: {stats['total_widgets']}")
    print(f"  GROUP数量: {stats['groups']}")
    print(f"  最大层级: {stats['max_level']}")
    print("  按类型统计:")
    for widget_type, count in stats['by_type'].items():
        print(f"    {widget_type}: {count}")

    # 获取树形结构（便于显示）
    widget_tree = parser.get_widget_tree()
    print("\n控件树结构:")
    print(json.dumps(widget_tree, ensure_ascii=False, indent=2, default=str))

    # 导出为JSON
    parser.export_to_json("widgets_hierarchy.json")
    print("\n已导出为 widgets_hierarchy.json")

    # 查找所有GROUP控件
    groups = parser.find_widgets_by_type('GROUP')
    print(f"\n找到 {len(groups)} 个GROUP控件:")
    for group in groups:
        children_count = len(group.get('children', []))
        print(f"  - {group['object_name']} (层级 {group['level']}, 子控件: {children_count})")

    # 查找test GROUP的子控件
    test_group = next((g for g in groups if g['object_name'] == 'test'), None)
    if test_group:
        print(f"\ntest GROUP的子控件:")
        for child in test_group.get('children', []):
            print(f"  - {child['object_name']} ({child['widget_category']})")


    # 可视化
    visualize_widget_tree(widget_tree)