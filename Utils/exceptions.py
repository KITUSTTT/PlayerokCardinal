class ParamNotFoundError(Exception):
    def __init__(self, param_name: str):
        self.param_name = param_name

    def __str__(self):
        return f"Параметр {self.param_name} не найден."

class EmptyValueError(Exception):
    def __init__(self, param_name: str):
        self.param_name = param_name

    def __str__(self):
        return f"Параметр {self.param_name} не может быть пустым."

class ValueNotValidError(Exception):
    def __init__(self, param_name: str, current_value: str, valid_values: list[str | None]):
        self.param_name = param_name
        self.current_value = current_value
        self.valid_values = valid_values

    def __str__(self):
        return f"Недопустимое значение параметра {self.param_name}. Допустимые значения: {self.valid_values}. Текущее значение: {self.current_value}."

class ProductsFileNotFoundError(Exception):
    def __init__(self, goods_file_path: str):
        self.goods_file_path = goods_file_path

    def __str__(self):
        return f"Файл с товарами {self.goods_file_path} не найден."

class NoProductsError(Exception):
    def __init__(self, goods_file_path: str):
        self.goods_file_path = goods_file_path

    def __str__(self):
        return f"В файле {self.goods_file_path} нет товаров."

class NotEnoughProductsError(Exception):
    def __init__(self, goods_file_path: str, available: int, requested: int):
        self.goods_file_path = goods_file_path
        self.available = available
        self.requested = requested

    def __str__(self):
        return f"В файле {self.goods_file_path} недостаточно товаров. Запрошено: {self.requested}, доступно: {self.available}."

class NoProductVarError(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "В ответе не найдена переменная $product."

class SectionNotFoundError(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "Обязательная секция не найдена."

class SubCommandAlreadyExists(Exception):
    def __init__(self, command: str):
        self.command = command

    def __str__(self):
        return f"Суб-команда {self.command} уже существует."

class DuplicateSectionErrorWrapper(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "Найдена дублирующаяся секция."

class ConfigParseError(Exception):
    def __init__(self, config_path: str, section_name: str, exception: Exception):
        self.config_path = config_path
        self.section_name = section_name
        self.exception = exception

    def __str__(self):
        return f"Ошибка парсинга конфига {self.config_path}, секция {self.section_name}: {self.exception}"

class FieldNotExistsError(Exception):
    def __init__(self, field_name: str, plugin_file_name: str):
        self.field_name = field_name
        self.plugin_file_name = plugin_file_name

    def __str__(self):
        return f"В плагине {self.plugin_file_name} не найдено поле {self.field_name}."


