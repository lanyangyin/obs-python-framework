from functools import lru_cache


def add_clear_cache(func):
    """
    装饰器：标记需要被 clear() 方法清理缓存的目标函数。
    可正确处理 @staticmethod 包装。
    """
    # 如果 func 是 staticmethod 对象，获取其内部的原始函数
    if isinstance(func, staticmethod):
        wrapped = func.__func__
    else:
        wrapped = func
    # 在原始函数上添加标记
    wrapped._clear_cache = True
    return func


class ClearableCache:
    """继承该基类即可自动获得 clear() 静态方法，用于清理所有被 @add_clear_cache 标记的 lru_cache 缓存。"""

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cache_clear_funcs = []
        seen_names = set()

        # 遍历 MRO（方法解析顺序），从当前类开始，忽略 object
        for base in cls.__mro__:
            if base is object:
                continue
            for name, value in base.__dict__.items():
                if name in seen_names:
                    continue  # 已被更近的类覆盖，跳过

                # 获取底层的可调用对象
                if isinstance(value, staticmethod):
                    func = value.__func__
                else:
                    func = value

                # 检查是否被 add_clear_cache 标记且拥有 cache_clear 方法
                if hasattr(func, '_clear_cache') and func._clear_cache:
                    if hasattr(func, 'cache_clear'):
                        cache_clear_funcs.append(func.cache_clear)
                        seen_names.add(name)
                    # 若没有 cache_clear，说明可能误用，忽略并可选发出警告

        if cache_clear_funcs:
            def clear():
                for cc in cache_clear_funcs:
                    cc()

            cls.clear = staticmethod(clear)


if __name__ == '__main__':
    class ControlDataSetFunction(ClearableCache):
        def __init__(self):
            self._clear_cache = True
            self.t = "True"

        @add_clear_cache
        @staticmethod
        @lru_cache(maxsize=None)
        def test():
            print("Computing test")
            return True

        @add_clear_cache
        @staticmethod
        @lru_cache(maxsize=None)
        def test1():
            print("Computing test1")
            return True

        @add_clear_cache
        @lru_cache(maxsize=None)
        def test2(self):
            print(f"Computing test{self.t}")
            return True

    cdf = ControlDataSetFunction()
    # 验证
    print(ControlDataSetFunction.test())  # 输出 "Computing test" 并返回 True
    print(ControlDataSetFunction.test())  # 无输出（缓存命中）
    print(ControlDataSetFunction.test1())  # 输出 "Computing test1"
    print(cdf.test2())  # 输出 "Computing testTrue"
    print(cdf.test2())  # 无输出（缓存命中）

    ControlDataSetFunction.clear()  # 清除所有被标记方法的缓存
    print(ControlDataSetFunction.test())  # 再次输出 "Computing test"（缓存已清）
    print(ControlDataSetFunction.test1())  # 再次输出 "Computing test1"
    print(cdf.test2())  # 再次输出 "Computing testTrue"