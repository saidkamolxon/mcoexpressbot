from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan quyidagilarni o'qiymiz
BOT_TOKEN: str = env.str("BOT_TOKEN")
OWNER_ID: str = env.str("OWNER")
ADMINS: list = env.list("ADMINS")
BING_API: str = env.str("BING_API")
BOT_USERNAME: str = env.str("BOT_USERNAME")
FLEET_API: str = env.str("FLEET_API")
FLEET_LOGIN: str = env.str("FLEET_LOGIN")
FLEET_PASSWORD: str = env.str("FLEET_PASSWORD")
FLEET_ACCOUNT_ID: str = env.str("FLEET_ACCOUNT_ID")
GOOGLE_API: str = env.str("GOOGLE_API")
ROADREADY_TOKEN = env.str("ROADREADY_TOKEN")
SWIFTELD_TOKEN: str = env.str("SWIFTELD_TOKEN")
IP: str = env.str("IP")  # Xosting ip manzili
DB_URL = env.str("DATABASE_URL") # postgresql
DB_USER = env.str("PGUSER") # postgresql
DB_PASS = env.str("PGPASSWORD") # postgresql
DB_NAME = env.str("PGDATABASE") # postgresql
DB_HOST = env.str("PGHOST") # postgresql
DB_PORT = env.str("PGPORT") # postgresql
