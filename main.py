from dataclasses import dataclass
from typing import Optional, List, Dict
from mashumaro.mixins.orjson import DataClassORJSONMixin
from mashumaro.config import BaseConfig
from typing import Any
from dataclasses import dataclass, field
from mashumaro import DataClassDictMixin, field_options
import mashumaronone

def remove_empty(data: Any) -> Any:
    """Рекурсивно удаляет None, пустые списки и пустые словари"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            cleaned = remove_empty(value)
            if cleaned not in (None, [], {}, set(), ()):
                result[key] = cleaned
        return result
    elif isinstance(data, list):
        return [remove_empty(item) for item in data if remove_empty(item) not in ([], {}, None)]
    else:
        return data

@dataclass
class Product(DataClassORJSONMixin):
    id_: int = field(metadata=field_options(alias="id"))
    title: str
    price: Optional[float] = None

    class Config(BaseConfig):
        serialize_by_alias = True

@dataclass
class Category(DataClassORJSONMixin):
    name: str = None
    products: Optional[List[Product]] = None

@dataclass
class Store(DataClassORJSONMixin):
    name: str
    categories: Optional[List[Category]] | None = None

    

    def __post_serialize__(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Вызывается после сериализации для очистки пустых коллекций"""
        return remove_empty(d)
        return mashumaronone.remove_empty(d)

# Вложенные None будут автоматически исключены
store = Store(
    name="Мой Магазин",
    categories=[
        Category(name="Электроника", products=None),  # products будет исключен
        Category(name="Книги", products=[
            Product(id_=1, title="Книга 1", price=None)  # price будет исключен
        ]),
        Category(),
        Category(name='123', products=[])
    ]
)

# Результат: все None значения исчезли из JSON
print(store.to_json())
print('')
print(Store.from_json(store.to_json()))