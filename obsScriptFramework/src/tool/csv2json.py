import csv
import json
import re
from typing import Dict, List, Any, Optional


def parse_test_csv(csv_file_path: str) -> Dict[str, Any]:
    """
    解析带有层级箭头和嵌套JSON的测试CSV文件

    输入示例：
    object_name,widget_category,customizable_attr,innate_attribute,derived_attribute
    top,BUTTON,{"visible": true},...
    →test,BUTTON,{"visible": true},...
    →→test,COMBOBOX,{"visible": true},...
    """

    nodes = []

    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            # 处理每一行数据
            obj_name = row['object_name']

            # 解析层级深度
            level = 0
            clean_name = obj_name

            # 统计箭头数量
            while clean_name.startswith('→'):
                level += 1
                clean_name = clean_name[1:]  # 移除一个箭头

            # 清理名称（移除可能的前导空格）
            clean_name = clean_name.strip()

            # 解析JSON属性
            try:
                customizable_attr = json.loads(row['customizable_attr'].replace('""', '"'))
            except:
                customizable_attr = {"error": "Failed to parse customizable_attr"}

            try:
                innate_attribute = json.loads(row['innate_attribute'].replace('""', '"'))
            except:
                innate_attribute = {"error": "Failed to parse innate_attribute"}

            try:
                derived_attribute = json.loads(row['derived_attribute'].replace('""', '"'))
            except:
                derived_attribute = {"error": "Failed to parse derived_attribute"}

            # 处理颜色值（将十六进制字符串转换为整数）
            if 'customizable_attr' in row:
                # 查找并转换所有0xFF格式的颜色值
                attr_str = row['customizable_attr']
                color_matches = re.findall(r'"0x[0-9A-Fa-f]+"', attr_str)
                for match in color_matches:
                    hex_str = match[1:-1]  # 去掉引号
                    try:
                        int_value = int(hex_str, 16)
                        # 更新customizable_attr字典
                        key = None
                        if 'color_alpha' in attr_str and hex_str in attr_str:
                            key = 'color_alpha'
                        elif 'color_red' in attr_str and hex_str in attr_str:
                            key = 'color_red'
                        elif 'color_green' in attr_str and hex_str in attr_str:
                            key = 'color_green'
                        elif 'color_blue' in attr_str and hex_str in attr_str:
                            key = 'color_blue'

                        if key and key in customizable_attr:
                            customizable_attr[key] = int_value
                    except:
                        pass

            # 创建节点
            node = {
                'level': level,
                'object_name': clean_name,
                'widget_category': row['widget_category'],
                'customizable_attr': customizable_attr,
                'innate_attribute': innate_attribute,
                'derived_attribute': derived_attribute,
                'children': [],
                'line_number': i + 1,  # 记录行号便于调试
                'original_name': obj_name  # 保留原始名称用于调试
            }

            nodes.append(node)

    # 构建树形结构
    if not nodes:
        return {}

    # 使用栈来构建树
    root = {
        'object_name': 'ROOT',
        'widget_category': 'ROOT',
        'children': [],
        'customizable_attr': {},
        'innate_attribute': {},
        'derived_attribute': {}
    }

    stack = [(root, -1)]  # (父节点, 层级)

    for node in nodes:
        current_level = node['level']

        # 弹出栈顶元素直到找到合适的父节点
        while stack and stack[-1][1] >= current_level:
            stack.pop()

        # 添加当前节点到父节点的children
        parent_node, _ = stack[-1]
        parent_node['children'].append(node)

        # 如果当前节点可能有子节点，将其压入栈
        if node['widget_category'] in ['GROUP', 'ROOT']:
            stack.append((node, current_level))

    return root


def convert_csv_to_json_tree(csv_file_path: str, output_json_path: Optional[str] = None) -> Dict[str, Any]:
    """
    将测试CSV转换为JSON树并可选保存到文件
    """
    try:
        tree = parse_test_csv(csv_file_path)

        if output_json_path:
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(tree, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON树已保存到 {output_json_path}")

        return tree

    except Exception as e:
        print(f"❌ 解析失败: {str(e)}")
        raise


def analyze_test_data(tree: Dict[str, Any]):
    """分析测试数据的统计信息"""

    stats = {
        'total_nodes': 0,
        'by_category': {},
        'by_level': {},
        'widget_types': set(),
        'color_widgets': [],
        'groups': [],
        'buttons': []
    }

    def traverse(node, level=0):
        if 'object_name' in node and node['object_name'] != 'ROOT':
            stats['total_nodes'] += 1

            # 按类别统计
            category = node.get('widget_category', 'UNKNOWN')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

            # 按层级统计
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1

            # 收集widget类型
            if 'innate_attribute' in node:
                variant = node['innate_attribute'].get('widget_variant', '')
                if variant:
                    stats['widget_types'].add(variant)

            # 收集颜色控件
            if node.get('widget_category') == 'COLORBOX':
                stats['color_widgets'].append({
                    'name': node['object_name'],
                    'control_name': node['innate_attribute'].get('control_name', ''),
                    'customizable_attr': node['customizable_attr']
                })

            # 收集分组
            if node.get('widget_category') == 'GROUP':
                stats['groups'].append({
                    'name': node['object_name'],
                    'control_name': node['innate_attribute'].get('control_name', ''),
                    'children_count': len(node.get('children', []))
                })

            # 收集按钮
            if node.get('widget_category') == 'BUTTON':
                stats['buttons'].append({
                    'name': node['object_name'],
                    'control_name': node['innate_attribute'].get('control_name', '')
                })

        # 递归遍历子节点
        for child in node.get('children', []):
            traverse(child, level + 1)

    traverse(tree)

    # 转换set为list以便JSON序列化
    stats['widget_types'] = list(stats['widget_types'])

    return stats


def extract_color_values(tree: Dict[str, Any]) -> List[Dict[str, Any]]:
    """提取所有颜色值并转换为可读格式"""

    color_values = []

    def traverse(node):
        if node.get('widget_category') == 'COLORBOX':
            custom_attrs = node.get('customizable_attr', {})

            # 检查是否有颜色值
            if any(key.startswith('color_') for key in custom_attrs):
                color_dict = {
                    'object_name': node['object_name'],
                    'control_name': node.get('innate_attribute', {}).get('control_name', ''),
                    'rgba': {}
                }

                # 提取RGBA值
                for channel in ['alpha', 'red', 'green', 'blue']:
                    key = f'color_{channel}'
                    if key in custom_attrs:
                        value = custom_attrs[key]
                        if isinstance(value, str) and value.startswith('0x'):
                            try:
                                value = int(value, 16)
                            except:
                                pass
                        color_dict['rgba'][channel[0].upper()] = value

                # 计算十六进制表示
                if all(ch in color_dict['rgba'] for ch in ['A', 'R', 'G', 'B']):
                    a = color_dict['rgba']['A']
                    r = color_dict['rgba']['R']
                    g = color_dict['rgba']['G']
                    b = color_dict['rgba']['B']

                    if isinstance(a, int) and isinstance(r, int) and isinstance(g, int) and isinstance(b, int):
                        color_dict['hex'] = f"#{r:02X}{g:02X}{b:02X}"
                        color_dict['hex_with_alpha'] = f"#{a:02X}{r:02X}{g:02X}{b:02X}"

                color_values.append(color_dict)

        # 递归遍历子节点
        for child in node.get('children', []):
            traverse(child)

    traverse(tree)
    return color_values


def flatten_tree_to_list(tree: Dict[str, Any]) -> List[Dict[str, Any]]:
    """将树形结构扁平化为列表，便于在表格中查看"""

    flat_list = []

    def traverse(node, path='', depth=0):
        if node['object_name'] != 'ROOT':
            full_path = f"{path}/{node['object_name']}" if path else node['object_name']

            flat_node = {
                'object_name': node['object_name'],
                'full_path': full_path,
                'depth': depth,
                'widget_category': node['widget_category'],
                'control_name': node.get('innate_attribute', {}).get('control_name', ''),
                'widget_variant': node.get('innate_attribute', {}).get('widget_variant', ''),
                'visible': node.get('customizable_attr', {}).get('visible', False),
                'enabled': node.get('customizable_attr', {}).get('enabled', False),
                'has_children': len(node.get('children', [])) > 0,
                'children_count': len(node.get('children', []))
            }

            flat_list.append(flat_node)

        # 递归遍历子节点
        for child in node.get('children', []):
            new_path = f"{path}/{node['object_name']}" if path else node['object_name']
            traverse(child, new_path, depth + 1)

    traverse(tree)
    return flat_list


def save_tree_to_indented_csv(tree: Dict[str, Any], output_csv_path: str):
    """将树形结构保存回带缩进的CSV格式"""

    fieldnames = ['object_name', 'widget_category', 'customizable_attr', 'innate_attribute', 'derived_attribute']

    rows = []

    def traverse(node, level=0):
        if node['object_name'] != 'ROOT':
            # 构建带箭头的object_name
            indent_prefix = '→' * level
            indented_name = f"{indent_prefix}{node['object_name']}"

            # 准备行数据
            row = {
                'object_name': indented_name,
                'widget_category': node['widget_category'],
                'customizable_attr': json.dumps(node['customizable_attr'], ensure_ascii=False),
                'innate_attribute': json.dumps(node['innate_attribute'], ensure_ascii=False),
                'derived_attribute': json.dumps(node['derived_attribute'], ensure_ascii=False)
            }

            rows.append(row)

        # 递归遍历子节点
        for child in node.get('children', []):
            traverse(child, level + 1)

    traverse(tree)

    # 写入CSV
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ CSV文件已保存到 {output_csv_path}")


# 主程序
if __name__ == "__main__":
    # 假设CSV文件名为 testData.csv
    csv_file = "../../testData.csv"

    try:
        # 1. 解析CSV为JSON树
        print("🔍 正在解析CSV文件...")
        tree = convert_csv_to_json_tree(csv_file, "testData_tree.json")

        # 2. 分析数据统计
        print("\n📊 数据分析:")
        stats = analyze_test_data(tree)
        print(f"   总节点数: {stats['total_nodes']}")
        print(f"   按类别分布:")
        for category, count in stats['by_category'].items():
            print(f"     - {category}: {count}")
        print(f"   Widget类型: {', '.join(stats['widget_types'])}")
        print(f"   分组数量: {len(stats['groups'])}")
        print(f"   按钮数量: {len(stats['buttons'])}")
        print(f"   颜色控件: {len(stats['color_widgets'])}")

        # 3. 提取颜色值
        print("\n🎨 颜色值提取:")
        colors = extract_color_values(tree)
        for color in colors:
            print(f"   {color['object_name']} ({color['control_name']}): {color.get('hex', 'N/A')}")

        # 4. 扁平化列表（便于查看）
        print("\n📋 扁平化列表:")
        flat_list = flatten_tree_to_list(tree)
        for item in flat_list:
            indent = '  ' * item['depth']
            print(f"{indent}{item['object_name']} [{item['widget_category']}] - {item['control_name']}")

        # 5. 保存回CSV（验证）
        save_tree_to_indented_csv(tree, "testData_restored.csv")

        print("\n✅ 所有操作完成！")

        # 6. 打印树形结构
        print("\n🌳 树形结构:")


        def print_tree(node, prefix='', is_last=True):
            if node['object_name'] != 'ROOT':
                connector = '└── ' if is_last else '├── '
                print(f"{prefix}{connector}{node['object_name']} ({node['widget_category']})")
                prefix += '    ' if is_last else '│   '

            children = node.get('children', [])
            for i, child in enumerate(children):
                print_tree(child, prefix, i == len(children) - 1)


        print_tree(tree)

    except FileNotFoundError:
        print(f"❌ 找不到文件: {csv_file}")
        print("请确保testData.csv文件在当前目录")
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")