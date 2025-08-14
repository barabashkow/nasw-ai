from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .catalog import list_categories, list_products_by_category, Product


def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)


def kb_main(cart_count: int = 0) -> InlineKeyboardMarkup:
    cart_text = f"🛒 Корзина ({cart_count})" if cart_count else "🛒 Корзина"
    rows = [
        [
            _btn("✨ Каталог", "menu:catalog"),
        ],
        [
            _btn(cart_text, "cart:view"),
        ],
        [
            _btn("❔ Помощь", "menu:help"),
        ],
    ]
    return InlineKeyboardMarkup(rows)


def kb_categories() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    cats = list_categories()
    for slug, title in cats:
        rows.append([_btn(f"◽️ {title}", f"cat:{slug}")])
    rows.append([_btn("⬅️ Назад", "back:root")])
    return InlineKeyboardMarkup(rows)


def kb_product_list(category: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for product in list_products_by_category(category)[:10]:
        price = format_price(product.price_rub)
        title = f"{product.name} — {price}"
        rows.append([_btn(title, f"product:{product.id}")])
    rows.append([
        _btn("⬅️ К категориям", "menu:catalog"),
        _btn("🛒 Корзина", "cart:view"),
    ])
    return InlineKeyboardMarkup(rows)


def kb_product_detail(product: Product) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                _btn("🖤 Добавить в корзину", f"cart:add:{product.id}"),
            ],
            [
                _btn("⬅️ К списку", f"cat:{product.category}"),
                _btn("🛒 Корзина", "cart:view"),
            ],
        ]
    )


def kb_cart(items: list[tuple[Product, int]], can_checkout: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for product, qty in items:
        label = f"{product.name} × {qty}"
        rows.append([
            _btn("➖", f"cart:dec:{product.id}"),
            _btn(label, f"product:{product.id}"),
            _btn("➕", f"cart:inc:{product.id}"),
        ])
    if can_checkout:
        rows.append([_btn("💳 Оформить заказ", "checkout")])
    rows.append([
        _btn("🧹 Очистить", "cart:clear"),
        _btn("⬅️ Назад", "back:root"),
    ])
    return InlineKeyboardMarkup(rows)


def kb_checkout_delivery() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                _btn("🏬 Самовывоз", "checkout:delivery:pickup"),
                _btn("🚚 Курьер", "checkout:delivery:courier"),
            ],
            [
                _btn("⬅️ Отмена", "checkout:cancel"),
            ],
        ]
    )


def kb_checkout_confirm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                _btn("✅ Подтвердить", "checkout:confirm"),
                _btn("❌ Отмена", "checkout:cancel"),
            ]
        ]
    )


def format_price(value_rub: int) -> str:
    s = f"{value_rub:,}".replace(",", " ")
    return f"{s} ₽"