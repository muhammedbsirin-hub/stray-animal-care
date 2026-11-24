import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
MEDIA_DIR = ROOT_DIR / "media"
load_dotenv(ROOT_DIR / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "stray_app"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "stray_db"),
    "charset": "utf8mb4",
    "collation": "utf8mb4_tr_0900_ai_ci",
    "autocommit": True,
    "use_pure": True,
}

APP_TITLE = "Stray Animal Care"
ISTANBUL_CENTER = (41.03, 29.00)
NOTIFICATION_REFRESH_MS = 15_000
