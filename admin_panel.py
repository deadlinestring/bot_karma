import logging
from aiogram import Bot, types, F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import DatabaseManager, Category, Title, Product, Size, ProductSize, Order, Settings
from config import ADMIN_IDS, BOT2_TOKEN

# Роутер админ-панели (подключается в главный dp)
router = Router()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для FSM админ панели
class AdminStates(StatesGroup):
    waiting_category_name = State()
    waiting_title_name = State()
    waiting_title_category = State()
    waiting_product_name = State()
    waiting_product_title = State()
    waiting_product_photo = State()
    waiting_size_name = State()
    waiting_size_price = State()
    waiting_product_for_size = State()
    waiting_size_for_product = State()
    waiting_new_product_name = State()
    waiting_new_product_photo = State()
    waiting_new_category_name = State()
    waiting_new_title_name = State()
    waiting_edit_size_name = State()
    waiting_edit_size_price = State()
    waiting_description_text = State()
    waiting_description_photo = State()
    waiting_description_video = State()

def is_admin(user_id):
    """Проверка прав администратора"""
    return user_id in ADMIN_IDS
def get_admin_keyboard():
    """Главная клавиатура админ панели"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 Добавить категорию", callback_data="admin_categories")],
        [InlineKeyboardButton(text="🎭 Добавить тайтл", callback_data="admin_titles")],
        [InlineKeyboardButton(text="🛍️ Управление товарами", callback_data="admin_products")],
        [InlineKeyboardButton(text="📏 Управление размерами", callback_data="admin_sizes")],
        [InlineKeyboardButton(text="📝 Описание товаров", callback_data="admin_desc")],
        [InlineKeyboardButton(text="🔙 Выход", callback_data="exit_admin")]
    ])
    
    return keyboard

def get_categories_admin_keyboard():
    """Клавиатура управления категориями"""
    with DatabaseManager.get_session() as db:
        categories = db.query(Category).all()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить категорию", callback_data="add_category")],
        *[[InlineKeyboardButton(text=f"📂 {cat.name}", callback_data=f"edit_category_{cat.id}")] 
          for cat in categories],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    
    return keyboard

def get_titles_admin_keyboard():
    """Клавиатура управления тайтлами"""
    with DatabaseManager.get_session() as db:
        titles = db.query(Title).all()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить тайтл", callback_data="add_title")],
        *[[InlineKeyboardButton(text=f"📖 {title.name}", callback_data=f"edit_title_{title.id}")] 
          for title in titles],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    
    return keyboard

def get_category_edit_keyboard(category_id: int):
    """Клавиатура редактирования категории"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Переименовать", callback_data=f"rename_category_{category_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_category_{category_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_categories")]
    ])
    return keyboard

def get_title_edit_keyboard(title_id: int):
    """Клавиатура редактирования тайтла"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Переименовать", callback_data=f"rename_title_{title_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_title_{title_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_titles")]
    ])
    return keyboard

def get_products_admin_keyboard():
    """Клавиатура управления товарами"""
    with DatabaseManager.get_session() as db:
        products = db.query(Product).all()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_product")],
        *[[InlineKeyboardButton(
            text=f"{'🟢' if (product.is_active or False) else '🔴'} {product.name}",
            callback_data=f"edit_product_{product.id}")]
          for product in products],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    
    return keyboard

def get_product_edit_keyboard(product_id: int, is_active: bool):
    """Клавиатура редактирования конкретного товара"""
    toggle_text = "🔓 Включить" if not is_active else "🚫 Выключить"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Переименовать", callback_data=f"rename_product_{product_id}")],
        [InlineKeyboardButton(text="🖼️ Изменить фото", callback_data=f"change_photo_{product_id}")],
        [InlineKeyboardButton(text=f"{toggle_text}", callback_data=f"toggle_active_{product_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_product_{product_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_products")]
    ])
    return keyboard

def get_sizes_admin_keyboard():
    """Клавиатура управления размерами"""
    with DatabaseManager.get_session() as db:
        sizes = db.query(Size).all()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить размер", callback_data="add_size")],
        *[[InlineKeyboardButton(text=f"📏 {size.name} - {size.price}₽", callback_data=f"edit_size_{size.id}")] 
          for size in sizes],
        [InlineKeyboardButton(text="🔗 Связать товар с размером", callback_data="link_product_size")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    
    return keyboard

DEFAULT_SIZES = [
    ("Стандарт 20см на пластиковой подставке", 1990.0),
    ("Стандарт 25см на пластиковой подставке", 2490.0),
    ("Премиум 25см на деревянной подставке", 3490.0),
    ("Премиум 30см на деревянной подставке", 4390.0),
    ("Настенная панель 30см", 4490.0),
    ("Настенная панель 35см", 4790.0),
    ("Настенная панель 40см", 5390.0),
    ("Настенная панель 45см", 5890.0),
    ("Настенная панель 50см", 6390.0),
    ("Настенная панель 55см", 7090.0),
]

def ensure_default_sizes():
    """Создает дефолтные размеры, если их нет"""
    with DatabaseManager.get_session() as db:
        existing = {s.name for s in db.query(Size).all()}
        created = 0
        for name, price in DEFAULT_SIZES:
            if name not in existing:
                db.add(Size(name=name, price=price))
                created += 1
        if created:
            db.commit()

# Обработчики админ команд
@router.message(Command("admin"))
async def handle_admin_start(message: types.Message):
    """Обработчик команды /admin"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    # Гарантируем наличие дефолтных размеров
    ensure_default_sizes()
    
    admin_text = """Привет, админ 👋  
Что будем делать?"""
    
    await message.answer(admin_text, reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "admin_back")
async def process_admin_back(callback: types.CallbackQuery):
    """Возврат в админ панель"""
    admin_text = """Привет, админ 👋  
Что будем делать?"""
    
    await callback.message.edit_text(admin_text, reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "admin_categories")
async def process_admin_categories(callback: types.CallbackQuery):
    """Управление категориями"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    
    categories_text = """📂 Управление категориями

Выберите действие:"""
    
    await callback.message.edit_text(categories_text, reply_markup=get_categories_admin_keyboard())

@router.callback_query(F.data == "admin_titles")
async def process_admin_titles(callback: types.CallbackQuery):
    """Управление тайтлами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    
    titles_text = """🎭 Управление тайтлами

Выберите действие:"""
    
    await callback.message.edit_text(titles_text, reply_markup=get_titles_admin_keyboard())

@router.callback_query(F.data == "admin_products")
async def process_admin_products(callback: types.CallbackQuery):
    """Управление товарами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    
    products_text = """💡 Управление товарами

Выберите действие:"""
    
    await callback.message.edit_text(products_text, reply_markup=get_products_admin_keyboard())

# ==============================
# Описание товаров: текст и медиа
# ==============================
def get_desc_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить текст", callback_data="desc_edit_text")],
        [InlineKeyboardButton(text="🖼️ Установить фото", callback_data="desc_set_photo"), InlineKeyboardButton(text="🗑️ Удалить фото", callback_data="desc_clear_photo")],
        [InlineKeyboardButton(text="🎬 Установить видео", callback_data="desc_set_video"), InlineKeyboardButton(text="🗑️ Удалить видео", callback_data="desc_clear_video")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    return keyboard

@router.callback_query(F.data == "admin_desc")
async def process_admin_desc(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    with DatabaseManager.get_session() as db:
        s = db.query(Settings).filter(Settings.id == 1).first()
    text = s.description_text if s and s.description_text else "Текст описания не задан."
    media_info = []
    if s and s.desc_photo_file_id:
        media_info.append("Фото: установлено")
    else:
        media_info.append("Фото: нет")
    if s and s.desc_video_file_id:
        media_info.append("Видео: установлено")
    else:
        media_info.append("Видео: нет")
    summary = "📝 Описание товаров (спойлер)\n\n" + text[:700] + ("…" if len(text) > 700 else "") + "\n\n" + "\n".join(media_info)
    await callback.message.edit_text(summary, reply_markup=get_desc_keyboard())

@router.callback_query(F.data == "desc_edit_text")
async def process_desc_edit_text(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_description_text)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]])
    await callback.message.edit_text("✏️ Пришлите новый текст описания (можно несколькими сообщениями, завершите последним сообщением). Отправьте одно сообщение с полным текстом:", reply_markup=kb)

@router.message(AdminStates.waiting_description_text)
async def process_desc_text_message(message: types.Message, state: FSMContext):
    text = message.text or ""
    with DatabaseManager.get_session() as db:
        s = db.query(Settings).filter(Settings.id == 1).first()
        if not s:
            s = Settings(id=1, description_text=text)
            db.add(s)
        else:
            s.description_text = text
        db.commit()
    await state.clear()
    await message.answer("✅ Текст описания обновлен.", reply_markup=get_desc_keyboard())

@router.callback_query(F.data == "desc_set_photo")
async def process_desc_set_photo(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_description_photo)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]])
    await callback.message.edit_text("🖼️ Пришлите фото для описания:", reply_markup=kb)

@router.message(AdminStates.waiting_description_photo, F.photo)
async def process_desc_photo_message(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    with DatabaseManager.get_session() as db:
        s = db.query(Settings).filter(Settings.id == 1).first()
        if not s:
            s = Settings(id=1, desc_photo_file_id=file_id)
            db.add(s)
        else:
            s.desc_photo_file_id = file_id
        db.commit()
    await state.clear()
    await message.answer("✅ Фото для описания установлено.", reply_markup=get_desc_keyboard())

@router.callback_query(F.data == "desc_clear_photo")
async def process_desc_clear_photo(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    with DatabaseManager.get_session() as db:
        s = db.query(Settings).filter(Settings.id == 1).first()
        if s:
            s.desc_photo_file_id = None
            db.commit()
    await callback.message.edit_text("✅ Фото для описания удалено.", reply_markup=get_desc_keyboard())

@router.callback_query(F.data == "desc_set_video")
async def process_desc_set_video(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_description_video)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]])
    await callback.message.edit_text("🎬 Пришлите видео для описания:", reply_markup=kb)

@router.message(AdminStates.waiting_description_video, F.video)
async def process_desc_video_message(message: types.Message, state: FSMContext):
    file_id = message.video.file_id
    with DatabaseManager.get_session() as db:
        s = db.query(Settings).filter(Settings.id == 1).first()
        if not s:
            s = Settings(id=1, desc_video_file_id=file_id)
            db.add(s)
        else:
            s.desc_video_file_id = file_id
        db.commit()
    await state.clear()
    await message.answer("✅ Видео для описания установлено.", reply_markup=get_desc_keyboard())

@router.callback_query(F.data == "desc_clear_video")
async def process_desc_clear_video(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    with DatabaseManager.get_session() as db:
        s = db.query(Settings).filter(Settings.id == 1).first()
        if s:
            s.desc_video_file_id = None
            db.commit()
    await callback.message.edit_text("✅ Видео для описания удалено.", reply_markup=get_desc_keyboard())

# ==============================
# Категории: редактирование/удаление
# ==============================
@router.callback_query(F.data.startswith("edit_category_"))
async def process_edit_category(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    category_id = int(callback.data.split("_")[2])
    with DatabaseManager.get_session() as db:
        cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        await callback.answer("❌ Категория не найдена.", show_alert=True)
        return
    text = f"📂 Категория: {cat.name}"
    await callback.message.edit_text(text, reply_markup=get_category_edit_keyboard(category_id))

@router.callback_query(F.data.startswith("rename_category_"))
async def process_rename_category(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    category_id = int(callback.data.split("_")[2])
    await state.update_data(edit_category_id=category_id)
    await state.set_state(AdminStates.waiting_new_category_name)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]])
    await callback.message.edit_text("✏️ Введите новое название категории:", reply_markup=keyboard)

@router.message(AdminStates.waiting_new_category_name)
async def process_new_category_name(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    data = await state.get_data()
    category_id = data.get('edit_category_id')
    if not category_id:
        await message.answer("❌ Не удалось определить категорию. Попробуйте снова.")
        await state.clear()
        return
    with DatabaseManager.get_session() as db:
        cat = db.query(Category).filter(Category.id == category_id).first()
        if not cat:
            await message.answer("❌ Категория не найдена.")
            await state.clear()
            return
        cat.name = new_name
        db.commit()
    await state.clear()
    await message.answer(f"✅ Категория переименована: {new_name}", reply_markup=get_category_edit_keyboard(category_id))

@router.callback_query(F.data.startswith("delete_category_"))
async def process_delete_category(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    category_id = int(callback.data.split("_")[2])
    try:
        with DatabaseManager.get_session() as db:
            # Находим все тайтлы категории
            titles = db.query(Title).filter(Title.category_id == category_id).all()
            for title in titles:
                # Находим и удаляем товары и их размеры
                products = db.query(Product).filter(Product.title_id == title.id).all()
                for product in products:
                    db.query(ProductSize).filter(ProductSize.product_id == product.id).delete()
                    db.delete(product)
                # Удаляем тайтл
                db.delete(title)
            # Удаляем категорию
            deleted = db.query(Category).filter(Category.id == category_id).delete()
            db.commit()
        if deleted:
            await callback.message.edit_text("✅ Категория удалена.", reply_markup=get_categories_admin_keyboard())
        else:
            await callback.message.edit_text("❌ Категория не найдена.", reply_markup=get_categories_admin_keyboard())
    except Exception as e:
        logger.error(f"Ошибка удаления категории: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при удалении категории.", reply_markup=get_categories_admin_keyboard())

# ==============================
# Тайтлы: редактирование/удаление
# ==============================
@router.callback_query(F.data.startswith("edit_title_"))
async def process_edit_title(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    title_id = int(callback.data.split("_")[2])
    with DatabaseManager.get_session() as db:
        title = db.query(Title).filter(Title.id == title_id).first()
    if not title:
        await callback.answer("❌ Тайтл не найден.", show_alert=True)
        return
    text = f"📖 Тайтл: {title.name}"
    await callback.message.edit_text(text, reply_markup=get_title_edit_keyboard(title_id))

@router.callback_query(F.data.startswith("rename_title_"))
async def process_rename_title(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    title_id = int(callback.data.split("_")[2])
    await state.update_data(edit_title_id=title_id)
    await state.set_state(AdminStates.waiting_new_title_name)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]])
    await callback.message.edit_text("✏️ Введите новое название тайтла:", reply_markup=keyboard)

@router.message(AdminStates.waiting_new_title_name)
async def process_new_title_name(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    data = await state.get_data()
    title_id = data.get('edit_title_id')
    if not title_id:
        await message.answer("❌ Не удалось определить тайтл. Попробуйте снова.")
        await state.clear()
        return
    with DatabaseManager.get_session() as db:
        title = db.query(Title).filter(Title.id == title_id).first()
        if not title:
            await message.answer("❌ Тайтл не найден.")
            await state.clear()
            return
        title.name = new_name
        db.commit()
    await state.clear()
    await message.answer(f"✅ Тайтл переименован: {new_name}", reply_markup=get_title_edit_keyboard(title_id))

@router.callback_query(F.data.startswith("delete_title_"))
async def process_delete_title(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    title_id = int(callback.data.split("_")[2])
    try:
        with DatabaseManager.get_session() as db:
            # Удалить товары и их размеры
            products = db.query(Product).filter(Product.title_id == title_id).all()
            for product in products:
                db.query(ProductSize).filter(ProductSize.product_id == product.id).delete()
                db.delete(product)
            # Удалить тайтл
            deleted = db.query(Title).filter(Title.id == title_id).delete()
            db.commit()
        if deleted:
            await callback.message.edit_text("✅ Тайтл удален.", reply_markup=get_titles_admin_keyboard())
        else:
            await callback.message.edit_text("❌ Тайтл не найден.", reply_markup=get_titles_admin_keyboard())
    except Exception as e:
        logger.error(f"Ошибка удаления тайтла: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при удалении тайтла.", reply_markup=get_titles_admin_keyboard())

@router.callback_query(F.data.startswith("edit_product_"))
async def process_edit_product(callback: types.CallbackQuery):
    """Открыть меню редактирования конкретного товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    product_id = int(callback.data.split("_")[2])
    with DatabaseManager.get_session() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return
    text = f"🛍️ {product.name}\n\nСтатус: {'активен' if product.is_active else 'выключен'}"
    await callback.message.edit_text(text, reply_markup=get_product_edit_keyboard(product.id, product.is_active))

@router.callback_query(F.data.startswith("toggle_active_"))
async def process_toggle_active(callback: types.CallbackQuery):
    """Включить/выключить товар"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    product_id = int(callback.data.split("_")[2])
    with DatabaseManager.get_session() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            await callback.answer("❌ Товар не найден.", show_alert=True)
            return
        product.is_active = not bool(product.is_active)
        db.commit()
        is_active = product.is_active
        name = product.name
    await callback.message.edit_text(
        f"🛍️ {name}\n\nСтатус: {'активен' if is_active else 'выключен'}",
        reply_markup=get_product_edit_keyboard(product_id, is_active)
    )

@router.callback_query(F.data.startswith("rename_product_"))
async def process_rename_product(callback: types.CallbackQuery, state: FSMContext):
    """Запросить новое имя товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    product_id = int(callback.data.split("_")[2])
    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.waiting_new_product_name)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]])
    await callback.message.edit_text("✏️ Введите новое название товара:", reply_markup=keyboard)

@router.message(AdminStates.waiting_new_product_name)
async def process_new_product_name(message: types.Message, state: FSMContext):
    """Применить новое имя товара"""
    new_name = message.text.strip()
    data = await state.get_data()
    product_id = data.get('edit_product_id')
    if not product_id:
        await message.answer("❌ Не удалось определить товар. Попробуйте снова.")
        await state.clear()
        return
    with DatabaseManager.get_session() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            await message.answer("❌ Товар не найден.")
            await state.clear()
            return
        product.name = new_name
        db.commit()
        is_active = product.is_active
    await state.clear()
    await message.answer(
        f"✅ Название обновлено: {new_name}",
        reply_markup=get_product_edit_keyboard(product_id, is_active)
    )

@router.callback_query(F.data.startswith("change_photo_"))
async def process_change_photo(callback: types.CallbackQuery, state: FSMContext):
    """Запросить новое фото товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    product_id = int(callback.data.split("_")[2])
    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.waiting_new_product_photo)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]])
    await callback.message.edit_text("🖼️ Отправьте новое фото товара:", reply_markup=keyboard)

@router.message(AdminStates.waiting_new_product_photo, F.photo)
async def process_new_product_photo(message: types.Message, state: FSMContext):
    """Применить новое фото товара"""
    photo = message.photo[-1]
    photo_file_id = photo.file_id
    data = await state.get_data()
    product_id = data.get('edit_product_id')
    if not product_id:
        await message.answer("❌ Не удалось определить товар. Попробуйте снова.")
        await state.clear()
        return
    with DatabaseManager.get_session() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            await message.answer("❌ Товар не найден.")
            await state.clear()
            return
        product.photo_url = photo_file_id
        db.commit()
        is_active = product.is_active
        name = product.name
    await state.clear()
    await message.answer(
        f"✅ Фото для товара '{name}' обновлено.",
        reply_markup=get_product_edit_keyboard(product_id, is_active)
    )

@router.callback_query(F.data.startswith("delete_product_"))
async def process_delete_product(callback: types.CallbackQuery):
    """Удалить товар и его связи размеров"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    product_id = int(callback.data.split("_")[2])
    try:
        with DatabaseManager.get_session() as db:
            # Удаляем связи размеров
            db.query(ProductSize).filter(ProductSize.product_id == product_id).delete()
            # Удаляем товар
            deleted = db.query(Product).filter(Product.id == product_id).delete()
            db.commit()
        if deleted:
            await callback.message.edit_text("✅ Товар удален.", reply_markup=get_products_admin_keyboard())
        else:
            await callback.message.edit_text("❌ Товар не найден.", reply_markup=get_products_admin_keyboard())
    except Exception as e:
        logger.error(f"Ошибка удаления товара: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при удалении товара.", reply_markup=get_products_admin_keyboard())

@router.callback_query(F.data == "admin_sizes")
async def process_admin_sizes(callback: types.CallbackQuery):
    """Управление размерами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    
    sizes_text = """📏 Управление размерами

Выберите действие:"""
    
    await callback.message.edit_text(sizes_text, reply_markup=get_sizes_admin_keyboard())

# Добавление категории
@router.callback_query(F.data == "add_category")
async def process_add_category(callback: types.CallbackQuery, state: FSMContext):
    """Добавление новой категории"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_category_name)
    
    add_text = """➕ Добавление категории

Введите название новой категории:"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]
    ])
    
    await callback.message.edit_text(add_text, reply_markup=keyboard)

@router.message(AdminStates.waiting_category_name)
async def process_category_name(message: types.Message, state: FSMContext):
    """Обработка названия категории"""
    category_name = message.text.strip()
    
    try:
        with DatabaseManager.get_session() as db:
            # Проверяем, не существует ли уже такая категория
            existing = db.query(Category).filter(Category.name == category_name).first()
            if existing:
                await message.answer("❌ Категория с таким названием уже существует!")
                return
            
            # Создаем новую категорию
            category = Category(name=category_name)
            db.add(category)
            db.commit()
            
            await message.answer(f"✅ Категория '{category_name}' успешно добавлена!")
            
    except Exception as e:
        logger.error(f"Ошибка добавления категории: {e}")
        await message.answer("❌ Произошла ошибка при добавлении категории.")
    
    await state.clear()

# Добавление тайтла
@router.callback_query(F.data == "add_title")
async def process_add_title(callback: types.CallbackQuery, state: FSMContext):
    """Добавление нового тайтла"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    
    # Получаем список категорий для выбора
    with DatabaseManager.get_session() as db:
        categories = db.query(Category).all()
    
    if not categories:
        await callback.answer("❌ Сначала добавьте категории!", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📂 {cat.name}", callback_data=f"select_category_{cat.id}")] 
        for cat in categories
    ] + [[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]])
    
    add_text = """➕ Добавление тайтла

Выберите категорию для нового тайтла:"""
    
    await callback.message.edit_text(add_text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("select_category_"))
async def process_select_category_for_title(callback: types.CallbackQuery, state: FSMContext):
    """Выбор категории для тайтла"""
    category_id = int(callback.data.split("_")[2])
    
    await state.update_data(category_id=category_id)
    await state.set_state(AdminStates.waiting_title_name)
    
    add_text = """➕ Добавление тайтла

Введите название нового тайтла:"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]
    ])
    
    await callback.message.edit_text(add_text, reply_markup=keyboard)

@router.message(AdminStates.waiting_title_name)
async def process_title_name(message: types.Message, state: FSMContext):
    """Обработка названия тайтла"""
    title_name = message.text.strip()
    data = await state.get_data()
    category_id = data['category_id']
    
    try:
        with DatabaseManager.get_session() as db:
            # Создаем новый тайтл
            title = Title(name=title_name, category_id=category_id)
            db.add(title)
            db.commit()
            
            await message.answer(f"✅ Тайтл '{title_name}' успешно добавлен!")
            
    except Exception as e:
        logger.error(f"Ошибка добавления тайтла: {e}")
        await message.answer("❌ Произошла ошибка при добавлении тайтла.")
    
    await state.clear()

# Добавление товара
@router.callback_query(F.data == "add_product")
async def process_add_product(callback: types.CallbackQuery, state: FSMContext):
    """Добавление нового товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    
    # Получаем список тайтлов для выбора
    with DatabaseManager.get_session() as db:
        titles = db.query(Title).all()
    
    if not titles:
        await callback.answer("❌ Сначала добавьте тайтлы!", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📖 {title.name}", callback_data=f"select_title_{title.id}")] 
        for title in titles
    ] + [[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]])
    
    add_text = """➕ Добавление товара

Выберите тайтл для нового товара:"""
    
    await callback.message.edit_text(add_text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("select_title_"))
async def process_select_title_for_product(callback: types.CallbackQuery, state: FSMContext):
    """Выбор тайтла для товара"""
    title_id = int(callback.data.split("_")[2])
    
    await state.update_data(title_id=title_id)
    await state.set_state(AdminStates.waiting_product_name)
    
    add_text = """➕ Добавление товара

Введите название нового товара:"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]
    ])
    
    await callback.message.edit_text(add_text, reply_markup=keyboard)

@router.message(AdminStates.waiting_product_name)
async def process_product_name(message: types.Message, state: FSMContext):
    """Обработка названия товара"""
    product_name = message.text.strip()
    data = await state.get_data()
    title_id = data['title_id']
    
    await state.update_data(product_name=product_name)
    await state.set_state(AdminStates.waiting_product_photo)
    
    add_text = """➕ Добавление товара

Теперь отправьте фото товара или нажмите "Пропустить":"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_photo")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]
    ])
    
    await message.answer(add_text, reply_markup=keyboard)

@router.message(AdminStates.waiting_product_photo, F.photo)
async def process_product_photo(message: types.Message, state: FSMContext):
    """Обработка фото товара"""
    photo = message.photo[-1]  # Берем фото наибольшего размера
    photo_file_id = photo.file_id
    
    data = await state.get_data()
    product_name = data['product_name']
    title_id = data['title_id']
    
    try:
        with DatabaseManager.get_session() as db:
            # Создаем новый товар
            product = Product(name=product_name, title_id=title_id, photo_url=photo_file_id, is_active=True)
            db.add(product)
            db.commit()
            db.refresh(product)
            # Автопривязка всех размеров к новому товару
            sizes = db.query(Size).all()
            for sz in sizes:
                link = ProductSize(product_id=product.id, size_id=sz.id)
                db.add(link)
            db.commit()
            
            await message.answer(f"✅ Товар '{product_name}' успешно добавлен!")
            
    except Exception as e:
        logger.error(f"Ошибка добавления товара: {e}")
        await message.answer("❌ Произошла ошибка при добавлении товара.")
    
    await state.clear()

@router.callback_query(F.data == "skip_photo")
async def process_skip_photo(callback: types.CallbackQuery, state: FSMContext):
    """Пропуск добавления фото"""
    data = await state.get_data()
    product_name = data['product_name']
    title_id = data['title_id']
    
    try:
        with DatabaseManager.get_session() as db:
            # Создаем новый товар без фото
            product = Product(name=product_name, title_id=title_id, is_active=True)
            db.add(product)
            db.commit()
            db.refresh(product)
            # Автопривязка всех размеров к новому товару
            sizes = db.query(Size).all()
            for sz in sizes:
                link = ProductSize(product_id=product.id, size_id=sz.id)
                db.add(link)
            db.commit()
            
            await callback.message.edit_text(f"✅ Товар '{product_name}' успешно добавлен!")
            
    except Exception as e:
        logger.error(f"Ошибка добавления товара: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при добавлении товара.")
    
    await state.clear()

# Добавление размера
@router.callback_query(F.data == "add_size")
async def process_add_size(callback: types.CallbackQuery, state: FSMContext):
    """Добавление нового размера"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_size_name)
    
    add_text = """➕ Добавление размера

Введите название нового размера (например: "Стандарт 25см на пластиковой подставке"):"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]
    ])
    
    await callback.message.edit_text(add_text, reply_markup=keyboard)

@router.message(AdminStates.waiting_size_name)
async def process_size_name(message: types.Message, state: FSMContext):
    """Обработка названия размера"""
    size_name = message.text.strip()
    
    await state.update_data(size_name=size_name)
    await state.set_state(AdminStates.waiting_size_price)
    
    add_text = """➕ Добавление размера

Введите цену для этого размера (только число, без валюты):"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]
    ])
    
    await message.answer(add_text, reply_markup=keyboard)

@router.message(AdminStates.waiting_size_price)
async def process_size_price(message: types.Message, state: FSMContext):
    """Обработка цены размера"""
    try:
        price = float(message.text.strip())
        data = await state.get_data()
        size_name = data['size_name']
        
        with DatabaseManager.get_session() as db:
            # Создаем новый размер
            size = Size(name=size_name, price=price)
            db.add(size)
            db.commit()
            db.refresh(size)
            # Автопривязка нового размера ко всем существующим товарам
            products = db.query(Product).all()
            for product in products:
                link = ProductSize(product_id=product.id, size_id=size.id)
                db.add(link)
            db.commit()
            
            await message.answer(f"✅ Размер '{size_name}' с ценой {price}₽ успешно добавлен!")
            
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную цену (число).")
        return
    except Exception as e:
        logger.error(f"Ошибка добавления размера: {e}")
        await message.answer("❌ Произошла ошибка при добавлении размера.")
    
    await state.clear()

# Связывание товара с размером
@router.callback_query(F.data == "link_product_size")
async def process_link_product_size(callback: types.CallbackQuery, state: FSMContext):
    """Связывание товара с размером"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    
    # Получаем список товаров для выбора
    with DatabaseManager.get_session() as db:
        products = db.query(Product).filter(Product.is_active == True).all()
    
    if not products:
        await callback.answer("❌ Сначала добавьте товары!", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🛍️ {product.name}", callback_data=f"select_product_{product.id}")] 
        for product in products
    ] + [[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]])
    
    link_text = """🔗 Связывание товара с размером

Выберите товар:"""
    
    await callback.message.edit_text(link_text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("select_product_"))
async def process_select_product_for_size(callback: types.CallbackQuery, state: FSMContext):
    """Выбор товара для связывания с размером"""
    product_id = int(callback.data.split("_")[2])
    
    # Получаем список размеров для выбора
    with DatabaseManager.get_session() as db:
        sizes = db.query(Size).all()
    
    if not sizes:
        await callback.answer("❌ Сначала добавьте размеры!", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📏 {size.name} - {size.price}₽", callback_data=f"select_size_{size.id}")] 
        for size in sizes
    ] + [[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]])
    
    await state.update_data(product_id=product_id)
    
    link_text = """🔗 Связывание товара с размером

Выберите размер:"""
    
    await callback.message.edit_text(link_text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("select_size_"))
async def process_select_size_for_product(callback: types.CallbackQuery, state: FSMContext):
    """Выбор размера для связывания с товаром"""
    size_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    product_id = data['product_id']
    
    try:
        with DatabaseManager.get_session() as db:
            # Проверяем, не связаны ли уже товар и размер
            existing = db.query(ProductSize).filter(
                ProductSize.product_id == product_id,
                ProductSize.size_id == size_id
            ).first()
            
            if existing:
                await callback.answer("❌ Этот товар уже связан с данным размером!", show_alert=True)
                return
            
            # Создаем связь
            product_size = ProductSize(product_id=product_id, size_id=size_id)
            db.add(product_size)
            db.commit()
            
            # Получаем названия для подтверждения
            product = db.query(Product).filter(Product.id == product_id).first()
            size = db.query(Size).filter(Size.id == size_id).first()
            
            await callback.message.edit_text(
                f"✅ Товар '{product.name}' успешно связан с размером '{size.name}'!"
            )
            
    except Exception as e:
        logger.error(f"Ошибка связывания товара с размером: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при связывании товара с размером.")
    
    await state.clear()

# Редактирование размеров
def get_size_edit_keyboard(size_id: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Переименовать", callback_data=f"rename_size_{size_id}")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"reprice_size_{size_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_size_{size_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_sizes")]
    ])
    return keyboard

@router.callback_query(F.data.startswith("edit_size_"))
async def process_edit_size(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    size_id = int(callback.data.split("_")[2])
    with DatabaseManager.get_session() as db:
        size = db.query(Size).filter(Size.id == size_id).first()
    if not size:
        await callback.answer("❌ Размер не найден.", show_alert=True)
        return
    text = f"📏 Размер: {size.name}\nЦена: {size.price}₽"
    await callback.message.edit_text(text, reply_markup=get_size_edit_keyboard(size_id))

@router.callback_query(F.data.startswith("rename_size_"))
async def process_rename_size(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    size_id = int(callback.data.split("_")[2])
    await state.update_data(edit_size_id=size_id)
    await state.set_state(AdminStates.waiting_edit_size_name)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]])
    await callback.message.edit_text("✏️ Введите новое название размера:", reply_markup=keyboard)

@router.message(AdminStates.waiting_edit_size_name)
async def process_new_size_name(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    data = await state.get_data()
    size_id = data.get('edit_size_id')
    if not size_id:
        await message.answer("❌ Не удалось определить размер. Попробуйте снова.")
        await state.clear()
        return
    with DatabaseManager.get_session() as db:
        size = db.query(Size).filter(Size.id == size_id).first()
        if not size:
            await message.answer("❌ Размер не найден.")
            await state.clear()
            return
        size.name = new_name
        db.commit()
    await state.clear()
    await message.answer(f"✅ Название размера обновлено: {new_name}", reply_markup=get_size_edit_keyboard(size_id))

@router.callback_query(F.data.startswith("reprice_size_"))
async def process_reprice_size(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    size_id = int(callback.data.split("_")[2])
    await state.update_data(edit_size_id=size_id)
    await state.set_state(AdminStates.waiting_edit_size_price)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin")]])
    await callback.message.edit_text("💰 Введите новую цену (число):", reply_markup=keyboard)

@router.message(AdminStates.waiting_edit_size_price)
async def process_new_size_price(message: types.Message, state: FSMContext):
    try:
        new_price = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную цену (число).")
        return
    data = await state.get_data()
    size_id = data.get('edit_size_id')
    if not size_id:
        await message.answer("❌ Не удалось определить размер. Попробуйте снова.")
        await state.clear()
        return
    with DatabaseManager.get_session() as db:
        size = db.query(Size).filter(Size.id == size_id).first()
        if not size:
            await message.answer("❌ Размер не найден.")
            await state.clear()
            return
        size.price = new_price
        db.commit()
    await state.clear()
    await message.answer(f"✅ Цена размера обновлена: {new_price}₽", reply_markup=get_size_edit_keyboard(size_id))

@router.callback_query(F.data.startswith("delete_size_"))
async def process_delete_size(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    size_id = int(callback.data.split("_")[2])
    try:
        with DatabaseManager.get_session() as db:
            db.query(ProductSize).filter(ProductSize.size_id == size_id).delete()
            deleted = db.query(Size).filter(Size.id == size_id).delete()
            db.commit()
        if deleted:
            await callback.message.edit_text("✅ Размер удален.", reply_markup=get_sizes_admin_keyboard())
        else:
            await callback.message.edit_text("❌ Размер не найден.", reply_markup=get_sizes_admin_keyboard())
    except Exception as e:
        logger.error(f"Ошибка удаления размера: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при удалении размера.", reply_markup=get_sizes_admin_keyboard())

# Отмена админ действий
@router.callback_query(F.data == "cancel_admin")
async def process_cancel_admin(callback: types.CallbackQuery, state: FSMContext):
    """Отмена админ действий"""
    await state.clear()
    
    admin_text = """Привет, админ 👋  
Что будем делать?"""
    
    await callback.message.edit_text(admin_text, reply_markup=get_admin_keyboard())

# Просмотр заказов
@router.callback_query(F.data == "admin_orders")
async def process_admin_orders(callback: types.CallbackQuery):
    """Просмотр заказов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    
    with DatabaseManager.get_session() as db:
        orders = db.query(Order).order_by(Order.created_at.desc()).limit(10).all()
    
    if not orders:
        orders_text = "📋 Заказы\n\nЗаказов пока нет."
    else:
        orders_text = "📋 Последние заказы:\n\n"
        
        for order in orders:
            status_emoji = {
                "pending": "⏳",
                "paid": "✅",
                "shipped": "🚚",
                "delivered": "📦"
            }.get(order.status, "❓")
            
            orders_text += f"{status_emoji} Заказ #{order.id}\n"
            orders_text += f"👤 Пользователь: @{order.username or 'без username'}\n"
            orders_text += f"💰 Сумма: {order.total_price}₽\n"
            orders_text += f"📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(orders_text, reply_markup=keyboard)

# Статистика
@router.callback_query(F.data == "admin_stats")
async def process_admin_stats(callback: types.CallbackQuery):
    """Статистика"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    
    with DatabaseManager.get_session() as db:
        categories_count = db.query(Category).count()
        titles_count = db.query(Title).count()
        products_count = db.query(Product).count()
        sizes_count = db.query(Size).count()
        orders_count = db.query(Order).count()
        
        total_revenue = db.query(Order).filter(Order.status == "paid").with_entities(
            db.func.sum(Order.total_price)
        ).scalar() or 0
    
    stats_text = f"""📊 Статистика

📂 Категории: {categories_count}
📖 Тайтлы: {titles_count}
🛍️ Товары: {products_count}
📏 Размеры: {sizes_count}
📋 Заказы: {orders_count}
💰 Общая выручка: {total_revenue}₽"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(stats_text, reply_markup=keyboard)
