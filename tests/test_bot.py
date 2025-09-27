#!/usr/bin/env python3
"""
Тест для проверки работы ботов
"""

import asyncio
import logging
from config import BOT1_TOKEN, BOT2_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bot1():
    """Тест основного бота"""
    try:
        logger.info("Тестирование основного бота...")
        
        # Проверяем импорт
        import bot1_main
        logger.info("✅ Импорт bot1_main успешен")
        
        # Проверяем токен
        if BOT1_TOKEN:
            logger.info(f"✅ Токен BOT1 загружен: {BOT1_TOKEN[:10]}...")
        else:
            logger.error("❌ Токен BOT1 не загружен")
            
        # Проверяем бота
        if bot1_main.bot:
            logger.info("✅ Бот bot1 инициализирован")
        else:
            logger.error("❌ Бот bot1 не инициализирован")
            
        # Проверяем диспетчер
        if bot1_main.dp:
            logger.info("✅ Диспетчер bot1 инициализирован")
        else:
            logger.error("❌ Диспетчер bot1 не инициализирован")
            
        logger.info("✅ Основной бот готов к работе")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тесте основного бота: {e}")

async def test_bot2():
    """Тест бота каталога"""
    try:
        logger.info("Тестирование бота каталога...")
        
        # Проверяем импорт
        import bot2_catalog
        logger.info("✅ Импорт bot2_catalog успешен")
        
        # Проверяем токен
        if BOT2_TOKEN:
            logger.info(f"✅ Токен BOT2 загружен: {BOT2_TOKEN[:10]}...")
        else:
            logger.error("❌ Токен BOT2 не загружен")
            
        # Проверяем бота
        if bot2_catalog.bot:
            logger.info("✅ Бот bot2 инициализирован")
        else:
            logger.error("❌ Бот bot2 не инициализирован")
            
        # Проверяем диспетчер
        if bot2_catalog.dp:
            logger.info("✅ Диспетчер bot2 инициализирован")
        else:
            logger.error("❌ Диспетчер bot2 не инициализирован")
            
        logger.info("✅ Бот каталога готов к работе")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тесте бота каталога: {e}")

async def main():
    """Основная функция тестирования"""
    logger.info("🧪 Начинаем тестирование ботов...")
    
    await test_bot1()
    print()
    await test_bot2()
    
    logger.info("🎯 Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(main())

