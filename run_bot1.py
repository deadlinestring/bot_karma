#!/usr/bin/env python3
"""
Запуск основного бота (bot1)
"""

import asyncio
import logging
from config import BOT1_TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Запуск основного бота"""
    try:
        logger.info("Запуск основного бота...")
        
        # Импортируем и запускаем основной бот
        import bot1_main
        await bot1_main.main()
        
    except KeyboardInterrupt:
        logger.info("Основной бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка в основном боте: {e}")

if __name__ == "__main__":
    asyncio.run(main())

