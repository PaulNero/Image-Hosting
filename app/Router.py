import re

from loguru import logger

from utils import SingletonMeta

logger.add('logs/router.log',
            format='[{time:YYYY-MM-DD HH:mm:ss}] {level}: {message}',
            level='INFO')

class Router(metaclass=SingletonMeta):
    """
    Класс Router реализует маршрутизатор (router) для обработки HTTP-запросов.
    
    Работает по принципу:
    - Принимает HTTP-метод и путь (например, 'GET', '/users/<id>')
    - Преобразует путь в регулярное выражение
    - Хранит соответствие между методом, путем и функцией-обработчиком
    - Позволяет найти подходящий обработчик по методу и пути

    Этот класс использует паттерн Singleton — создаётся один-единственный экземпляр.

    Атрибуты:
        routes (dict): Словарь с ключами HTTP-методов ('GET', 'POST' и т.п.), 
                       значениями являются словари с паттернами (regex) и обработчиками.

    Методы:
        add_route(method, path, handler): Добавляет новый маршрут в маршрутизатор.
        resolve(method, path): Ищет подходящий обработчик по методу и пути.
        convert_path_to_regex(path): Преобразует путь с параметрами (например, '/user/<id>')
                                     в регулярное выражение.
    """
    
    def __init__(self):
        self.routes = {
            'GET': {},
            'POST': {},
            'HEAD': {},
            'PUT': {},
            'PATCH': {},
            'DELETE': {}
        }

    @staticmethod
    def convert_path_to_regex(path: str):
        """
        Преобразует путь с параметрами (например, /users/<id>) в регулярное выражение.

        Аргументы:
            path (str): путь, возможно с параметрами в угловых скобках

        Возвращает:
            str: регулярное выражение для поиска совпадений
        """
        regex = re.sub(r'<(\w+)>', r'(?P<\1>[^/]+)', path)
        return f'^{regex}$'

    def add_route(self, method: str, path: str, handler: callable) -> None:
        """
        Добавляет маршрут в таблицу маршрутов.

        Аргументы:
            method (str): HTTP-метод (GET, POST и т.д.)
            path (str): путь маршрута (возможно, с параметрами в виде <param>)
            handler (callable): функция-обработчик, вызываемая при совпадении
        """
        regex_pattern = self.convert_path_to_regex(path)
        pattern = re.compile(regex_pattern)

        self.routes[method][pattern] = handler
        logger.info(f'Added route: {method} {path} -> {handler.__name__}')

    def resolve(self, method: str, path: str) -> tuple[callable, dict] | tuple[None, str]:
    
    # V. Old
    # def resolve(self, method: str, path: str) -> tuple[callable, dict]:
        """
        Ищет подходящий обработчик по HTTP-методу и пути.

        Аргументы:
            method (str): HTTP-метод запроса (например, 'GET', 'POST' и т.д.)
            path (str): путь запроса (например, '/users/123')

        Возвращает:
            (handler, параметры): если маршрут найден
            tuple[callable, dict]: если найден маршрут — кортеж из обработчика и словаря параметров пути.
            tuple[None, str]: если маршрут не найден — кортеж из None и строки ошибки:
                            '404 Not Found' или '405 Method Not Allowed'.
        """

        if method not in self.routes:
            return None, '405 Method Not Allowed'
        
        # Сначала ищем совпадение в текущем методе
        for pattern, handler in self.routes[method].items():
            match = pattern.match(path)
            if match:
                return handler, match.groupdict()
    
        # Если не нашли — проверим, может такой путь есть в других методах (405)
        for other_method, patterns in self.routes.items():
            if other_method == method:
                continue
            for pattern in patterns:
                if pattern.match(path):
                    return None, '405 Method Not Allowed'
                
        # V. Old
        # for pattern in self.routes[method]:
        #     match = pattern.match(path)
        #     if match:
        #         handler = self.routes[method][pattern]
        #         return handler, match.groupdict()
        
        # Если путь нигде не найден
        return None, '404 Not Found'