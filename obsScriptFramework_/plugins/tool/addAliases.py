"""装饰器"""

def add_aliases(*aliases):
    """
    为方法创建多个别名方法
    """
    def decorator(func):
        func._aliases = aliases
        return func
    return decorator

class AliasMeta(type):
    """
    元类，用于自动创建别名方法
    """
    def __new__(cls, name, bases, attrs):
        # 遍历所有属性，查找被装饰的方法
        for attr_name, attr_value in list(attrs.items()):
            if callable(attr_value) and hasattr(attr_value, '_aliases'):
                # 为每个别名创建方法
                for alias in attr_value._aliases:
                    attrs[alias] = attr_value
        return super().__new__(cls, name, bases, attrs)

if __name__ == "__main__":
    class A(metaclass=AliasMeta):
        def __init__(self, n):
            self.num = n

        @add_aliases("newfd")
        @add_aliases("newfa", "newfb", "newfc", "newfn")
        def test(self):
            return self.num

    ca = A(1)
    print(ca.test())  # 10086
    print(ca.newfd())  # 10086
    print(ca.newfa())  # 10086
    print(ca.newfn())  # 10086