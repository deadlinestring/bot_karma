import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Токены ботов
BOT1_TOKEN = os.getenv('BOT1_TOKEN')  # Основной бот
BOT2_TOKEN = os.getenv('BOT2_TOKEN')  # Каталог

# Имена ботов (для ссылок)
BOT2_USERNAME = os.getenv('BOT2_USERNAME', 'karma_nightlights_catalog_bot')  # @имя_бота_каталога

# Настройки Юкассы
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')

# Настройки базы данных (SQLite по умолчанию)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_database.db')

# ID администраторов
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]

# Настройки доставки
DELIVERY_METHODS = {
    'post': {'name': 'Почта России', 'price': 510},
    'cdek': {'name': 'СДЭК', 'price': 700},
    'pickup': {'name': 'Самовывоз', 'price': 0}
}

# Информация о компании
COMPANY_INFO = {
    'name': 'Магазин ночников',
    'description': 'Изготавливаем уникальные ночники на заказ',
    'discount_percent': 10  # Скидка за заказ через бота
}

# FAQ
FAQ_ITEMS = [
    {
        'question': 'Сколько времени занимает изготовление?',
        'answer': 'Изготовление занимает 3-5 рабочих дней'
    },
    {
        'question': 'Как происходит оплата?',
        'answer': 'Оплата производится через Юкассу банковской картой'
    },
    {
        'question': 'Можно ли вернуть товар?',
        'answer': 'Возврат возможен в течение 14 дней при сохранении товарного вида'
    }
]
