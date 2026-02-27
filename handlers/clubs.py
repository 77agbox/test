from aiogram import Router
from data_loader import load_clubs

router = Router()

CLUBS_DATA = load_clubs()

# сюда переносится логика кружков
