import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN

import handlers.start as start
import handlers.clubs as clubs
import handlers.packages as packages
import handlers.masterclasses as masterclasses


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Подключаем роутеры
dp.include_router(start.router)
dp.include_router(clubs.router)
dp.include_router(packages.router)
dp.include_router(masterclasses.router)


async def main():
    try:
        me = await bot.get_me()
        logging.info(f"Бот запущен как @{me.username}")

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    except Exception as e:
        logging.exception("Ошибка при запуске бота:")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
