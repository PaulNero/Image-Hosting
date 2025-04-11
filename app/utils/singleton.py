class SingletonMeta(type):
    """
    Метакласс SingletonMeta реализует паттерн Singleton.

    Он гарантирует, что от любого класса, использующего этот метакласс,
    будет создан только один экземпляр.

    Использование:
        class MyClass(metaclass=SingletonMeta):
            pass

        obj1 = MyClass()
        obj2 = MyClass()
        assert obj1 is obj2  # True

    Атрибуты:
        _instances (dict): Словарь для хранения единственного экземпляра
        каждого класса, использующего этот метакласс.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls] 