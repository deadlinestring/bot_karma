import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from database import DatabaseManager, Category, Title, Product, Size, ProductSize
from config import BOT2_TOKEN, ADMIN_IDS, BOT1_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT2_TOKEN)
bot1 = Bot(token=BOT1_TOKEN)  # Бот для отправки заказов
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния для FSM
class AdminStates(StatesGroup):
    waiting_category_name = State()
    waiting_title_name = State()
    waiting_title_category = State()
    waiting_product_name = State()
    waiting_product_title = State()
    waiting_product_photo = State()
    waiting_size_name = State()
    waiting_size_price = State()

class CartStates(StatesGroup):
    viewing_product = State()
    viewing_cart = State()

# Класс для работы с корзиной
class Cart:
    def __init__(self):
        self.items = []
    
    def add_item(self, product_id, size_id, product_name, size_name, price):
        """Добавление товара в корзину"""
        item = {
            'product_id': product_id,
            'size_id': size_id,
            'product_name': product_name,
            'size_name': size_name,
            'price': price
        }
        self.items.append(item)
    
    def remove_item(self, index):
        """Удаление товара из корзины"""
        if 0 <= index < len(self.items):
            self.items.pop(index)
    
    def clear(self):
        """Очистка корзины"""
        self.items = []
    
    def get_total_price(self):
        """Получение общей стоимости"""
        return sum(item['price'] for item in self.items)
    
    def is_empty(self):
        """Проверка на пустоту корзины"""
        return len(self.items) == 0

# Словарь для хранения корзин пользователей
user_carts = {}

def get_user_cart(user_id):
    """Получение корзины пользователя"""
    if user_id not in user_carts:
        user_carts[user_id] = Cart()
    return user_carts[user_id]

# Клавиатуры
def get_main_keyboard():
    """Главная клавиатура каталога"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍️ Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
    ])
    return keyboard

def get_categories_keyboard():
    """Клавиатура категорий"""
    with DatabaseManager.get_session() as db:
        categories = db.query(Category).all()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📂 {cat.name}", callback_data=f"category_{cat.id}")] 
        for cat in categories
    ] + [[InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]])
    
    return keyboard

def get_titles_keyboard(category_id):
    """Клавиатура тайтлов для категории"""
    with DatabaseManager.get_session() as db:
        titles = db.query(Title).filter(Title.category_id == category_id).all()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📖 {title.name}", callback_data=f"title_{title.id}")] 
        for title in titles
    ] + [[InlineKeyboardButton(text="🔙 К категориям", callback_data="back_to_categories")]])
    
    return keyboard

def get_products_keyboard(title_id):
    """Клавиатура товаров для тайтла"""
    with DatabaseManager.get_session() as db:
        products = db.query(Product).filter(
            Product.title_id == title_id,
            Product.is_active == True
        ).all()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🛍️ {product.name}", callback_data=f"product_{product.id}")] 
        for product in products
    ] + [[InlineKeyboardButton(text="🔙 К тайтлам", callback_data=f"back_to_titles")]])
    
    return keyboard

def get_product_sizes_keyboard(product_id, user_id):
    """Клавиатура размеров для товара"""
    with DatabaseManager.get_session() as db:
        product_sizes = db.query(ProductSize, Size).join(Size).filter(
            ProductSize.product_id == product_id
        ).all()
    
    # product_sizes возвращает список кортежей (ProductSize, Size)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"📏 {sz.name} - {sz.price}₽",
            callback_data=f"add_to_cart_{product_id}_{sz.id}"
        )]
        for ps, sz in product_sizes
    ] + [[InlineKeyboardButton(text="🔙 К товарам", callback_data="back_to_products")]])
    
    return keyboard

def get_cart_keyboard(user_id):
    """Клавиатура корзины"""
    cart = get_user_cart(user_id)
    
    if cart.is_empty():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
    
    return keyboard

# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    welcome_text = """Привет 👋  
Я — каталог ночников!  

Здесь вы найдёте светильники по любимым аниме, фильмам, играм и вашим личным эскизам 🎨  

Выберите категорию, чтобы начать:"""
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

# Обработчики callback-ов
@dp.callback_query(F.data == "main_menu")
async def process_main_menu(callback: types.CallbackQuery):
    """Главное меню"""
    welcome_text = """Привет 👋  
Я — каталог ночников!  

Здесь вы найдёте светильники по любимым аниме, фильмам, играм и вашим личным эскизам 🎨  

Выберите категорию, чтобы начать:"""
    
    await callback.message.edit_text(welcome_text, reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "catalog")
async def process_catalog(callback: types.CallbackQuery):
    """Показ категорий"""
    catalog_text = """📂 Выберите категорию:

Здесь вы найдете ночники разных тематик и стилей."""
    
    await callback.message.edit_text(catalog_text, reply_markup=get_categories_keyboard())

@dp.callback_query(F.data.startswith("category_"))
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
    
    await callback.message.edit_text(titles_text, reply_markup=get_titles_keyboard(category_id))

@dp.callback_query(F.data.startswith("title_"))
async def process_title(callback: types.CallbackQuery):
    """Показ товаров в тайтле"""
    title_id = int(callback.data.split("_")[1])
    
    with DatabaseManager.get_session() as db:
        title = db.query(Title).filter(Title.id == title_id).first()
        products = db.query(Product).filter(
            Product.title_id == title_id,
            Product.is_active == True
        ).all()
    
    if not products:
        products_text = f"📖 {title.name}\n\nВ этом тайтле пока нет товаров."
    else:
        products_text = f"Вот наши работы по «{title.name}» ✨  \n\nВыберите модель и размер:"
    
    await callback.message.edit_text(products_text, reply_markup=get_products_keyboard(title_id))

@dp.callback_query(F.data.startswith("product_"))
async def process_product(callback: types.CallbackQuery):
    """Показ товара и его размеров"""
    product_id = int(callback.data.split("_")[1])
    
    with DatabaseManager.get_session() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        product_sizes = db.query(ProductSize, Size).join(Size).filter(
            ProductSize.product_id == product_id
        ).all()
    
    if not product_sizes:
        product_text = f"""🛍️ {product.name}

❌ У этого товара пока нет доступных размеров."""
    else:
        product_text = f"""🛍️ {product.name}

📏 Выберите размер:"""
    
    # Отправляем фото товара, если есть
    if product.photo_url:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=product.photo_url,
            caption=product_text,
            reply_markup=get_product_sizes_keyboard(product_id, callback.from_user.id)
        )
    else:
        await callback.message.edit_text(
            product_text,
            reply_markup=get_product_sizes_keyboard(product_id, callback.from_user.id)
        )

@dp.callback_query(F.data.startswith("add_to_cart_"))
async def process_add_to_cart(callback: types.CallbackQuery):
    """Добавление товара в корзину"""
    parts = callback.data.split("_")
    product_id = int(parts[3])
    size_id = int(parts[4])
    
    with DatabaseManager.get_session() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        size = db.query(Size).filter(Size.id == size_id).first()
    
    # Добавляем товар в корзину
    cart = get_user_cart(callback.from_user.id)
    cart.add_item(product_id, size_id, product.name, size.name, size.price)
    
    success_text = f"""✅ {product.name} · {size.name} добавлен в корзину!  

Хотите выбрать ещё или оформить заказ?"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👉 Выбрать ещё", callback_data="catalog")],
        [InlineKeyboardButton(text="👉 Оформить заказ", callback_data="cart")]
    ])
    
    await callback.message.edit_text(success_text, reply_markup=keyboard)

@dp.callback_query(F.data == "cart")
async def process_cart(callback: types.CallbackQuery):
    """Показ корзины"""
    cart = get_user_cart(callback.from_user.id)
    
    if cart.is_empty():
        cart_text = """🛒 Ваша корзина пуста

Добавьте товары из каталога, чтобы оформить заказ."""
    else:
        cart_text = "Ваша корзина 🛒  \n\n"
        
        for i, item in enumerate(cart.items, 1):
            cart_text += f"{i}. {item['product_name']}\n"
            cart_text += f"   📏 {item['size_name']}\n"
            cart_text += f"   💰 {item['price']} ₽\n\n"
        
        cart_text += f"💳 Итого: {cart.get_total_price()} ₽"
    
    await callback.message.edit_text(cart_text, reply_markup=get_cart_keyboard(callback.from_user.id))

@dp.callback_query(F.data == "checkout")
async def process_checkout(callback: types.CallbackQuery):
    """Оформление заказа"""
    cart = get_user_cart(callback.from_user.id)
    
    if cart.is_empty():
        await callback.answer("❌ Корзина пуста!", show_alert=True)
        return
    
    # Формируем данные заказа
    order_data = {
        'user_id': callback.from_user.id,
        'username': callback.from_user.username or "",
        'items': cart.items
    }
    
    try:
        # Отправляем заказ в основной бот
        order_message = f"ORDER_DATA:{json.dumps(order_data)}"
        await bot1.send_message(chat_id=callback.from_user.id, text=order_message)
        
        checkout_text = f"""✅ Заказ отправлен в основной бот!

🛒 Ваши товары:
"""
        
        for item in cart.items:
            checkout_text += f"• {item['product_name']} · {item['size_name']} - {item['price']} ₽\n"
        
        checkout_text += f"\n💳 Итого: {cart.get_total_price()} ₽\n\n"
        checkout_text += "Перейдите в основной бот для завершения заказа и оплаты! 🚀"
        
    except Exception as e:
        logger.error(f"Ошибка отправки заказа в основной бот: {e}")
        checkout_text = """✅ Заказ оформлен!

🛒 Ваши товары:
"""
        
        for item in cart.items:
            checkout_text += f"• {item['product_name']} · {item['size_name']} - {item['price']} ₽\n"
        
        checkout_text += f"\n💳 Итого: {cart.get_total_price()} ₽\n\n"
        checkout_text += "Обратитесь в основной бот для завершения заказа!"
    
    # Очищаем корзину
    cart.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(checkout_text, reply_markup=keyboard)

@dp.callback_query(F.data == "clear_cart")
async def process_clear_cart(callback: types.CallbackQuery):
    """Очистка корзины"""
    cart = get_user_cart(callback.from_user.id)
    cart.clear()
    
    clear_text = """🗑️ Корзина очищена

Все товары удалены из корзины."""
    
    await callback.message.edit_text(clear_text, reply_markup=get_main_keyboard())

# Обработчики навигации
@dp.callback_query(F.data == "back_to_categories")
async def process_back_to_categories(callback: types.CallbackQuery):
    """Возврат к категориям"""
    catalog_text = """📂 Выберите категорию:

Здесь вы найдете ночники разных тематик и стилей."""
    
    await callback.message.edit_text(catalog_text, reply_markup=get_categories_keyboard())

@dp.callback_query(F.data == "back_to_titles")
async def process_back_to_titles(callback: types.CallbackQuery):
    """Возврат к тайтлам"""
    # Здесь нужно получить category_id из контекста
    # Для простоты показываем категории
    catalog_text = """📂 Выберите категорию:

Здесь вы найдете ночники разных тематик и стилей."""
    
    await callback.message.edit_text(catalog_text, reply_markup=get_categories_keyboard())

@dp.callback_query(F.data == "back_to_products")
async def process_back_to_products(callback: types.CallbackQuery):
    """Возврат к товарам"""
    # Здесь нужно получить title_id из контекста
    # Для простоты показываем категории
    catalog_text = """📂 Выберите категорию:

Здесь вы найдете ночники разных тематик и стилей."""
    
    await callback.message.edit_text(catalog_text, reply_markup=get_categories_keyboard())

# Админ команды
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Админ панель"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    # Импортируем админ панель
    import admin_panel
    await admin_panel.handle_admin_start(message)

# Функция для запуска бота
async def main():
    """Запуск бота каталога"""
    logger.info("Запуск бота каталога...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
