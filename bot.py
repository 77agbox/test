import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db

# Роутеры
import handlers.start as start
import handlers.clubs as clubs
import handlers.packages as packages
import handlers.masterclasses as masterclasses
import handlers.admin as admin


# ================= ЛОГИ =================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


# ================= БОТ =================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ================= ПОДКЛЮЧЕНИЕ РОУТЕРОВ =================

dp.include_router(start.router)
dp.include_router(clubs.router)
dp.include_router(packages.router)
dp.include_router(masterclasses.router)
dp.include_router(admin.router)


# ================= MAIN =================

async def main():
    try:
        # Инициализация базы данных
        init_db()

        # Проверка подключения
        me = await bot.get_me()
        logging.info(f"Бот запущен как @{me.username}")

        # Удаляем вебхук если был
        await bot.delete_webhook(drop_pending_updates=True)

        # Запуск polling
        await dp.start_polling(bot)

    except Exception:
        logging.exception("Критическая ошибка при запуске:")
    finally:
        await bot.session.close()


# ================= ЗАПУСК =================

if __name__ == "__main__":
    asyncio.run(main())
