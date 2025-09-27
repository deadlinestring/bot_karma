#!/usr/bin/env python3
"""
Тест команды /start
"""

import asyncio
import logging
from aiogram import Bot
from config import BOT1_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_start_command():
    """Тест команды /start"""
    try:
        bot = Bot(token=BOT1_TOKEN)
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"🤖 Бот: @{bot_info.username} ({bot_info.first_name})")
        
        # Получаем обновления
        updates = await bot.get_updates()
        logger.info(f"📨 Получено обновлений: {len(updates)}")
        
        if updates:
            last_update = updates[-1]
            logger.info(f"📝 Последнее обновление: {last_update}")
        
        await bot.session.close()
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_start_command())

