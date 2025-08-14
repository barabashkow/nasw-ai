import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class BotSettings:
    bot_token: str
    owner_chat_id: int | None = None


def get_settings() -> BotSettings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is not set. Provide it via .env or environment.")
    owner_raw = os.getenv("OWNER_CHAT_ID", "").strip()
    owner_id = int(owner_raw) if owner_raw.isdigit() else None
    return BotSettings(bot_token=token, owner_chat_id=owner_id)