from aiogram import Dispatcher

from loader import dp
from .throttling import ThrottlingMiddleware
from .checkuser import CheckUser


if __name__ == "middlewares":
    dp.middleware.setup(ThrottlingMiddleware())
    dp.middleware.setup(CheckUser())
