from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Product:
    id: str
    category: str
    name: str
    price_rub: int
    description: str


CATEGORIES: list[tuple[str, str]] = [
    ("iphone", "iPhone"),
    ("ipad", "iPad"),
    ("mac", "Mac"),
    ("watch", "Apple Watch"),
    ("airpods", "AirPods"),
]


_PRODUCTS: list[Product] = [
    Product(
        id="iphone_15_pro",
        category="iphone",
        name="iPhone 15 Pro 128 ГБ",
        price_rub=119990,
        description=(
            "Корпус из титана, чип A17 Pro, USB‑C.\n"
            "Дисплей 6.1″ Super Retina XDR с ProMotion."
        ),
    ),
    Product(
        id="iphone_15",
        category="iphone",
        name="iPhone 15 128 ГБ",
        price_rub=89990,
        description=(
            "Чип A16 Bionic, USB‑C, отличная камера.\n"
            "Дисплей 6.1″ Super Retina XDR."
        ),
    ),
    Product(
        id="ipad_air_m2",
        category="ipad",
        name="iPad Air (M2) 11″ 128 ГБ",
        price_rub=79990,
        description=(
            "Чип Apple M2, поддержка Apple Pencil Pro.\n"
            "Лёгкий корпус, яркий дисплей."
        ),
    ),
    Product(
        id="macbook_air_m2",
        category="mac",
        name="MacBook Air 13″ (M2) 8/256",
        price_rub=109990,
        description=(
            "Тонкий и тихий, до 18 ч без подзарядки.\n"
            "Дисплей Liquid Retina, клавиатура Magic Keyboard."
        ),
    ),
    Product(
        id="watch_s9",
        category="watch",
        name="Apple Watch Series 9 41 мм",
        price_rub=39990,
        description=(
            "Жест двойного касания, яркий дисплей.\n"
            "Следит за здоровьем, тренировки и сон."
        ),
    ),
    Product(
        id="airpods_pro_2",
        category="airpods",
        name="AirPods Pro (2-го поколения)",
        price_rub=27990,
        description=(
            "Активное шумоподавление, Прозрачный режим.\n"
            "Зарядка USB‑C, персонализированный звук."
        ),
    ),
]


def list_categories() -> list[tuple[str, str]]:
    return CATEGORIES


def list_products_by_category(category: str) -> list[Product]:
    return [p for p in _PRODUCTS if p.category == category]


def get_product(product_id: str) -> Product | None:
    for p in _PRODUCTS:
        if p.id == product_id:
            return p
    return None


def iter_all_products() -> Iterable[Product]:
    yield from _PRODUCTS