import os
import sqlite3
import asyncio
from vkbottle import Bot

TOKEN = "vk1.a.2xJ9Erjp0zJXSonrBiTJeJwjNIRkEuD0UwYLs22DPpscioaeRYv_VqSaQheuHYoeBFsq1R6raVq6hQ7uaS6sVbFllqreR6GHNj51eFFE2B5EPlR6j7UNRqF1yU5YDg550Zl3oD8eSgevlIv9rs2hkdqYpO-m-iYJ6SXEIDSZxbC-A3n26WSXTa9i-v5gEn8NAR592ntCwzxTVyXnttgyPA"  # замените на ваш токен
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')
bot = Bot(TOKEN)

def initialize_duel_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS duels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER,
            user2_id INTEGER,
            bet INTEGER,
            winner_id INTEGER DEFAULT NULL,
            timestamp INTEGER
        )
    ''')
    conn.commit()
    conn.close()
    print("Таблица 'duels' успешно создана (или уже существует).")

@bot.on.message(text="/ping")
async def ping_handler(message):
    await message.reply("pong")

async def main():
    print("Инициализация таблиц...")
    initialize_duel_table()
    print("Таблицы инициализированы.")
    print("Запуск бота...")
    try:
        await bot.run_polling()
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())
