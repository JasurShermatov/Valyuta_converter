# data/texts.py yaratish kerak
texts = {
    "admin_start": "👋 Assalomu alaykum, {fullname}!\n\n📊 Admin paneliga xush kelibsiz!",
}


def text(key: str) -> str:
    return texts.get(key, key)
