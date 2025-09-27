import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from config import BOT1_TOKEN, BOT2_TOKEN, ADMIN_IDS
import bot1_main
import bot2_catalog
import admin_panel

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Запуск всех ботов"""
    logger.info("Запуск системы ботов...")
    
    # Создаем задачи для каждого бота
    tasks = []
    
    try:
        # Запускаем основной бот (bot1)
        bot1_task = asyncio.create_task(bot1_main.main())
        tasks.append(bot1_task)
        logger.info("Основной бот запущен")
        
        # Запускаем бот каталога (bot2)
        bot2_task = asyncio.create_task(bot2_catalog.main())
        tasks.append(bot2_task)
        logger.info("Бот каталога запущен")
        
        # Ждем завершения всех задач
        await asyncio.gather(*tasks)
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"Ошибка при запуске ботов: {e}")
    finally:
        logger.info("Остановка ботов...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа завершена пользователем")



