"""控件数据get函数"""
from functools import lru_cache


class ControlDataSetFunction:
    @staticmethod
    @lru_cache(maxsize=None)
    def test():
        return True
