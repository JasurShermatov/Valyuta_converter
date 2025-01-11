from aiogram.types import InlineKeyboardButton

from data.config import channels_manager
from data.texts import button
from loader import bot
from utils.misc import subscription


async def check_status(user_id: int):
    final_status = True
    chs = []
    for channel in channels_manager.get_channels():
        channel_id = channel.get("id")
        try:
            status = await subscription.check(
                user_id=user_id,
                channel=channel_id
            )
            final_status &= status
            if not status:
                chat = await bot.get_chat(channel_id)
                invite_link = channel.get('link')  # await chat.export_invite_link()
                chs.append([InlineKeyboardButton(text=channel.get('title'), url=invite_link)])
        except Exception as ex:
            print("check channels:", ex)
    chs.append([InlineKeyboardButton(text=button("user_check_subscribe"), callback_data=f"user_check_subs")])
    return final_status, chs
