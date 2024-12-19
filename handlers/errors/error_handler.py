import logging
from aiogram import Router
from aiogram.exceptions import (
    TelegramUnauthorizedError,
    TelegramBadRequest,
    TelegramAPIError,
    TelegramRetryAfter,
    TelegramEntityTooLarge,
)
from aiogram.types import Update

router = Router()


@router.errors()  # Changed from @dp.errors_handler()
async def errors_handler(update: Update, exception: Exception) -> bool:
    """
    Exceptions handler. Catches all exceptions within task factory tasks.
    :param update: Update object
    :param exception: Raised exception
    :return: bool
    """

    if isinstance(exception, TelegramBadRequest):
        if "message is not modified" in str(exception):
            logging.exception("Message is not modified")
            return True
        if "message can't be deleted" in str(exception):
            logging.exception("Message cant be deleted")
            return True
        if "message to delete not found" in str(exception):
            logging.exception("Message to delete not found")
            return True
        if "message text is empty" in str(exception):
            logging.exception("MessageTextIsEmpty")
            return True
        if "can't demote chat creator" in str(exception):
            logging.exception("Can't demote chat creator")
            return True

    if isinstance(exception, TelegramUnauthorizedError):
        logging.exception(f"Unauthorized: {exception}")
        return True

    if isinstance(exception, TelegramRetryAfter):
        logging.exception(f"RetryAfter: {exception} \nUpdate: {update}")
        return True

    if isinstance(exception, TelegramEntityTooLarge):
        logging.exception(f"CantParseEntities: {exception} \nUpdate: {update}")
        return True

    if isinstance(exception, TelegramAPIError):
        logging.exception(f"TelegramAPIError: {exception} \nUpdate: {update}")
        return True

    logging.exception(f"Update: {update} \n{exception}")
    return True
