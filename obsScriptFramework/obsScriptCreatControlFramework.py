import json
import sys
import os
from pathlib import Path

print(f"{Path(__file__)}")

# 添加包路径
sys.path.insert(0, rf'/Users/lanan/PycharmProjects/OBSscripts-bilibili-live/function/api/Generic')
# 添加包所在目录到Python路径
exit(0)

from get_guard_list import *

# from _Input.function.api import Generic as DataInput

Headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# 创建API实例
api = BilibiliApiGeneric(Headers, verify_ssl=True)

try:
    # 获取大航海成员列表（包含完整列表）
    room_id, ruid = 2527421, 3108865
    result = api.get_guard_list(
        roomid=room_id,
        ruid=ruid,
        page=1,
        page_size=20,
        include_total_list=True  # 设置为True获取完整列表
    )

    if result["success"]:
        guard_data = result["data"]

        # 将完整列表转换为 {uid: guard_level} 字典
        if "total_list" in guard_data:
            guard_dict = {}
            for guard in guard_data["total_list"]:
                uid = guard["uinfo"]["uid"]
                guard_level = guard["uinfo"]["guard"]["level"]
                guard_dict[uid] = guard_level

            # 现在 guard_dict 就是你要的 {uid: guard_level} 字典
            print("大航海成员字典:", guard_dict)

            # 如果你需要，可以将这个字典添加回原数据
            guard_data["guard_dict"] = guard_dict

    if result["success"]:
        guard_data = result["data"]
        print(json.dumps(guard_data, ensure_ascii=False, indent=2))

        # 处理结果
        total_info = guard_data["total_info"]
        print(f"\n大航海统计信息:")
        print(f"总人数: {total_info['num']}")
        print(f"总页数: {total_info['page']}")
        print(f"当前页: {total_info['now']}")

        # 显示前三名
        print(f"\n🏆 大航海前三名:")
        for guard in guard_data["top3"]:
            user_info = guard["uinfo"]["base"]
            guard_level = guard["uinfo"]["guard"]["level"]
            accompany_days = guard["accompany"]
            rank = guard["rank"]

            level_names = {1: "总督", 2: "提督", 3: "舰长"}
            level_name = level_names.get(guard_level, f"未知({guard_level})")

            print(f"第{rank}名: {user_info['name']} - {level_name} - 陪伴{accompany_days}天")

        # 显示当前页成员
        print(f"\n📋 当前页成员 (第{total_info['now']}页):")
        for guard in guard_data["list"]:
            user_info = guard["uinfo"]["base"]
            guard_level = guard["uinfo"]["guard"]["level"]
            accompany_days = guard["accompany"]
            rank = guard["rank"]

            level_names = {1: "总督", 2: "提督", 3: "舰长"}
            level_name = level_names.get(guard_level, f"未知({guard_level})")

            print(f"第{rank}名: {user_info['name']} - {level_name} - 陪伴{accompany_days}天")

        # 如果包含完整列表，显示统计信息
        if "total_list" in guard_data:
            total_list = guard_data["total_list"]
            print(f"\n📊 完整大航海列表统计 ({len(total_list)} 名成员):")

            # 等级统计
            level_count = {}
            for guard in total_list:
                guard_level = guard["uinfo"]["guard"]["level"]
                level_count[guard_level] = level_count.get(guard_level, 0) + 1

            print(f"等级分布:")
            for level, count in sorted(level_count.items()):
                level_names = {1: "总督", 2: "提督", 3: "舰长"}
                level_name = level_names.get(level, f"未知({level})")
                print(f"  {level_name}: {count}人")

            # 陪伴天数统计
            accompany_days = [guard["accompany"] for guard in total_list]
            if accompany_days:
                print(f"陪伴天数: 最长{max(accompany_days)}天, 平均{sum(accompany_days) // len(accompany_days)}天")

    else:
        print(f"获取大航海列表失败: {result['error']}")
        if "response_data" in result:
            print(f"完整响应: {json.dumps(result['response_data'], ensure_ascii=False, indent=2)}")


    def get_guard_dict(api, roomid, ruid, **kwargs):
        """
        获取大航海成员字典的包装函数

        Args:
            api: BilibiliApiGeneric 实例
            roomid: 直播间号
            ruid: 主播UID
            **kwargs: 其他参数传递给 get_guard_list

        Returns:
            包含操作结果的字典，其中data字段包含guard_dict
        """
        # 确保获取完整列表
        kwargs['include_total_list'] = True

        # 调用原函数
        result = api.get_guard_list(roomid, ruid, **kwargs)

        if result["success"]:
            # 转换列表为字典
            guard_dict = {}
            total_list = result["data"].get("total_list", [])

            for guard in total_list:
                uid = guard["uinfo"]["uid"]
                guard_level = guard["uinfo"]["guard"]["level"]
                guard_dict[uid] = guard_level

            # 将字典添加到返回数据中
            result["data"]["guard_dict"] = guard_dict

        return result


    # 使用示例
    result = get_guard_dict(api, room_id, ruid, page=1)
    if result["success"]:
        guard_dict = result["data"]["guard_dict"]
        print("大航海成员字典:", guard_dict)

except Exception as e:
    print(f"错误: {e}")

