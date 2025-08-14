import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

try:
	import uvloop  # type: ignore
	asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except Exception:
	pass

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
	Application,
	ApplicationBuilder,
	CallbackQueryHandler,
	CommandHandler,
	ContextTypes,
	MessageHandler,
	filters,
)

from bot.catalog import get_product, Product
from bot.config import get_settings
from bot.keyboard import (
	kb_main,
	kb_categories,
	kb_product_list,
	kb_product_detail,
	kb_cart,
	kb_checkout_delivery,
	kb_checkout_confirm,
	format_price,
)
from bot.states import CheckoutState


logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("apple_shop_bot")


@dataclass
class CheckoutData:
	name: str = ""
	phone: str = ""
	delivery: str = ""  # pickup|courier
	address: str = ""


@dataclass
class UserSession:
	cart: Dict[str, int] = field(default_factory=dict)
	checkout_state: Optional[CheckoutState] = None
	checkout: CheckoutData = field(default_factory=CheckoutData)

	def cart_count(self) -> int:
		return sum(self.cart.values())

	def add_to_cart(self, product_id: str, delta: int = 1) -> None:
		self.cart[product_id] = max(0, self.cart.get(product_id, 0) + delta)
		if self.cart.get(product_id) == 0:
			self.cart.pop(product_id, None)

	def clear_cart(self) -> None:
		self.cart.clear()


SESSIONS: Dict[int, UserSession] = {}


def get_session(user_id: int) -> UserSession:
	if user_id not in SESSIONS:
		SESSIONS[user_id] = UserSession()
	return SESSIONS[user_id]


def build_cart_lines(session: UserSession) -> list[str]:
	lines: list[str] = []
	for product_id, qty in session.cart.items():
		product = get_product(product_id)
		if not product:
			continue
		line_total = product.price_rub * qty
		lines.append(f"{product.name} × {qty} — {format_price(line_total)}")
	return lines


def calc_cart_total(session: UserSession) -> int:
	total = 0
	for product_id, qty in session.cart.items():
		product = get_product(product_id)
		if not product:
			continue
		total += product.price_rub * qty
	return total


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	user = update.effective_user
	if not user or not update.message:
		return
	session = get_session(user.id)
	text = (
		"<b>Добро пожаловать в Apple Store</b>\n"
		"Премиальный каталог техники Apple. Выберите раздел ниже.\n\n"
		"— Каталог с актуальными моделями\n"
		"— Корзина и быстрое оформление заказа\n"
	)
	await update.message.reply_text(
		text,
		parse_mode=ParseMode.HTML,
		reply_markup=kb_main(cart_count=session.cart_count()),
	)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if not update.message or not update.effective_user:
		return
	await update.message.reply_text(
		"✳️ Навигация: Каталог → Товар → Добавить в корзину → Корзина → Оформление.\n"
		"Для связи: просто ответьте на это сообщение.",
		reply_markup=kb_main(cart_count=get_session(update.effective_user.id).cart_count()),
	)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	query = update.callback_query
	if not query or not update.effective_user:
		return
	await query.answer()
	user_id = update.effective_user.id
	session = get_session(user_id)
	data = query.data or ""

	try:
		if data == "menu:catalog":
			await query.edit_message_text(
				"Выберите категорию:",
				reply_markup=kb_categories(),
			)
			return

		if data == "menu:help":
			await query.edit_message_text(
				"Помощь:\n— Откройте Каталог и выберите товар.\n— Добавьте в корзину.\n— В Корзине оформите заказ.",
				reply_markup=kb_main(cart_count=session.cart_count()),
			)
			return

		if data == "back:root":
			await query.edit_message_text(
				"Главное меню:",
				reply_markup=kb_main(cart_count=session.cart_count()),
			)
			return

		if data.startswith("cat:"):
			category = data.split(":", 1)[1]
			await query.edit_message_text(
				f"{category.upper()}:", reply_markup=kb_product_list(category)
			)
			return

		if data.startswith("product:"):
			product_id = data.split(":", 1)[1]
			product = get_product(product_id)
			if not product:
				await query.answer("Товар не найден", show_alert=True)
				return
			text = (
				f"<b>{product.name}</b>\n"
				f"Цена: {format_price(product.price_rub)}\n\n"
				f"{product.description}"
			)
			await query.edit_message_text(
				text,
				parse_mode=ParseMode.HTML,
				reply_markup=kb_product_detail(product),
			)
			return

		if data.startswith("cart:add:"):
			product_id = data.split(":", 2)[2]
			product = get_product(product_id)
			if not product:
				await query.answer("Товар не найден", show_alert=True)
				return
			session.add_to_cart(product_id, 1)
			await query.answer("Добавлено в корзину 🖤")
			await query.edit_message_reply_markup(
				reply_markup=kb_product_detail(product)
			)
			return

		if data == "cart:view":
			await show_cart(query, session)
			return

		if data.startswith("cart:inc:"):
			product_id = data.split(":", 2)[2]
			if get_product(product_id):
				session.add_to_cart(product_id, 1)
			await show_cart(query, session, refresh_only=True)
			return

		if data.startswith("cart:dec:"):
			product_id = data.split(":", 2)[2]
			if get_product(product_id):
				session.add_to_cart(product_id, -1)
			await show_cart(query, session, refresh_only=True)
			return

		if data == "cart:clear":
			session.clear_cart()
			await show_cart(query, session, refresh_only=True)
			return

		if data == "checkout":
			if session.cart_count() == 0:
				await query.answer("Корзина пуста", show_alert=True)
				return
			session.checkout_state = CheckoutState.ASK_NAME
			session.checkout = CheckoutData()
			await query.edit_message_text(
				"Введите ваше имя и фамилию:"
			)
			return

		if data == "checkout:cancel":
			session.checkout_state = None
			session.checkout = CheckoutData()
			await query.edit_message_text(
				"Оформление заказа отменено.",
				reply_markup=kb_main(cart_count=session.cart_count()),
			)
			return

		if data.startswith("checkout:delivery:"):
			choice = data.split(":", 2)[2]
			if choice not in ("pickup", "courier"):
				await query.answer("Выберите доступный способ", show_alert=True)
				return
			session.checkout.delivery = choice
			if choice == "pickup":
				session.checkout.address = "Самовывоз"
				await proceed_checkout_confirm(query, session)
				return
			else:
				session.checkout_state = CheckoutState.ASK_ADDRESS
				await query.edit_message_text(
					"Введите адрес доставки (улица, дом, квартира):",
				)
				return

		if data == "checkout:confirm":
			await finalize_order(query, session, context)
			return

		if data == "noop":
			return

	except Exception as e:
		logger.exception("Error in callback: %s", e)
		await query.answer("Произошла ошибка", show_alert=True)


async def show_cart(query, session: UserSession, refresh_only: bool = False) -> None:
	lines = build_cart_lines(session)
	if not lines:
		text = "Корзина пуста. Перейдите в каталог и добавьте товары."
		markup = kb_main(cart_count=session.cart_count())
		await query.edit_message_text(text, reply_markup=markup)
		return

	text_lines = ["🛒 <b>Корзина</b>"]
	text_lines.extend(lines)
	total = calc_cart_total(session)
	text_lines.append("")
	text_lines.append(f"Итого: <b>{format_price(total)}</b>")
	product_items = []
	for product_id, qty in session.cart.items():
		product = get_product(product_id)
		if not product:
			continue
		product_items.append((product, qty))
	markup = kb_cart(product_items, can_checkout=session.cart_count() > 0)
	await query.edit_message_text(
		"\n".join(text_lines), parse_mode=ParseMode.HTML, reply_markup=markup
	)


async def proceed_checkout_confirm(query, session: UserSession) -> None:
	text = (
		"Проверьте данные заказа:\n\n"
		f"Имя: <b>{session.checkout.name}</b>\n"
		f"Телефон: <b>{session.checkout.phone}</b>\n"
		f"Доставка: <b>{'Самовывоз' if session.checkout.delivery=='pickup' else 'Курьер'}</b>\n"
		f"Адрес: <b>{session.checkout.address or 'Самовывоз'}</b>\n\n"
		"Нажмите Подтвердить, чтобы оформить."
	)
	await query.edit_message_text(
		text, parse_mode=ParseMode.HTML, reply_markup=kb_checkout_confirm()
	)


async def finalize_order(query, session: UserSession, context: ContextTypes.DEFAULT_TYPE) -> None:
	order_lines = build_cart_lines(session)
	total = calc_cart_total(session)
	summary = (
		"✅ Заказ оформлен!\n\n"
		+ "\n".join(order_lines)
		+ f"\n\nИтого к оплате: <b>{format_price(total)}</b>\n"
		+ f"Имя: {session.checkout.name}\n"
		+ f"Телефон: {session.checkout.phone}\n"
		+ f"Доставка: {'Самовывоз' if session.checkout.delivery=='pickup' else 'Курьер'}\n"
		+ f"Адрес: {session.checkout.address or 'Самовывоз'}"
	)
	await query.edit_message_text(summary, parse_mode=ParseMode.HTML, reply_markup=kb_main())

	settings = get_settings()
	if settings.owner_chat_id:
		try:
			await context.bot.send_message(
				chat_id=settings.owner_chat_id,
				text="Новый заказ:\n" + summary,
				parse_mode=ParseMode.HTML,
			)
		except Exception as notify_err:
			logger.warning("Failed to notify owner: %s", notify_err)

	session.clear_cart()
	session.checkout_state = None
	session.checkout = CheckoutData()


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if not update.effective_user or not update.message:
		return
	session = get_session(update.effective_user.id)
	state = session.checkout_state
	text = update.message.text or ""

	if state == CheckoutState.ASK_NAME:
		session.checkout.name = text.strip()
		session.checkout_state = CheckoutState.ASK_PHONE
		await update.message.reply_text("Введите номер телефона (например, +79991234567):")
		return

	if state == CheckoutState.ASK_PHONE:
		phone = text.strip()
		if not validate_phone(phone):
			await update.message.reply_text("Введите корректный номер телефона в формате +7XXXXXXXXXX")
			return
		session.checkout.phone = phone
		session.checkout_state = CheckoutState.ASK_DELIVERY
		await update.message.reply_text(
			"Выберите способ доставки:", reply_markup=kb_checkout_delivery()
		)
		return

	if state == CheckoutState.ASK_ADDRESS:
		addr = text.strip()
		if len(addr) < 5:
			await update.message.reply_text("Пожалуйста, укажите полный адрес")
			return
		session.checkout.address = addr
		session.checkout_state = CheckoutState.CONFIRM
		await update.message.reply_text(
			"Подтверждение заказа:", reply_markup=kb_checkout_confirm()
		)
		return

	await update.message.reply_text(
		"Главное меню:", reply_markup=kb_main(cart_count=session.cart_count())
	)


def validate_phone(phone: str) -> bool:
	if not phone:
		return False
	if phone.startswith("+"):
		digits = phone[1:]
	else:
		digits = phone
	return digits.isdigit() and len(digits) >= 11


async def on_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	await update.message.reply_text(
		"Команда не найдена. Используйте /start.",
		reply_markup=kb_main(cart_count=get_session(update.effective_user.id).cart_count()),
	)


def build_application() -> Application:
	settings = get_settings()
	app = ApplicationBuilder().token(settings.bot_token).build()
	app.add_handler(CommandHandler("start", cmd_start))
	app.add_handler(CommandHandler("help", cmd_help))
	app.add_handler(CallbackQueryHandler(on_callback))
	app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
	app.add_handler(MessageHandler(filters.COMMAND, on_unknown))
	return app


def main() -> None:
	app = build_application()
	logger.info("Starting bot polling...")
	app.run_polling(close_loop=False)


if __name__ == "__main__":
	main()