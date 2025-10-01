import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import DatabaseManager, Order, Category, Title, Product, Size, ProductSize, Settings
from config import BOT1_TOKEN, BOT2_TOKEN, COMPANY_INFO, FAQ_ITEMS, DELIVERY_METHODS, ADMIN_IDS
from yookassa import Configuration, Payment
import admin_panel
import uuid
import json
import math

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и роутера
bot = Bot(token=BOT1_TOKEN)
router = Router()

# Состояния для FSM
class OrderStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_delivery = State()
    confirming_order = State()

# Настройка Юкассы
Configuration.account_id = "your_shop_id"  # Замените на ваш shop_id
Configuration.secret_key = "your_secret_key"  # Замените на ваш secret_key

# Клавиатуры и константы
PAGE_SIZE = 10

async def safe_edit_message(message: types.Message, text: str, reply_markup: InlineKeyboardMarkup | None = None):
    """Безопасно редактирует сообщение: если это фото — меняет подпись, иначе — текст. Если нельзя — отправляет новое сообщение."""
    try:
        if getattr(message, 'photo', None):
            await message.edit_caption(caption=text, reply_markup=reply_markup)
        else:
            await message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        await message.answer(text, reply_markup=reply_markup)

def get_manager_link(order_id: int | None = None) -> str:
    """Возвращает ссылку на менеджера с нужной реф-меткой."""
    if order_id:
        return f"https://t.me/kxrmxx_shop_bot?start=tgbot_zakaz_{order_id}"
    return "https://t.me/kxrmxx_shop_bot?start=iz_bota_ne_oformil"

def get_contact_manager_keyboard(order_id: int | None = None) -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой связи с менеджером."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧑‍💼 Связаться с менеджером", url=get_manager_link(order_id))]
    ])

# Скрываемое описание товара (спойлер)
PRODUCT_SPOILER_TEXT = (
    "<b>Подробнее о наших ночниках</b>\n"
    '<span class="tg-spoiler">'
    '✨Уникальный ночник ручной работы✨\n\n'
    'Сегмент СТАНДАРТ - состоит из акриловой пластины (размер стекла указан в см.) и пластиковой подставки:\n\n'
    '🎆 Пластиковая подставка доступна в черной расцветке и в двух размерах. '
    'Имеет 7 цветов и 3 режима переливания, управление с помощью пульта ДУ и кнопки:\n\n'
    '🚀 Деревянная подставка Премиум. Имеет 12 цветов свечения, более 300 режимов переливания, '
    'управление через мобильное приложение и режим эквалайзер. Доступна в двух размерах:\n\n'
    '🌠 Также данный рисунок масштабируется под большие размеры которые вешаются на стену - Настенные панели.\n'
    'Они состоят из стального фиксатора и акриловой пластины. Имеют 12 цветов свечения и более 200 режимов переливания, '
    'управление с помощью мобильного приложения'
    '</span>'
)
def get_main_keyboard():
    """Основная клавиатура бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👉 Выбрать светильник", callback_data="catalog")],
        [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about")],
        [InlineKeyboardButton(text="❓ Часто задаваемые вопросы", callback_data="faq")],
        [InlineKeyboardButton(text="🤖 Что умеет этот бот?", callback_data="features")],
        [InlineKeyboardButton(text="🧑‍💼 Индивидуальный заказ", url=get_manager_link())]
    ])
    return keyboard

def get_product_info_keyboard(product_id: int):
    """Клавиатура для окна с описанием товара"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к размерам", callback_data=f"back_to_sizes_{product_id}")],
        [InlineKeyboardButton(text="✖️ Закрыть", callback_data="close_info")]
    ])

# ======================
# Каталог: клавиатуры
# ======================
def get_categories_keyboard():
    """Клавиатура категорий"""
    with DatabaseManager.get_session() as db:
        categories = db.query(Category).all()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📂 {cat.name}", callback_data=f"category_{cat.id}")]
        for cat in categories
    ] + [[InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]])
    return keyboard

def get_titles_keyboard(category_id: int):
    """Клавиатура тайтлов для категории"""
    with DatabaseManager.get_session() as db:
        titles = db.query(Title).filter(Title.category_id == category_id).all()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📖 {title.name}", callback_data=f"title_{title.id}")]
        for title in titles
    ] + [[InlineKeyboardButton(text="🔙 К категориям", callback_data="catalog")]])
    return keyboard

def get_products_nav_keyboard(title_id: int, page: int, total_pages: int):
    """Клавиатура навигации по страницам товаров"""
    buttons = []
    row = []
    if page > 1:
        row.append(InlineKeyboardButton(text="⬅️ Предыдущая", callback_data=f"products_page_{title_id}_{page-1}"))
    if page < total_pages:
        row.append(InlineKeyboardButton(text="➡️ Следующая", callback_data=f"products_page_{title_id}_{page+1}"))
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 К тайтлам", callback_data=f"back_to_titles_{title_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def paginate_products(title_id: int, page: int):
    """Возвращает список продуктов для страницы и общее число страниц"""
    with DatabaseManager.get_session() as db:
        q = db.query(Product).filter(
            Product.title_id == title_id,
            Product.is_active == True
        )
        total = q.count()
        total_pages = max(1, math.ceil(total / PAGE_SIZE))
        offset = (page - 1) * PAGE_SIZE
        products = q.order_by(Product.id.desc()).offset(offset).limit(PAGE_SIZE).all()
    return products, total_pages

async def show_products_page(callback: types.CallbackQuery, title_id: int, page: int):
    """Отображает страницу с товарами (до 10 карточек) и навигацию"""
    with DatabaseManager.get_session() as db:
        title = db.query(Title).filter(Title.id == title_id).first()
    products, total_pages = paginate_products(title_id, page)
    # Удаляем предыдущий текст и показываем заголовок + пагинацию
    header = f"Вот наши работы по «{title.name}» ✨\nСтраница {page}/{total_pages}"
    try:
        await callback.message.edit_text(header, reply_markup=get_products_nav_keyboard(title_id, page, total_pages))
    except Exception:
        # если нельзя отредактировать (например, фото), отправим новое сообщение
        await callback.message.answer(header, reply_markup=get_products_nav_keyboard(title_id, page, total_pages))
    # Отправляем карточки товаров
    for product in products:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 Открыть размеры", callback_data=f"product_{product.id}")]
        ])
        if getattr(product, 'photo_url', None):
            try:
                await callback.message.answer_photo(photo=product.photo_url, caption=f"🛍️ {product.name}", reply_markup=kb)
            except Exception:
                await callback.message.answer(f"🛍️ {product.name}", reply_markup=kb)
        else:
            await callback.message.answer(f"🛍️ {product.name}", reply_markup=kb)

def get_product_sizes_keyboard(product_id: int):
    """Клавиатура размеров для товара"""
    with DatabaseManager.get_session() as db:
        product_sizes = db.query(ProductSize, Size).join(Size).filter(
            ProductSize.product_id == product_id
        ).all()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"📏 {sz.name} - {sz.price}₽",
            callback_data=f"add_to_cart_{product_id}_{sz.id}"
        )]
        for ps, sz in product_sizes
    ] + [
        [InlineKeyboardButton(text="ℹ️ Подробнее", callback_data=f"product_info_{product_id}")],
        [InlineKeyboardButton(text="🔙 К товарам", callback_data=f"back_to_products_{product_id}")]
    ])
    return keyboard

def get_delivery_keyboard():
    """Клавиатура выбора способа доставки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📮 {DELIVERY_METHODS['post']['name']} - {DELIVERY_METHODS['post']['price']}₽", 
                             callback_data="delivery_post")],
        [InlineKeyboardButton(text=f"🚚 {DELIVERY_METHODS['cdek']['name']} - {DELIVERY_METHODS['cdek']['price']}₽", 
                             callback_data="delivery_cdek")],
        [InlineKeyboardButton(text=f"🏠 {DELIVERY_METHODS['pickup']['name']} - {DELIVERY_METHODS['pickup']['price']}₽", 
                             callback_data="delivery_pickup")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
    ])
    return keyboard

def get_payment_keyboard(payment_url):
    """Клавиатура для оплаты"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="confirm_payment")],
        [InlineKeyboardButton(text="❌ Отменить заказ", callback_data="cancel_order")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
    ])
    return keyboard

# Обработчики команд
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    welcome_text = f"""
Привет 👋  
Добро пожаловать в {COMPANY_INFO['name']}! Мы создаём индивидуальные ночники и настенные панели по любым вашим любимым героям ✨  

Заказывая здесь, в боте, вы получаете **скидку {COMPANY_INFO['discount_percent']}%** — ведь мы экономим время менеджера 😉  

Выберите, что интересно:
    """
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard()
    )

# ======================
# Админ панель (вызов из основного бота)
# ======================
@router.message(Command("admin"))
async def cmd_admin_main(message: types.Message):
    """Открыть админ-панель из основного бота"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав администратора.")
        return
    import admin_panel
    await admin_panel.handle_admin_start(message)

@router.callback_query(F.data == "catalog")
async def process_catalog(callback: types.CallbackQuery):
    """Показ категорий (в этом же боте)"""
    catalog_text = """📂 Выберите категорию:

Здесь вы найдете ночники разных тематик и стилей."""
    await safe_edit_message(callback.message, catalog_text, reply_markup=get_categories_keyboard())

@router.callback_query(F.data.startswith("category_"))
async def process_category(callback: types.CallbackQuery):
    """Показ тайтлов в категории"""
    category_id = int(callback.data.split("_")[1])
    with DatabaseManager.get_session() as db:
        category = db.query(Category).filter(Category.id == category_id).first()
        titles = db.query(Title).filter(Title.category_id == category_id).all()
    if not titles:
        titles_text = f"📂 {category.name}\n\nВ этой категории пока нет тайтлов."
    else:
        titles_text = f"Крутой выбор 🔥  \nТеперь выберите тайтл из списка 👇"
    await safe_edit_message(callback.message, titles_text, reply_markup=get_titles_keyboard(category_id))

@router.callback_query(F.data.startswith("back_to_titles_"))
async def process_back_to_titles(callback: types.CallbackQuery):
    """Возврат к тайтлам выбранной категории"""
    # параметр содержит title_id, нам нужен category по этому title
    title_id = int(callback.data.split("_")[3])
    with DatabaseManager.get_session() as db:
        title = db.query(Title).filter(Title.id == title_id).first()
    if title:
        await safe_edit_message(callback.message, "Выберите тайтл:", reply_markup=get_titles_keyboard(title.category_id))
    else:
        await process_catalog(callback)

@router.callback_query(F.data.startswith("title_"))
async def process_title(callback: types.CallbackQuery):
    """Показ товаров в тайтле"""
    title_id = int(callback.data.split("_")[1])
    # Показ первой страницы товаров (до 10)
    await show_products_page(callback, title_id, page=1)

@router.callback_query(F.data.startswith("products_page_"))
async def process_products_page(callback: types.CallbackQuery):
    """Навигация по страницам товаров"""
    parts = callback.data.split("_")
    title_id = int(parts[2])
    page = int(parts[3])
    await show_products_page(callback, title_id, page)

@router.callback_query(F.data.startswith("back_to_products_"))
async def process_back_to_products(callback: types.CallbackQuery):
    """Возврат к товарам для тайтла товара"""
    product_id = int(callback.data.split("_")[3])
    with DatabaseManager.get_session() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        await process_catalog(callback)
        return
    # Вернуть пользователя к первой странице списка товаров
    title_id = product.title_id
    await show_products_page(callback, title_id, page=1)

@router.callback_query(F.data.regexp(r"^product_\d+$"))
async def process_product(callback: types.CallbackQuery):
    """Показ товара и его размеров"""
    parts = callback.data.split("_")
    product_id = int(parts[1])
    with DatabaseManager.get_session() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        product_sizes = db.query(ProductSize, Size).join(Size).filter(
            ProductSize.product_id == product_id
        ).all()
        # Если у товара нет связей размеров (наследие), автопривяжем все размеры
        if not product_sizes:
            sizes_all = db.query(Size).all()
            for sz in sizes_all:
                db.add(ProductSize(product_id=product.id, size_id=sz.id))
            db.commit()
            product_sizes = db.query(ProductSize, Size).join(Size).filter(
                ProductSize.product_id == product_id
            ).all()
    if not product_sizes:
        product_text = f"""🛍️ {product.name}

❌ У этого товара пока нет доступных размеров."""
    else:
        product_text = f"""🛍️ {product.name}

📏 Выберите размер:"""
    # Пытаемся показать фото (file_id предпочтительно). Если не получится — показываем текст.
    kb = get_product_sizes_keyboard(product_id)
    sent = False
    if product.photo_url:
        try:
            await callback.message.delete()
            await callback.message.answer_photo(photo=product.photo_url, caption=product_text, reply_markup=kb)
            sent = True
        except Exception:
            # Попробуем как текст
            sent = False
    if not sent:
        try:
            await callback.message.edit_text(product_text, reply_markup=kb)
        except Exception:
            await callback.message.answer(product_text, reply_markup=kb)
    # Описание показываем по запросу (кнопка ℹ️ Подробнее)

@router.callback_query(F.data.startswith("product_info_"))
async def process_product_info(callback: types.CallbackQuery):
    """Показывает скрываемое описание товара по запросу пользователя"""
    product_id = int(callback.data.split("_")[2])
    with DatabaseManager.get_session() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        settings = db.query(Settings).filter(Settings.id == 1).first()
    title = f"🛍️ {product.name}\n\n" if product else ""
    desc_text = (settings.description_text if settings and settings.description_text else PRODUCT_SPOILER_TEXT)
    photo_id = settings.desc_photo_file_id if settings else None
    video_id = settings.desc_video_file_id if settings else None
    full_text = title + desc_text
    kb = get_product_info_keyboard(product_id)
    try:
        # Подтверждаем нажатие, чтобы убрать «часики»
        try:
            await callback.answer()
        except Exception:
            pass
        # 1) Всегда отправляем текст с клавиатурой (HTML)
        await callback.message.answer(full_text, reply_markup=kb, parse_mode=ParseMode.HTML)
        # 2) Опционально отправляем медиа отдельными сообщениями (без клавиатуры)
        if photo_id:
            await callback.message.answer_photo(photo=photo_id, caption="📷 Фото")
        if video_id:
            await callback.message.answer_video(video=video_id, caption="🎥 Видео")
    except Exception as e:
        logger.error(f"Ошибка отправки описания: {e}")
        # Попробуем отправить без HTML как простой текст
        try:
            await callback.message.answer(full_text, reply_markup=kb)
            if photo_id:
                await callback.message.answer_photo(photo=photo_id, caption="📷 Фото")
            if video_id:
                await callback.message.answer_video(video=video_id, caption="🎥 Видео")
        except Exception:
            await callback.message.answer("Описание временно недоступно.")

@router.callback_query(F.data.startswith("back_to_sizes_"))
async def process_back_to_sizes(callback: types.CallbackQuery):
    """Возврат из окна описания к размерам для конкретного товара"""
    product_id = int(callback.data.split("_")[3])
    with DatabaseManager.get_session() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        product_sizes = db.query(ProductSize, Size).join(Size).filter(
            ProductSize.product_id == product_id
        ).all()
    if not product:
        await process_catalog(callback)
        return
    if not product_sizes:
        product_text = f"""🛍️ {product.name}

❌ У этого товара пока нет доступных размеров."""
    else:
        product_text = f"""🛍️ {product.name}

📏 Выберите размер:"""
    kb = get_product_sizes_keyboard(product_id)
    # Если у товара есть фото — покажем карточку с фото, как в process_product
    if getattr(product, 'photo_url', None):
        try:
            await callback.message.delete()
        except Exception:
            pass
        try:
            await callback.message.answer_photo(photo=product.photo_url, caption=product_text, reply_markup=kb)
        except Exception:
            # Если не удалось с фото — отправим текст
            await callback.message.answer(product_text, reply_markup=kb)
    else:
        try:
            await callback.message.edit_text(product_text, reply_markup=kb)
        except Exception:
            await callback.message.answer(product_text, reply_markup=kb)

@router.callback_query(F.data == "close_info")
async def process_close_info(callback: types.CallbackQuery):
    """Закрывает сообщение с описанием"""
    try:
        await callback.message.delete()
    except Exception:
        try:
            await callback.message.edit_text("Закрыто")
        except Exception:
            pass

@router.message(StateFilter(OrderStates.waiting_for_name))
async def handle_name_input(message: types.Message, state: FSMContext):
    """Принимаем ФИО и переходим к телефону"""
    full_name = message.text.strip()
    if len(full_name.split()) < 2:
        await message.answer("Пожалуйста, укажите ФИО полностью (имя и фамилия минимум).")
        return
    await state.update_data(customer_name=full_name)
    await state.set_state(OrderStates.waiting_for_phone)
    await message.answer("Теперь укажите номер телефона (в формате +7XXXXXXXXXX):")

@router.message(StateFilter(OrderStates.waiting_for_phone))
async def handle_phone_input(message: types.Message, state: FSMContext):
    """Принимаем телефон и переходим к адресу"""
    phone = message.text.strip().replace(" ", "")
    # Простая валидация телефона
    if not (phone.startswith("+7") or phone.startswith("8")) or not phone.replace("+", "").isdigit() or len(phone.replace("+", "")) not in (11, 12):
        await message.answer("Похоже, номер неверный. Пример: +79991234567")
        return
    await state.update_data(customer_phone=phone)
    await state.set_state(OrderStates.waiting_for_address)
    await message.answer("Укажите адрес полностью с индексом (город, улица, дом, квартира, индекс):")

@router.message(StateFilter(OrderStates.waiting_for_address))
async def handle_address_input(message: types.Message, state: FSMContext):
    """Принимаем адрес и показываем выбор доставки"""
    address = message.text.strip()
    if len(address) < 10:
        await message.answer("Пожалуйста, укажите полный адрес и индекс.")
        return
    await state.update_data(customer_address=address)
    data = await state.get_data()
    # Покажем сводку и предложим варианты доставки
    summary = "Данные для заказа сохранены:\n\n"
    summary += f"ФИО: {data.get('customer_name')}\n"
    summary += f"Телефон: {data.get('customer_phone')}\n"
    summary += f"Адрес: {address}\n\n"
    summary += "Теперь выберите способ доставки:" 
    await state.set_state(OrderStates.waiting_for_delivery)
    await message.answer(summary, reply_markup=get_delivery_keyboard())

@router.callback_query(F.data.startswith("add_to_cart_"))
async def process_add_to_cart(callback: types.CallbackQuery, state: FSMContext):
    """Выбор размера → собираем данные покупателя → доставка → оплата"""
    parts = callback.data.split("_")
    product_id = int(parts[3])
    size_id = int(parts[4])
    with DatabaseManager.get_session() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        size = db.query(Size).filter(Size.id == size_id).first()
    # Собираем order_data в формате, который уже понимает текущий флоу
    order_data = {
        'user_id': callback.from_user.id,
        'username': callback.from_user.username or "",
        'items': [{
            'product_id': product_id,
            'size_id': size_id,
            'product_name': product.name,
            'size_name': size.name,
            'price': size.price
        }]
    }
    # Сохраняем в состояние и переводим к сбору ФИО
    total_price = size.price
    discount_amount = total_price * COMPANY_INFO['discount_percent'] / 100
    await state.update_data(order_data=order_data, total_price=total_price, discount_amount=discount_amount)
    await state.set_state(OrderStates.waiting_for_name)
    items_text = "Вы выбрали:\n\n"
    items_text += f"• {product.name} · {size.name}\n  Цена: {size.price} ₽\n\n"
    items_text += f"💰 Итого товаров: {total_price} ₽\n"
    items_text += f"🎁 Скидка {COMPANY_INFO['discount_percent']}%: -{discount_amount} ₽\n\n"
    items_text += "Пожалуйста, введите ФИО полностью для оформления заказа:" 
    # Если исходное сообщение было с фото, нужно редактировать подпись, а не текст
    try:
        if getattr(callback.message, 'photo', None):
            await callback.message.edit_caption(caption=items_text)
        else:
            await callback.message.edit_text(items_text)
    except Exception:
        # Если редактирование невозможно (например, старое сообщение), отправим новое
        await callback.message.answer(items_text)

@router.callback_query(F.data == "about")
async def process_about(callback: types.CallbackQuery):
    """Информация о компании"""
    about_text = f"""
Мы — команда мастеров, которые превращают ваши любимые арты и героев в уникальные светильники 🌙  

Каждый ночник мы делаем вручную, с вниманием к деталям.  
🎨 Индивидуальный дизайн  
⚡ Качественные материалы  
🚚 Доставка по всей России и СНГ  

У нас более 1000 довольных клиентов — и мы рады создать что-то и для вас!  
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    
    await safe_edit_message(callback.message, about_text, reply_markup=keyboard)

@router.callback_query(F.data == "faq")
async def process_faq(callback: types.CallbackQuery):
    """FAQ"""
    faq_text = """❓ Часто задаваемые вопросы

❓ Как оформить заказ?  
— Всё просто: выбираете товар → бот помогает с доставкой → получаете ссылку на оплату.  

❓ Какие есть варианты доставки?  
— Почта России и СДЭК (стоимость и сроки бот покажет сразу).  

❓ Можно ли сделать по моему арту?  
— Конечно! Мы любим кастомные заказы ❤️  
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    
    await safe_edit_message(callback.message, faq_text, reply_markup=keyboard)

@router.callback_query(F.data == "features")
async def process_features(callback: types.CallbackQuery):
    """Что умеет бот"""
    features_text = """Я помогу вам:  
✨ выбрать подходящий ночник  
✨ рассчитать доставку в ваш город  
✨ оформить заказ со скидкой  
✨ и даже оплатить онлайн  

Всё быстро, удобно и без лишних шагов 🚀  
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    
    await safe_edit_message(callback.message, features_text, reply_markup=keyboard)

@router.callback_query(F.data == "back_to_main")
async def process_back_to_main(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    # Очищаем состояние заказа
    await state.clear()
    
    welcome_text = f"""
Привет 👋  
Добро пожаловать в {COMPANY_INFO['name']}! Мы создаём индивидуальные ночники и настенные панели по любым вашим любимым героям ✨  

Заказывая здесь, в боте, вы получаете **скидку {COMPANY_INFO['discount_percent']}%** — ведь мы экономим время менеджера 😉  

Выберите, что интересно:
    """
    
    await safe_edit_message(callback.message, welcome_text, reply_markup=get_main_keyboard())

# Обработка заказа от бота каталога
@router.message(F.text.startswith("ORDER_DATA:"))
async def process_order_from_catalog(message: types.Message, state: FSMContext):
    """Обработка данных заказа от бота каталога"""
    try:
        # Парсим данные заказа
        order_data = json.loads(message.text.replace("ORDER_DATA:", ""))
        
        # Сохраняем данные заказа в состоянии
        await state.update_data(order_data=order_data)
        
        # Формируем сообщение с выбранными товарами
        items_text = "Вы выбрали:\n\n"
        total_price = 0
        
        for item in order_data['items']:
            items_text += f"• {item['product_name']} · {item['size_name']}\n"
            items_text += f"  Цена: {item['price']} ₽\n\n"
            total_price += item['price']
        
        items_text += f"💰 Итого товаров: {total_price} ₽\n"
        items_text += f"🎁 Скидка {COMPANY_INFO['discount_percent']}%: -{total_price * COMPANY_INFO['discount_percent'] / 100} ₽\n\n"
        
        discount_amount = total_price * COMPANY_INFO['discount_percent'] / 100
        items_text += f"Хотите рассчитать доставку прямо сейчас?"
        
        await state.update_data(
            total_price=total_price,
            discount_amount=discount_amount
        )
        # Переходим к сбору ФИО
        await state.set_state(OrderStates.waiting_for_name)
        items_text += "\nПожалуйста, введите ФИО полностью для оформления заказа:"
        await message.answer(items_text)
        
    except Exception as e:
        logger.error(f"Ошибка обработки заказа: {e}")
        await message.answer("❌ Произошла ошибка при обработке заказа. Попробуйте еще раз.")

@router.callback_query(F.data == "calculate_delivery")
async def process_calculate_delivery(callback: types.CallbackQuery, state: FSMContext):
    """Расчет доставки"""
    data = await state.get_data()
    if not all(k in data for k in ("customer_name", "customer_phone", "customer_address")):
        # Если пользователь попал сюда без ввода данных — направим его
        await callback.message.answer("Сначала укажем данные для отправки. Пожалуйста, введите ФИО:")
        await state.set_state(OrderStates.waiting_for_name)
        return
    delivery_text = """Варианты доставки

📦 Почта России — 510 ₽ (5-7 дней, до 30 в регионы)  
🚚 СДЭК — 700 ₽ (3-5 дней)  

Выберите удобный вариант 👇"""
    
    await safe_edit_message(callback.message, delivery_text, reply_markup=get_delivery_keyboard())

@router.callback_query(F.data.startswith("delivery_"))
async def process_delivery_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора доставки"""
    delivery_method = callback.data.replace("delivery_", "")
    delivery_info = DELIVERY_METHODS[delivery_method]
    
    # Получаем данные заказа
    data = await state.get_data()
    order_data = data['order_data']
    total_price = data['total_price']
    discount_amount = data['discount_amount']
    customer_name = data.get('customer_name')
    customer_phone = data.get('customer_phone')
    customer_address = data.get('customer_address')
    
    # Рассчитываем итоговую стоимость
    delivery_price = delivery_info['price']
    final_price = total_price - discount_amount + delivery_price
    
    order_summary = f"""Ваш заказ готов ✅  
Товар: {order_data['items'][0]['product_name']} · {order_data['items'][0]['size_name']}  
Стоимость: {total_price} ₽  
Доставка: {delivery_info['name']} · {delivery_price} ₽  
Покупатель: {customer_name}  
Телефон: {customer_phone}  
Адрес: {customer_address}  
-------------------  
Итого к оплате: {final_price:.0f} ₽  

💳 Оплатите заказ по кнопке ниже, и мы сразу запустим его в производство ✨"""
    
    await state.update_data(
        delivery_method=delivery_method,
        delivery_price=delivery_price,
        final_price=final_price
    )
    
    await state.set_state(OrderStates.confirming_order)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", callback_data="create_payment")],
        [InlineKeyboardButton(text="🔙 Изменить доставку", callback_data="calculate_delivery")],
        [InlineKeyboardButton(text="❌ Отменить заказ", callback_data="cancel_order")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")],
        [InlineKeyboardButton(text="🧑‍💼 Индивидуальный заказ", url=get_manager_link())]
    ])
    
    await safe_edit_message(callback.message, order_summary, reply_markup=keyboard)

@router.callback_query(F.data == "create_payment")
async def process_create_payment(callback: types.CallbackQuery, state: FSMContext):
    """Создание платежа"""
    try:
        # Получаем данные заказа
        data = await state.get_data()
        order_data = data['order_data']
        final_price = data['final_price']
        delivery_method = data['delivery_method']
        delivery_price = data['delivery_price']
        customer_name = data.get('customer_name')
        customer_phone = data.get('customer_phone')
        customer_address = data.get('customer_address')
        
        # Создаем заказ в базе данных
        with DatabaseManager.get_session() as db:
            # Вкладываем данные клиента в items[0], чтобы не менять схему БД
            items_enriched = [dict(order_data['items'][0])]
            items_enriched[0]['customer_name'] = customer_name
            items_enriched[0]['customer_phone'] = customer_phone
            items_enriched[0]['customer_address'] = customer_address
            order = Order(
                user_id=callback.from_user.id,
                username=callback.from_user.username or "",
                items=items_enriched,
                delivery_method=delivery_method,
                delivery_price=delivery_price,
                total_price=final_price,
                discount_amount=data['discount_amount'],
                status="pending"
            )
            db.add(order)
            db.commit()
            db.refresh(order)
            
            order_id = order.id
        
        # Создаем платеж в Юкассе
        payment = Payment.create({
            "amount": {"value": f"{final_price:.2f}", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": f"https://t.me/your_bot"},
            "capture": True,
            "description": f"Заказ #{order_id} - Ночники"
        }, str(uuid.uuid4()))
        
        # Обновляем заказ с данными платежа
        with DatabaseManager.get_session() as db:
            db_order = db.query(Order).filter(Order.id == order_id).first()
            db_order.payment_url = payment.confirmation.confirmation_url
            db_order.payment_id = payment.id
            db.commit()
        
        payment_text = f"""💳 Оплата заказа #{order_id}

Сумма к оплате: **{final_price:.0f} ₽**

Нажмите на кнопку ниже для перехода к оплате:"""
        
        # Сохраняем в состоянии, чтобы проверить оплату по кнопке "Я оплатил"
        await state.update_data(order_id=order_id, payment_id=payment.id)

        await safe_edit_message(callback.message, payment_text, reply_markup=get_payment_keyboard(payment.confirmation.confirmation_url))
        
    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
        await callback.message.answer("❌ Произошла ошибка при создании платежа. Попробуйте еще раз.")

@router.callback_query(F.data == "confirm_payment")
async def process_confirm_payment(callback: types.CallbackQuery, state: FSMContext):
    """Проверка статуса оплаты и завершение оформления"""
    try:
        data = await state.get_data()
        order_id = data.get('order_id')
        payment_id = data.get('payment_id')
        if not order_id or not payment_id:
            await callback.message.answer("❌ Не найден активный заказ для проверки оплаты.")
            return
        # Проверяем статус платежа в Юкассе
        payment_obj = Payment.find_one(payment_id)
        status = getattr(payment_obj, 'status', None)
        if status != 'succeeded':
            await callback.message.answer("⏳ Оплата ещё не найдена. Если вы уже оплатили, подождите минутку и нажмите кнопку снова.")
            return
        # Обновляем заказ: помечаем оплаченным
        with DatabaseManager.get_session() as db:
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                order.status = 'paid'
                db.commit()
        # Отправляем благодарность и ссылку менеджера с рефметкой
        manager_link = get_manager_link(order_id)
        thank_text = (
            "Спасибо за заказ ❤️\n"
            f"Ваш ночник уже взяли в работу. Номер заказа: {order_id}\n\n"
            "Перейдите, пожалуйста, по ссылке, чтобы наш менеджер подтвердил ваш заказ:\n\n"
            f"{manager_link}"
        )
        await callback.message.answer(thank_text, reply_markup=get_contact_manager_keyboard(order_id))
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка при подтверждении оплаты: {e}")
        await callback.message.answer("❌ Не получилось проверить оплату. Попробуйте еще раз чуть позже.")

@router.callback_query(F.data == "cancel_order")
async def process_cancel_order(callback: types.CallbackQuery, state: FSMContext):
    """Отмена заказа"""
    await state.clear()
    
    cancel_text = """❌ Заказ отменен

Если передумаете, всегда можете начать заново!"""
    
    await safe_edit_message(callback.message, cancel_text, reply_markup=get_main_keyboard())

# Функция для запуска бота
async def main():
    """Запуск бота"""
    logger.info("Запуск основного бота...")
    # Создаем диспетчер и подключаем роутеры
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(admin_panel.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
