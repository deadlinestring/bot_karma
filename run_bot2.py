#!/usr/bin/env python3
"""
Запуск бота каталога (bot2)
"""

import asyncio
import logging
from config import BOT2_TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Запуск бота каталога"""
    try:
        logger.info("Запуск бота каталога...")
        
        # Импортируем и запускаем бот каталога
        import bot2_catalog
        await bot2_catalog.main()
        
    except KeyboardInterrupt:
        logger.info("Бот каталога остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка в боте каталога: {e}")

if __name__ == "__main__":
    asyncio.run(main())

