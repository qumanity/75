import os
import re
import time
import random
import sqlite3
import requests
import csv
import io
import json
import asyncio
import aiosqlite
from datetime import datetime
import schedule
from vkbottle import Bot
from vkbottle import API
from shop import SHOP
from vkbottle import Bot, VKAPIError
from vkbottle_types.objects import MessagesMessageActionStatus  # Новый импорт
import json
import logging
from vkbottle.bot import Bot, BotLabeler, Message
from datetime import timedelta


# ==============================
# Конфигурация и инициализация
# ==============================
OWNER_ID = 527055305  # Укажите ID владельца бота

# Глобальный словарь для хранения времени последней игры в слот для каждого пользователя
slot_cooldowns = {}
# Хранение ID сообщения, на которое бот ответил
answered_message_id = None
# Глобальная переменная для хранения ID (conversation_message_id) сообщения /help
help_cmid = None
alt_cmid = None  # Для отслеживания сообщения с альтернативными командами
panel_messages = {}
user_last_messages = {}
user_tasks = {}


# Словарь с количеством дней до повышения
PROMOTIONS = {
    "Младший модератор": 7,
    "Модератор": 15,
    "Старший модератор": 15,
    "Куратор модерации": 15,
    "Зам.Главного модератора": 100,
    "Главный модератор": 999   
}

# Словарь с количеством дней до повышения
ISKL = {
    "Младший модератор": 5,
    "Модератор": 10
}

# Путь к базе данных
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

# ID беседы для логов (peer_id)
# Например, если у вас есть беседа с chat_id = 123, то peer_id = 2000000000 + 123.
LOG_CHAT_ID = 2000000008  # Замените на нужное значение
LOG_STAFF_ID = 2000000010

# Пороговые значения ставки и КД
MIN_BET = 50
MAX_BET = 500
DUEL_COOLDOWN = 300  # 15 минут в секундах

# Таблица коэффициентов для разных режимов
COEFFICIENTS = {
    "easy": [(3, 0.2), (2, 0.5), (1, 0.3)],  # Безопасный режим
    "risky": [(5, 0.05), (3, 0.2), (2, 0.3), (1, 0.25), (0, 0.2)],  # Рискованный
    "default": [(5, 0.05), (3, 0.15), (2, 0.3), (1, 0.4), (0, 0.1)]  # Обычный
}

# Замените на ваш токен группы ВКонтакте
logging.basicConfig(level=logging.INFO)
bot = Bot("vk1.a.35e6GiYzUeGur4vuP0EYIFKkJfS9Vw446NYkPITriiAZlvmxWbbEFHdh9Isad4YodCFDet9kianNh6FTUsDDN8SbD-n6vxfri00pQZCLlcqrCt64NQxsE2fTS3umbHAdyZoJs2RYuCoxzq9hZ3Wm3J3DCLkZ7Ln-n0aYqFQ0ZSAVRWpXBJK4vmVm6R5BAndC4QObH9j2kJQWrs30dLS--w")
api = API("vk1.a.35e6GiYzUeGur4vuP0EYIFKkJfS9Vw446NYkPITriiAZlvmxWbbEFHdh9Isad4YodCFDet9kianNh6FTUsDDN8SbD-n6vxfri00pQZCLlcqrCt64NQxsE2fTS3umbHAdyZoJs2RYuCoxzq9hZ3Wm3J3DCLkZ7Ln-n0aYqFQ0ZSAVRWpXBJK4vmVm6R5BAndC4QObH9j2kJQWrs30dLS--w")
labeler = BotLabeler()
bl = BotLabeler()

# Хранение персональных заданий для каждого пользователя
user_tasks = {}


# Токен бота и список администраторов
CSV_URL = "https://docs.google.com/spreadsheets/d/1G3QYC8oQHAqGUfewK85BHjYsfKttyzC6CKa75DCuPj4/export?format=csv"
REESTR_URL = "https://docs.google.com/spreadsheets/d/1MTOZEviCcE1JxpHmpteKVn11IeV6ayhpv6uu18UuQjg/export?format=csv"
TOKEN = "vk1.a.35e6GiYzUeGur4vuP0EYIFKkJfS9Vw446NYkPITriiAZlvmxWbbEFHdh9Isad4YodCFDet9kianNh6FTUsDDN8SbD-n6vxfri00pQZCLlcqrCt64NQxsE2fTS3umbHAdyZoJs2RYuCoxzq9hZ3Wm3J3DCLkZ7Ln-n0aYqFQ0ZSAVRWpXBJK4vmVm6R5BAndC4QObH9j2kJQWrs30dLS--w"
ADMINS = [527055305]
OWNER_ID = 527055305
LIST_URL = "https://docs.google.com/spreadsheets/d/1G0Rr2cmV7_pDW-sQlqe2_MKSm-rgGFb9VArN6r3C5UM/export?format=csv"
CHECK_INTERVAL = 1  # интервал проверки в секундах
CHAT_ID = 2  # ID беседы, куда будем отправлять уведомления

# Храним предыдущие строки, чтобы отслеживать изменения
previous_data = []

# Список напоминаний (в реальном проекте можно хранить в базе данных)
reminders = []

# Инициализация бота
bot = Bot(TOKEN)

# Глобальные словари для активных дуэлей и КД
pending_duels = {}    # Ключ: target_id, значение: dict { "challenger": id, "bet": value, "time": timestamp }
duel_cooldowns = {}   # Ключ: user_id, значение: timestamp последней дуэли

# Приоритет ролей (больше число – выше приоритет)
ROLE_PRIORITY = {
    "owner": 7,
    "depspec": 6,
    "senadmin": 5,
    "admin": 4,
    "senmoder": 3,
    "moder": 2,
    "user": 1
}

BET_COOLDOWN = 120  # 2 минуты в секундах
DB_PATH = "database.db"

last_bets = {}  # Хранение времени последней ставки пользователей

def get_user_balance(user_id):
    """ Получает баланс пользователя из базы данных """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0


def update_user_balance(user_id, amount):
    """ Обновляет баланс пользователя """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def get_referral_bonus(user_id):
    """ Проверяет, имеет ли пользователь реферальный бонус (10% к выигрышу в первый день) """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT referral FROM referrals WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        joined_at = result[0]
        return (time.time() - joined_at) < 86400  # Если прошло менее суток, бонус действует
    return False


# ==============================
# Функции для работы с базой данных
# ==============================

async def check_chat_id(message: Message) -> bool:
    """Проверяет, что команда используется только в чате с ID 2."""
    if message.peer_id != 2000000002:  # 2000000000 + chat_id (2)
        await message.reply("Эта команда доступна только в определенном чате!")
        return False
    return True

# Функция для отправки напоминания
async def send_weekly_reminder():
    # ID беседы, куда отправляется напоминание
    chat_id = 2
    user_mention = "@n.ivanov.official"
    reminder_text = f"{user_mention}, не забудь про еженедельный отчет."

    try:
        await bot.api.messages.send(
            peer_id=2000000000 + chat_id,  # Для бесед peer_id = 2000000000 + chat_id
            random_id=0,
            message=reminder_text
        )
        print(f"Напоминание отправлено в беседу {chat_id}")
    except Exception as e:
        print(f"Ошибка при отправке напоминания: {e}")


# Функция для планирования напоминаний
def send_reminder(user_id, message_text):
    async def reminder_job():
        try:
            await bot.api.messages.send(
                peer_id=2000000000 + 2,  # ID беседы с напоминаниями (2)
                message=f"@id{user_id} {message_text}",
                random_id=0
            )
        except Exception as e:
            print(f"Ошибка при отправке напоминания: {e}")

    return reminder_job

def is_owner(user_id):
    # Проверка, что пользователь является владельцем
    return get_user_role(user_id) == "owner"

# Функция для удаления сообщения
async def delete_message(bot, message_id, peer_id):
    """
    Функция для удаления сообщения по message_id и peer_id.
    Параметры:
    - bot: объект бота
    - message_id: ID сообщения для удаления
    - peer_id: ID чата/беседы
    """
    try:
        response = await bot.api.messages.delete(
            message_ids=[message_id],  # Список с ID сообщения
            peer_id=peer_id  # ID беседы (peer_id)
        )

        # Логируем полученный ответ от API
        print(f"Ответ от API: {response}")

        if isinstance(response, dict) and response.get("response") == 1:
            return "✅ Сообщение удалено."
        elif isinstance(response, list) and len(response) > 0:
            return "✅ Сообщение удалено."
        else:
            print(f"Ошибка удаления: Неудовлетворительный ответ от API: {response}")
            return f"⚠️ Не удалось удалить сообщение: {response}"

    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
        return f"⚠️ Ошибка при удалении сообщения: {e}"


# Функция для получения данных из Google Sheets
def get_data_from_google_sheets():
    response = requests.get(LIST_URL)
    # Преобразуем полученный CSV в список словарей
    content = io.StringIO(response.text)
    csv_reader = csv.DictReader(content)
    return list(csv_reader)

# Функция для отправки сообщения в чат
async def send_message_to_chat(message):
    await bot.api.messages.send(peer_id=200000002, message=message)

# Функция для проверки новых строк и оповещения
async def check_new_rows():
    global previous_data
    current_data = get_data_from_google_sheets()

    # Проверка, есть ли новые строки
    if len(current_data) > len(previous_data):
        new_rows = current_data[len(previous_data):]
        
        # Формируем сообщение об новых строках
        new_rows_message = "Новые добавленные строки:\n"
        for row in new_rows:
            new_rows_message += json.dumps(row) + "\n"

        # Отправляем сообщение в нужный чат
        await send_message_to_chat(new_rows_message)
        
        # Обновляем предыдущие данные
        previous_data = current_data

# Функция для регулярной проверки
async def periodic_check():
    while True:
        await check_new_rows()
        await asyncio.sleep(CHECK_INTERVAL)  # Используем asyncio.sleep для асинхронного ожидания


# Создаем таблицу, если её нет
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nicknames (
                vk_id INTEGER PRIMARY KEY,
                nickname TEXT
            )
        """)
        conn.commit()

init_db()

import sqlite3

# Подключаемся к базе данных
def get_db_connection():
    conn = sqlite3.connect('database.db')  # Путь к вашей базе данных
    conn.row_factory = sqlite3.Row  # Чтобы можно было обращаться к столбцам по имени
    return conn

# Подключаемся к базе данных
def get_db_connection():
    conn = sqlite3.connect('database.db')  # Путь к вашей базе данных
    conn.row_factory = sqlite3.Row  # Чтобы можно было обращаться к столбцам по имени
    return conn

# Функция для получения никнейма из базы данных
def get_nickname(vk_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nickname FROM nicknames WHERE vk_id = ?", (vk_id,))
    result = cursor.fetchone()
    conn.close()
    return result['nickname'] if result else None

# Функция для удаления никнейма из базы данных
def remove_nickname_from_db(vk_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM nicknames WHERE vk_id = ?", (vk_id,))
    conn.commit()
    conn.close()

# Функция для получения списка всех никнеймов
# Функция для получения всех никнеймов
def get_alll_nicknames():
    # Открытие базы данных и получение всех записей с никнеймами
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT vk_id, nickname FROM nicknames")  # Убедись, что выбираешь оба столбца
        results = cursor.fetchall()

    return results  # Возвращаем список с кортежами вида (vk_id, nickname)



def extract_vk_id(mention: str) -> str:
    """
    Извлекает числовой ID из строки вида "https://vk.com/id12345".
    Возвращает строку с цифрами или None, если не найдено.
    """
    match = re.search(r'https://vk\.com/id(\d+)', mention)
    if match:
        return match.group(1)
    return None

def get_info_by_id(vk_id: str) -> dict:
    """
    Загружает CSV-данные по URL, ищет строку, где в столбце с ID (предположим, столбец A, индекс 0)
    совпадает с vk_id, и возвращает данные в виде словаря.
    Если строка не найдена или произошла ошибка, возвращает словарь с ключом "error".
    """
    try:
        response = requests.get(CSV_URL)
        response.raise_for_status()
    except Exception as e:
        return {"error": f"Ошибка загрузки CSV: {e}"}
    
    data = response.text.splitlines()
    reader = csv.reader(data)
    # Если в CSV есть заголовок, можно его пропустить:
    rows = list(reader)
    
    target_row = None
    for row in rows:
        # Если таблица содержит не менее нужного количества столбцов (проверьте, какой столбец содержит ID)
        if len(row) < 1:
            continue
        # Предположим, что нужный ID находится в первом столбце (индекс 0)
        if row[0].strip() == vk_id:
            target_row = row
            break

    if not target_row:
        return {"error": f"ID {vk_id} не найден."}
    
    # Формируем информацию для вывода. Здесь можно адаптировать формат.
    # Например, выводим всю строку, разделённую запятыми.
    info_str = ", ".join(target_row)
    return {"info": info_str}

def get_base_nickname(nickname: str) -> str:
    """
    Возвращает базовый никнейм, очищая его от лишних пробелов.
    Ожидается, что nickname передаётся в формате "Nick_Name".
    """
    return nickname.strip()

def add_column_if_not_exists(table: str, column: str, column_type: str):
    """Добавляет новый столбец в таблицу, если его ещё нет."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Получаем список столбцов в таблице
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]

    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        conn.commit()
        print(f"✅ Столбец '{column}' добавлен в таблицу '{table}'")
    else:
        print(f"⚠️ Столбец '{column}' уже существует в таблице '{table}'")

    conn.close()

def get_info_from_csv(nickname: str) -> dict:
    try:
        response = requests.get(CSV_URL)
        response.raise_for_status()
        response.encoding = 'utf-8'  # Указываем кодировку UTF-8
        data = response.text
    except Exception as e:
        return {"error": f"Ошибка загрузки CSV: {e}"}

    reader = csv.reader(io.StringIO(data))
    rows = list(reader)

    target_row = None
    for row in rows:
        if len(row) < 25:
            continue
        cell = row[2].strip()
        if cell.lower() == nickname.strip().lower():
            target_row = row
            break

    if not target_row:
        return {"error": f"Никнейм '{nickname}' не найден."}

    try:
        info = {
            "NickName": target_row[2].strip(),
            "Должность": target_row[3].strip(),
            "lvl": target_row[4].strip(),
            "Реальное имя": target_row[6].strip(),
            "Дата рождения": target_row[7].strip(),
            "Возраст": target_row[8].strip(),
            "Доступ с ПК": target_row[9].strip(),
            "Часовой пояс": target_row[10].strip(),
            "Username Discord": target_row[12].strip(),
            "Discord ID": target_row[13].strip(),
            "VK": target_row[15].strip(),
            "Forum": target_row[16].strip(),
            "Telegram": target_row[17].strip(),
            "Дата назначения": target_row[19].strip(),
            "Последнее повышение": target_row[20].strip(),
            "Предупреждения": target_row[22].strip(),
            "Выговоры": target_row[23].strip(),
            "Еженедельные": target_row[25].strip(),
            "Дней всего": target_row[26].strip(),
            "Дней на посту": target_row[27].strip(),
            "№ в реестре": target_row[29].strip()            
        }
    except Exception as e:
        return {"error": f"Ошибка при извлечении данных: {e}"}
    
    return info

def get_reestr_from_csv(reestr: str) -> dict:
    try:
        response = requests.get(REESTR_URL)
        response.raise_for_status()
        response.encoding = 'utf-8'  # Указываем кодировку UTF-8
        data = response.text
    except Exception as e:
        return {"error": f"Ошибка загрузки CSV: {e}"}

    reader = csv.reader(io.StringIO(data))
    rows = list(reader)

    target_row = None
    for row in rows:
        if len(row) < 16:  # Проверка на минимальное количество столбцов
            continue
        cell = row[2].strip()  # Используем столбец с индексом 1 для поиска по никнейму
        if cell.lower() == reestr.strip().lower():
            target_row = row
            break

    if not target_row:
        return {"error": f"Запись реестра {reestr} не найдена."}
    
    try:
        reestr = {
            "№": target_row[2].strip(),  # Допустим, это номер записи
            "Отметка времени": target_row[3].strip(),    
            "Адрес электронной почты": target_row[4].strip(),  
            "Игровой NickName": target_row[5].strip(),  
            "Реальное имя": target_row[6].strip(),  
            "Возраст (полных лет)": target_row[7].strip(),  
            "Дата рождения": target_row[8].strip(),  
            "Страница ВК (цифрами, узнать можно на сайте https://regvk.com )": target_row[9].strip(),  
            "Username Discord (тег)": target_row[10].strip(),  
            "ID Discord (цифрами)": target_row[11].strip(),  
            "Telegram ": target_row[12].strip(),  
            "Часовой пояс": target_row[13].strip(),  
            "Ссылка на форумный аккаунт": target_row[14].strip(),  
            "Дата": target_row[15].strip(),  
            "Актуальность (стоит ли человек на данный момент)": target_row[16].strip(),  
        }
    except Exception as e:
        return {"error": f"Ошибка при извлечении данных: {e}"}
    
    return reestr

def get_link_from_csv(reestr: str) -> dict:
    try:
        response = requests.get(REESTR_URL)
        response.raise_for_status()
        response.encoding = 'utf-8'  # Указываем кодировку UTF-8
        data = response.text
    except Exception as e:
        return {"error": f"Ошибка загрузки CSV: {e}"}

    reader = csv.reader(io.StringIO(data))
    rows = list(reader)

    target_row = None
    for row in rows:
        if len(row) < 16:  # Проверка на минимальное количество столбцов
            continue
        cell = row[5].strip()  # Используем столбец с индексом 1 для поиска по никнейму
        if cell.lower() == reestr.strip().lower():
            target_row = row
            break

    if not target_row:
        return {"error": f"Ссылки юзера не найдены."}
    
    try:
        reestr = {
            "№": target_row[2].strip(),  # Допустим, это номер записи
            "Отметка времени": target_row[3].strip(),    
            "Адрес электронной почты": target_row[4].strip(),  
            "Игровой NickName": target_row[5].strip(),  
            "Реальное имя": target_row[6].strip(),  
            "Возраст (полных лет)": target_row[7].strip(),  
            "Дата рождения": target_row[8].strip(),  
            "Страница ВК (цифрами, узнать можно на сайте https://regvk.com )": target_row[9].strip(),  
            "Username Discord (тег)": target_row[10].strip(),  
            "ID Discord (цифрами)": target_row[11].strip(),  
            "Telegram ": target_row[12].strip(),  
            "Часовой пояс": target_row[13].strip(),  
            "Ссылка на форумный аккаунт": target_row[14].strip(),  
            "Дата": target_row[15].strip(),  
            "Актуальность (стоит ли человек на данный момент)": target_row[16].strip(),  
        }
    except Exception as e:
        return {"error": f"Ошибка при извлечении данных: {e}"}
    
    return reestr

def get_all_nicknames() -> list:
    try:
        response = requests.get(CSV_URL)
        response.raise_for_status()
        response.encoding = 'utf-8'
        data = response.text
    except Exception as e:
        return [f"Ошибка загрузки CSV: {e}"]

    reader = csv.reader(io.StringIO(data))
    nicknames = [row[2].strip() for row in reader if len(row) > 2 and row[2].strip()]
    return nicknames if nicknames else ["Никнеймы не найдены."]


def get_db_connection():
    return sqlite3.connect(DB_PATH)

def initialize_applications_table():
    """Создаёт таблицу applications, если её ещё нет."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT,
            verdict TEXT,
            verdict_date TEXT,
            reason TEXT,
            vk TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("Таблица applications успешно создана (или уже существует).")

# Функция для синхронизации таблицы заявок с данными из Google CSV
def sync_applications_from_google() -> str:
    try:
        response = requests.get(LIST_URL)
        response.raise_for_status()
        response.encoding = 'utf-8'
        data = response.text
    except Exception as e:
        return f"Ошибка загрузки CSV: {e}"

    reader = csv.reader(io.StringIO(data))
    rows = list(reader)
    if not rows:
        return "CSV пустой."

    conn = get_db_connection()
    cursor = conn.cursor()
    updated_count = 0
    inserted_count = 0

    # Проходим по всем строкам CSV; предполагается, что нужные столбцы:
    # row[7] - Игровой Nick_Name (nickname)
    # row[2] - Вердикт
    # row[3] - Отметка времени (verdict_date)
    # row[4] - Причина отказа (reason)
    # row[10] - Ссылка на страницу в ВКонтакте (vk)
    for row in rows:
        if len(row) < 11:
            continue
        nickname = row[6].strip()
        verdict = row[2].strip() if row[2] else ""
        verdict_date = row[3].strip() if row[3] else ""
        reason = row[4].strip() if row[4] else ""
        vk_page = row[9].strip() if row[10] else ""
        if not nickname:
            continue

        # Проверяем, есть ли заявка с таким никнеймом
        cursor.execute("SELECT vk FROM applications WHERE nickname = ?", (nickname,))
        existing = cursor.fetchone()
        if existing:
            # Если поле vk пустое, обновляем его
            if not existing[0]:
                cursor.execute("UPDATE applications SET vk = ? WHERE nickname = ?", (vk_page, nickname))
                updated_count += 1
        # Новые записи не добавляем
        else:
            inserted_count += 1  # Учитываем только попытки вставки, но не делаем реальную вставку

    conn.commit()
    conn.close()
    return f"Синхронизация базы заявлений завершена: обновлено {updated_count} записей."


async def find_application_in_google(nickname: str) -> dict:
    """Ищет заявку в Google CSV по никнейму и возвращает данные (если найдены)."""
    try:
        response = requests.get(LIST_URL)
        response.raise_for_status()
        response.encoding = 'utf-8'
        data = response.text
    except Exception as e:
        return {"error": f"Ошибка загрузки CSV: {e}"}

    reader = csv.reader(io.StringIO(data))
    rows = list(reader)
    
    if not rows:
        return {"error": "CSV пустой."}

    for row in rows:
        if len(row) < 11:
            continue

        csv_nickname = row[6].strip()
        if csv_nickname.lower() == nickname.lower():
            return {
                "nickname": csv_nickname,
                "verdict": row[2].strip() if row[2] else "",
                "vk_page": row[9].strip() if row[9] else "Не найден"
            }

    return {"error": "Заявка не найдена."}

# ===== Утилиты =====

def get_info_from_list(nickname: str) -> dict:
    """
    Извлекает информацию из CSV по никнейму.
    Сначала ищет по nickname (row[7]), затем по VK (row[10]) если не найдено.
    """
    try:
        response = requests.get(LIST_URL)
        response.raise_for_status()
        response.encoding = 'utf-8'
        data = response.text
    except Exception as e:
        return {"error": f"Ошибка загрузки CSV: {e}"}

    reader = csv.reader(io.StringIO(data))
    rows = list(reader)
    target_row = None
    for row in rows:
        if len(row) < 11:
            continue
        if row[7].strip().lower() == nickname.strip().lower():
            target_row = row
            break
    if not target_row:
        for row in rows:
            if len(row) < 11:
                continue
            if row[10].strip().lower() == nickname.strip().lower():
                target_row = row
                break
    if not target_row:
        return {"error": f"Никнейм '{nickname}' не найден."}
    try:
        info = {
            "Вердикт": target_row[2].strip(),
            "Отметка времени": target_row[3].strip(),
            "Адрес электронной почты": target_row[4].strip(),
            "Ваше имя и возраст": target_row[6].strip(),
            "Игровой Nick_Name": target_row[7].strip(),
            "Discord ID": target_row[8].strip(),
            "Никнейм с тэгом": target_row[9].strip(),
            "Ссылка на страницу в ВКонтакте": target_row[10].strip()
        }
    except Exception as e:
        return {"error": f"Ошибка при извлечении данных: {e}"}
    return info

# Пример функции получения базового никнейма (можно изменить по логике)
def get_base_nickname(nickname: str) -> str:
    return nickname.strip()

def get_nickname(nickname: str) -> str:
    return nickname.strip()

# ====== Инициализация таблицы ======
def initialize_duel_table():
    conn = get_db_connection()
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

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def initialize_applications_table():
    """Создаёт таблицу applications для заявлений, если она ещё не существует.
       Таблица содержит:
         - nickname TEXT PRIMARY KEY,
         - verdict TEXT,
         - verdict_date TEXT,
         - reason TEXT (для отказов)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            nickname TEXT PRIMARY KEY,
            verdict TEXT,
            verdict_date TEXT,
            reason TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("Таблица applications успешно создана (или уже существует).")

# ====== Работа с БД ======
def add_user(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, balance, last_duel_time) VALUES (?, ?, ?)",
                   (user_id, 100, 0))
    conn.commit()
    conn.close()


def get_balance(user_id: int) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0


def update_balance(user_id: int, amount: int):
    """Обновляет баланс пользователя (прибавляет/вычитает сумму)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()




def get_active_duel(user_id: int):
    """Проверяем, есть ли активная дуэль у пользователя."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, user1_id, bet FROM duels WHERE user2_id = ? AND winner_id IS NULL", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def create_duel(user1: int, user2: int, bet: int):
    """Создаём запись о вызове на дуэль."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO duels (user1_id, user2_id, bet, timestamp) VALUES (?, ?, ?, ?)",
                   (user1, user2, bet, int(time.time())))
    conn.commit()
    conn.close()


def remove_duel(duel_id: int):
    """Удаляет вызов на дуэль (при отклонении или отмене)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM duels WHERE id = ?", (duel_id,))
    conn.commit()
    conn.close()


def set_duel_winner(duel_id: int, winner: int):
    """Записывает победителя дуэли."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE duels SET winner_id = ? WHERE id = ?", (winner, duel_id))
    conn.commit()
    conn.close()

def get_db_connection():
    """Возвращает соединение с базой данных."""
    return sqlite3.connect(DB_PATH)

def initialize_punishments_table():
    """Создаёт таблицу punishments, если её ещё не существует."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS punishments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                type TEXT,
                issued_by INTEGER,
                issued_at INTEGER
            )
        ''')
        conn.commit()
    print("Таблица punishments успешно создана (или уже существует).")

def initialize_database():
    """Создаёт таблицу users, если она ещё не существует."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            registration_date TEXT,
            role TEXT DEFAULT 'user',
            balance INTEGER DEFAULT 0,
            points INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            total_messages INTEGER DEFAULT 0,
            last_message_time INTEGER DEFAULT 0,
            last_reward_time INTEGER DEFAULT 0,
            last_russian_roulette INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_punishments_table()

def get_all_users_with_points():
    """Возвращает список всех пользователей с их количеством баллов."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, points FROM users WHERE points")
    users = cursor.fetchall()
    conn.close()
    return users

def initialize_columns():
    """Инициализирует дополнительные колонки в таблице users."""
    add_column_if_not_exists("points", "INTEGER DEFAULT 0")
    add_column_if_not_exists("total_messages", "INTEGER DEFAULT 0")
    add_column_if_not_exists("last_message_time", "INTEGER DEFAULT 0")
    add_column_if_not_exists("last_reward_time", "INTEGER DEFAULT 0")
    add_column_if_not_exists("last_russian_roulette", "INTEGER DEFAULT 0")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def initialize_punishments_table():
    """Создаёт таблицу punishments, если её ещё не существует."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS punishments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                type TEXT,           -- 'warn' или 'vig'
                issued_by INTEGER,
                issued_at INTEGER
            )
        ''')
        conn.commit()
    print("Таблица punishments успешно создана или уже существует.")

async def get_chat_name(chat_id: int) -> str:
    """Возвращает название беседы по chat_id"""
    try:
        chat_info = await bot.api.messages.get_conversations_by_id(peer_ids=2000000000 + chat_id)
        return chat_info.items[0].chat_settings.title
    except Exception:
        return f"Беседа {chat_id}"


def add_punishment(chat_id: int, user_id: int, p_type: str, issued_by: int):
    issued_at = int(time.time())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO punishments (chat_id, user_id, type, issued_by, issued_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (chat_id, user_id, p_type, issued_by, issued_at))
        conn.commit()
    print(f"Добавлено наказание {p_type} для пользователя {user_id} в беседе {chat_id}.")

def count_punishment(chat_id: int, user_id: int, p_type: str) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM punishments
            WHERE chat_id = ? AND user_id = ? AND type = ?
        ''', (chat_id, user_id, p_type))
        result = cursor.fetchone()
    cnt = result[0] if result else 0
    print(f"Пользователь {user_id} имеет {cnt} наказаний типа {p_type} в беседе {chat_id}.")
    return cnt

def update_user_message_count(user_id: int):
    """Обновляет счётчик сообщений и время последнего сообщения для пользователя."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    current_time = int(time.time())  # Текущее время в секундах
    
    # Получаем текущее значение total_messages для данного пользователя
    cursor.execute("SELECT total_messages FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row:
        total_messages = row[0] if row[0] is not None else 0
        total_messages += 1
        cursor.execute(
            "UPDATE users SET total_messages = ?, last_message_time = ? WHERE user_id = ?",
            (total_messages, current_time, user_id)
        )
    else:
        # Если пользователя нет в базе, можно создать новую запись (либо обработать по-другому)
        cursor.execute(
            "INSERT INTO users (user_id, total_messages, last_message_time) VALUES (?, ?, ?)",
            (user_id, 1, current_time)
        )
    
    conn.commit()
    conn.close()

def remove_one_punishment(chat_id: int, user_id: int, p_type: str) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM punishments
            WHERE chat_id = ? AND user_id = ? AND type = ?
            ORDER BY issued_at ASC LIMIT 1
        ''', (chat_id, user_id, p_type))
        result = cursor.fetchone()
        if result:
            punishment_id = result[0]
            cursor.execute('DELETE FROM punishments WHERE id = ?', (punishment_id,))
            conn.commit()
            print(f"Удалено наказание id {punishment_id} (тип {p_type}) для пользователя {user_id}.")
            return True
        else:
            print(f"Нет наказаний типа {p_type} для пользователя {user_id}.")
            return False

def remove_multiple_punishments(chat_id: int, user_id: int, p_type: str, count: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM punishments
            WHERE chat_id = ? AND user_id = ? AND type = ?
            ORDER BY issued_at ASC LIMIT ?
        ''', (chat_id, user_id, p_type, count))
        rows = cursor.fetchall()
        if rows:
            ids = [str(row[0]) for row in rows]
            placeholders = ",".join("?" for _ in ids)
            cursor.execute(f"DELETE FROM punishments WHERE id IN ({placeholders})", ids)
            conn.commit()
            print(f"Удалено {len(ids)} наказаний типа {p_type} для пользователя {user_id}.")
            
def get_punishments(chat_id: int, user_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, chat_id, user_id, type, issued_by, issued_at
            FROM punishments
            WHERE chat_id = ? AND user_id = ?
        ''', (chat_id, user_id))
        rows = cursor.fetchall()
    return rows

def update_balance(user_id: int, amount: int):
    """
    Обновляет баланс пользователя.
    :param user_id: идентификатор пользователя
    :param amount: изменение баланса (отрицательное значение списывает, положительное – прибавляет)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def initialize_banned_table():
    """Создаёт таблицу banned_users, если её ещё не существует."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS banned_users (
                chat_id INTEGER,
                user_id INTEGER,
                reason TEXT,
                banned_by INTEGER,
                banned_at INTEGER,
                PRIMARY KEY (chat_id, user_id)
            )
        ''')
        conn.commit()

# Функция проверки, забанен ли пользователь в беседе
async def is_user_banned(chat_id: int, user_id: int) -> bool:
    """Возвращает True, если пользователь забанен в указанной беседе."""
    async with await get_db_connection() as conn:
        async with conn.execute("SELECT 1 FROM bans WHERE chat_id = ? AND user_id = ?", (chat_id, user_id)) as cursor:
            row = await cursor.fetchone()
            return row is not None

def add_ban(chat_id: int, user_id: int, reason: str, banned_by: int):
    """Добавляет пользователя в список заблокированных для конкретной беседы."""
    banned_at = int(time.time())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO banned_users (chat_id, user_id, reason, banned_by, banned_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (chat_id, user_id, reason, banned_by, banned_at))
        conn.commit()

# Функция проверки времени последней ставки
def check_cooldown(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT last_bet_time FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result and time.time() - result[0] < BET_COOLDOWN:
        return False
    return True

# Функция обновления времени ставки
def update_bet_time(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_bet_time = ? WHERE user_id = ?", (time.time(), user_id))
    conn.commit()
    conn.close()

async def add_application(nickname: str, vk_page: str, verdict: str, reason: str = None):
    conn = await aiosqlite.connect(DB_PATH)
    await conn.execute(
        "INSERT INTO applications (nickname, vk_page, verdict, reason) VALUES (?, ?, ?, ?)",
        (nickname, vk_page, verdict, reason),
    )
    await conn.commit()
    await conn.close()

def get_vk_from_list(nickname: str) -> str:
    """Ищет ВКонтакте-страницу по нику в заявках."""
    user_info = get_info_from_list(nickname)
    return user_info.get("Ссылка на страницу в ВКонтакте", "Не найден") if "error" not in user_info else "Не найден"


# Функция получения баланса
def get_balance(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

# Функция обновления баланса
def update_balance(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# Функция выбора коэффициента
def get_multiplier(mode):
    return random.choices(*zip(*COEFFICIENTS[mode]))[0]

def remove_ban(chat_id: int, user_id: int):
    """Удаляет пользователя из списка заблокированных для конкретной беседы."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM banned_users WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        conn.commit()

if __name__ == "__main__":
    initialize_banned_table()

def is_user_banned(chat_id: int, user_id: int) -> bool:
    """Проверяет, находится ли пользователь в списке заблокированных."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM banned_users WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        return cursor.fetchone() is not None

def add_user(user_id: int) -> bool:
    """Регистрирует нового пользователя, если его ещё нет."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        conn.close()
        return False
    cursor.execute("INSERT INTO users (user_id, registration_date) VALUES (?, ?)",
                   (user_id, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()
    return True

def get_registration_date(user_id: int) -> str:
    """Возвращает дату регистрации пользователя."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT registration_date FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "Неизвестно"

def get_balance(user_id: int) -> int:
    """Возвращает баланс пользователя (коины)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def get_points(user_id: int) -> int:
    """Возвращает количество баллов пользователя."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def update_points_balance(user_id: int, amount: int):
    """Обновляет баллы пользователя (прибавляет/вычитает указанную сумму)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_total_messages(user_id: int) -> int:
    """Возвращает общее количество сообщений пользователя."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT total_messages FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def get_last_message_time(user_id: int) -> str:
    """
    Возвращает время последнего сообщения пользователя в формате 'YYYY-MM-DD HH:MM:SS'.
    Если данных нет, возвращает "Нет данных".
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_message_time FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result and result[0]:
        # Если значение хранится как Unix timestamp (секунды)
        return datetime.fromtimestamp(result[0]).strftime("%Y-%m-%d %H:%M:%S")
    return "Нет данных"

def add_column_if_not_exists(column_name: str, column_definition: str):
    """Добавляет колонку в таблицу users, если её нет."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    if not any(col[1] == column_name for col in columns):
        cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_definition}")
        conn.commit()
    conn.close()


def initialize_columns():
    """Инициализирует дополнительные колонки в таблице users."""
    add_column_if_not_exists("points", "INTEGER DEFAULT 0")
    add_column_if_not_exists("total_messages", "INTEGER DEFAULT 0")
    add_column_if_not_exists("last_message_time", "INTEGER DEFAULT 0")
    add_column_if_not_exists("last_reward_time", "INTEGER DEFAULT 0")
    add_column_if_not_exists("last_russian_roulette", "INTEGER DEFAULT 0")

# ===== Функции работы с БД =====
def add_user(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, balance, last_duel_time) VALUES (?, ?, ?)",
                   (user_id, 100, 0))  # Стартовый баланс и кд дуэли
    conn.commit()
    conn.close()


def get_balance(user_id: int) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0


def update_balance(user_id: int, amount: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


# ====== Работа с БД ======
def add_user(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, balance, last_duel_time) VALUES (?, ?, ?)",
                   (user_id, 100, 0))
    conn.commit()
    conn.close()


def get_balance(user_id: int) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def add_user(user_id: int) -> bool:
    """Регистрирует нового пользователя, если его ещё нет."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        conn.close()
        return False  # Пользователь уже существует
    cursor.execute("INSERT INTO users (user_id, registration_date) VALUES (?, ?)",
                   (user_id, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()
    return True


def get_balance(user_id: int) -> int:
    """Возвращает баланс пользователя."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def get_user_message_stats(user_id: int):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Проверяем, что запрос возвращает корректные данные
    cursor.execute("SELECT total_messages, last_message_time FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        total_messages, last_message_timestamp = result
        # Если нужно, выводим информацию для диагностики
        print(f"total_messages: {total_messages}, last_message_timestamp: {last_message_timestamp}")
        
        # Форматируем время
        formatted_time = datetime.fromtimestamp(last_message_timestamp).strftime("%d-%m-%Y %H:%M")
        
        return total_messages, formatted_time
    else:
        return 0, "Нет данных"



def get_points(user_id: int) -> int:
    """Возвращает количество баллов пользователя."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0


def update_points_balance(user_id: int, amount: int):
    """Обновляет баллы пользователя (принимает отрицательное значение для вычитания)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def remove_user(user_id: int):
    """Удаляет пользователя из базы данных."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
def set_user_level(user_id: int, level: int):
    """Устанавливает уровень (статус) пользователя."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET level = ? WHERE user_id = ?", (level, user_id))
    conn.commit()
    conn.close()


def get_user_level(user_id: int) -> int:
    """Возвращает уровень пользователя."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT level FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 1

def extract_mention_id(mention):
    """ Извлекает ID из упоминания @id123 или [id123|Имя] """
    match = re.search(r'id(\d+)', mention)
    return int(match.group(1)) if match else None

def get_nickname(user_id):
    """ Получает никнейм пользователя из базы, если нет  — возвращает имя ВК """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT nickname FROM nicknames WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    return f"id{user_id}"  # Если ника нет, используем ID



# =======================================
# Утилита: получение user_id из упоминания
# =======================================

def get_user_id_from_mention(mention: str) -> int:
    """
    Извлекает user_id из упоминания вида "[id12345|Name]".
    Если передана строка с числом, возвращает его как int.
    """
    if "[id" in mention and "|" in mention:
        try:
            return int(mention.split("[id")[1].split("|")[0])
        except (IndexError, ValueError):
            return None
    if mention.isdigit():
        return int(mention)
    return None


def get_user_role(user_id: int) -> str:
    """Возвращает роль пользователя."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "user"


def update_user_role(user_id: int, new_role: str):
    """Обновляет роль пользователя в базе данных."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE user_id = ?", (new_role, user_id))
    conn.commit()
    conn.close()


def get_all_users_with_balance():
    """Возвращает список всех пользователей с их балансами."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, balance FROM users")
    users = cursor.fetchall()
    conn.close()
    return users


def get_moderators():
    """Возвращает список пользователей с уровнем больше 1 (модераторов)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, level FROM users WHERE level > 1")
    moderators = cursor.fetchall()
    conn.close()
    return moderators


def get_staff():
    """Возвращает список сотрудников с ролями (для администрирования)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, role FROM users WHERE role IN ('owner', 'depspec', 'senadmin', 'admin', 'senmoder', 'moder')"
    )
    staff = cursor.fetchall()
    conn.close()
    return staff

def add_user(user_id: int) -> bool:
    """Регистрирует пользователя, если его ещё нет, и сохраняет дату регистрации."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            return False  # Пользователь уже есть
        cursor.execute("INSERT INTO users (user_id, registration_date) VALUES (?, ?)",
                       (user_id, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
    return True

def get_registration_date(user_id: int) -> str:
    """Возвращает дату регистрации пользователя."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT registration_date FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
    return row[0] if row else None

def add_chat(chat_id: int, chat_name: str):
    """Добавляет идентификатор чата и его название в БД, если их ещё нет."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("INSERT OR IGNORE INTO chats (chat_id, chat_name) VALUES (?, ?)", (chat_id, chat_name))
    
    # Если чат уже есть, обновляем его название (вдруг оно изменилось)
    cursor.execute("UPDATE chats SET chat_name = ? WHERE chat_id = ?", (chat_name, chat_id))
    
    conn.commit()
    conn.close()

def get_all_chats() -> list:
    """Возвращает список всех синхронизированных чатов."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id FROM chats")
        rows = cursor.fetchall()
    return [row[0] for row in rows]


def get_user_role(user_id: int) -> str:
    """Возвращает роль пользователя."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "user"


def update_user_role(user_id: int, new_role: str):
    """Обновляет роль пользователя в базе данных."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE user_id = ?", (new_role, user_id))
    conn.commit()
    conn.close()

def get_staff():
    """Возвращает список сотрудников с ролями (для администрирования)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, role FROM users WHERE role IN ('owner', 'depspec', 'senadmin', 'admin', 'senmoder', 'moder')"
    )
    staff = cursor.fetchall()
    conn.close()
    return staff

# =======================================
# Функция логирования событий
# =======================================
async def log_event(event_message: str):
    """
    Отправляет лог-сообщение в отдельную беседу.
    :param event_message: текст события для логирования.
    """
    try:
        await bot.api.messages.send(
            peer_id=LOG_CHAT_ID,
            message=event_message,
            random_id=0
        )
    except Exception as e:
        print("Ошибка логирования:", e)

async def log_staff(event_message: str):
    """
    Отправляет лог-сообщение в отдельную беседу.
    :param event_message: текст события для логирования.
    """
    try:
        await bot.api.messages.send(
            peer_id=LOG_STAFF_ID,
            message=event_message,
            random_id=0
        )
    except Exception as e:
        print("Ошибка логирования:", e)

async def main():
    try:
        print("Инициализация таблиц...")
        initialize_duel_table()
        print("Таблицы инициализированы.")
        print("Запуск бота...")
        await bot.run_polling()
    except Exception as e:
        import traceback
        print("Ошибка при запуске бота:")
        print(traceback.format_exc())


# ==============================
# Утилиты
# ==============================

async def get_user_id_from_mention(mention: str) -> int:
    """
    Извлекает user_id из упоминания вида "[id12345|Name]".
    Если передана строка с числом, возвращает его как int.
    """
    if "[id" in mention and "|" in mention:
        try:
            return int(mention.split("[id")[1].split("|")[0])
        except (IndexError, ValueError):
            return None
    if mention.isdigit():
        return int(mention)
    return None

async def get_user_name(user_id: int) -> str:
    """Получает имя пользователя через API ВКонтакте."""
    try:
        user_info = await bot.api.users.get(user_ids=user_id)
        user = user_info[0]
        return f"{user.first_name} {user.last_name}"
    except Exception:
        return f"User {user_id}"
    
def set_user_level(user_id: int, level: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET level = ? WHERE user_id = ?", (level, user_id))
    conn.commit()
    conn.close()

def get_user_level(user_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT level FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 1

def get_moderators():
    # Для команды /moders мы выбираем всех пользователей, у которых роль не "user"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, level FROM users WHERE role != 'user'")
    moderators = cursor.fetchall()
    conn.close()
    return moderators


async def get_user_id_from_mention(mention: str) -> int:
    """
    Извлекает user_id из упоминания вида "[id12345|Name]".
    Если передана строка с числом, возвращает его как int.
    """
    if "[id" in mention and "|" in mention:
        try:
            return int(mention.split("[id")[1].split("|")[0])
        except (IndexError, ValueError):
            return None
    if mention.isdigit():
        return int(mention)
    return None


def extract_user_id(mention: str) -> int:
    """Быстрый способ извлечь user_id из упоминания с помощью регулярного выражения."""
    match = re.search(r"\[id(\d+)\|", mention)
    return int(match.group(1)) if match else None


def get_today_date() -> str:
    """Возвращает сегодняшнюю дату в формате YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")

async def get_user_name(user_id: int) -> str:
    """Получает имя пользователя через API ВКонтакте."""
    try:
        user_info = await bot.api.users.get(user_ids=user_id)
        user = user_info[0]
        return f"{user.first_name} {user.last_name}"
    except Exception:
        return f"User {user_id}"

async def get_user_id_from_mention(mention: str) -> int:
    """
    Извлекает user_id из различных форматов:
      - Упоминание вида "[id12345|Name]"
      - Ссылка вида "https://vk.com/id12345"
      - Числовая строка
    """
    # Если передана ссылка вида "https://vk.com/id12345"
    if mention.startswith("https://vk.com/"):
        # Попробуем извлечь через регулярное выражение
        match = re.search(r"vk\.com/(id\d+)", mention)
        if match:
            uid_str = match.group(1)  # Например, "id12345"
            return int(uid_str.replace("id", ""))
    # Если передано упоминание вида "[id12345|Name]"
    if "[id" in mention and "|" in mention:
        try:
            return int(mention.split("[id")[1].split("|")[0])
        except (IndexError, ValueError):
            return None
    # Если это просто число
    if mention.isdigit():
        return int(mention)
    return None

async def get_user_name(user_id: int) -> str:
    """Получает имя пользователя через API ВКонтакте."""
    try:
        user_info = await bot.api.users.get(user_ids=user_id)
        user = user_info[0]
        return f"{user.first_name} {user.last_name}"
    except Exception:
        return f"User {user_id}"


async def get_user_id_from_mention(mention: str) -> int:
    """
    Извлекает user_id из упоминания вида "[id12345|Name]".
    Если передана строка с числом, возвращает его как int.
    """
    if "[id" in mention and "|" in mention:
        try:
            return int(mention.split("[id")[1].split("|")[0])
        except (IndexError, ValueError):
            return None
    if mention.isdigit():
        return int(mention)
    return None


def extract_user_id(mention: str) -> int:
    """Быстрый способ извлечь user_id из упоминания с помощью регулярного выражения."""
    match = re.search(r"\[id(\d+)\|", mention)
    return int(match.group(1)) if match else None


def get_today_date() -> str:
    """Возвращает сегодняшнюю дату в формате YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")

async def get_user_name(user_id: int) -> str:
    try:
        user_info = await bot.api.users.get(user_ids=user_id)
        user = user_info[0]
        return f"{user.first_name} {user.last_name}"
    except Exception:
        return f"User {user_id}"

async def get_user_id_from_mention(mention: str) -> int:
    if mention.startswith("https://vk.com/"):
        match = re.search(r"vk\.com/(id\d+)", mention)
        if match:
            uid_str = match.group(1)
            return int(uid_str.replace("id", ""))
    if "[id" in mention and "|" in mention:
        try:
            return int(mention.split("[id")[1].split("|")[0])
        except (IndexError, ValueError):
            return None
    if mention.isdigit():
        return int(mention)
    return None

def get_today_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")

async def get_user_id_from_mention(mention: str) -> int:
    """
    Извлекает user_id из упоминания вида "[id12345|Name]", ссылки вида "https://vk.com/id12345" или "https://vk.com/username".
    Если передана строка с числом, возвращает его как int.
    """
    # Обработка упоминания в формате [id12345|Name]
    if "[id" in mention and "|" in mention:
        try:
            return int(mention.split("[id")[1].split("|")[0])
        except (IndexError, ValueError):
            return None

    # Обработка ссылки с никнеймом вида "https://vk.com/username"
    if "https://vk.com" in mention:
        username = mention.split("https://vk.com/")[-1]  # Извлекаем username
        if username:
            # Делаем запрос к VK API для получения ID по username
            user_id = await get_vk_user_id_by_username(username)
            if user_id:
                return user_id
            else:
                return None

    # Если строка является числом, возвращаем её как int
    if mention.isdigit():
        return int(mention)
    
    return None

async def get_vk_user_id_by_username(username: str) -> int:
    """
    Получаем user_id по username через VK API.
    """
    access_token = 'YOUR_VK_ACCESS_TOKEN'  # Ваш токен доступа
    url = f'https://api.vk.com/method/users.get?user_ids={username}&access_token={access_token}&v=5.131'
    response = requests.get(url).json()
    if 'response' in response and len(response['response']) > 0:
        return response['response'][0]['id']
    return None



async def add_application(nick, verdict, reason):
    # Здесь логика добавления заявления в базу или обработка отказа.
    # Например, можно записать данные в таблицу applications
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO applications (nickname, verdict, reason) VALUES (?, ?, ?)",
                   (nick, verdict, reason))
    conn.commit()
    conn.close()

async def add_approve(nick, verdict):
    # Здесь логика добавления заявления в базу или обработка отказа.
    # Например, можно записать данные в таблицу applications
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO applications (nickname, verdict) VALUES (?, ?)",
                   (nick, verdict))
    conn.commit()
    conn.close()

async def get_user_link(uid: int):
    try:
        # Получаем информацию о пользователе с помощью API
        user_info = await bot.api.users.get(user_ids=[uid])
        
        # Если пользователь найден, извлекаем его имя
        if user_info:
            first_name = user_info[0].first_name
            last_name = user_info[0].last_name
            return f"{first_name} {last_name}"  # Возвращаем полное имя пользователя
        else:
            return "Неизвестный пользователь"
    except Exception as e:
        print(f"Ошибка при получении информации о пользователе: {e}")
        return "Неизвестный пользователь"

async def get_user_first_name(uid):
    """
    Получаем имя пользователя по его ID. Возвращаем только имя, без фамилии.
    """
    try:
        user_info = await bot.api.users.get(user_ids=uid)
        # Возвращаем только первое имя
        return user_info[0].first_name if user_info else 'Неизвестный'
    except Exception as e:
        print(f"Ошибка при получении данных пользователя: {e}")
        return 'Неизвестный'



async def get_all_applications():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT nickname, verdict, reason, vk FROM applications")
    apps = cursor.fetchall()
    conn.close()
    return apps



async def resolve_user_id(arg: str, bot):
    print(f"[DEBUG] resolve_user_id вызвана с аргументом: {arg}")

    # 0. Проверка формата вида [id618936124|@korton5]
    pattern_mention = r'^\[id(\d+)\|.*\]$'
    match = re.match(pattern_mention, arg)
    if match:
        print(f"[DEBUG] Найден формат упоминания: id = {match.group(1)}")
        return int(match.group(1))
    
    # 1. Если аргумент является ссылкой вида vk.com/..., например, https://vk.com/korton5 или https://vk.com/id1234567
    pattern_full_url = r'(?:https?://)?(?:www\.)?vk\.com/([^/\?]+)'
    match = re.match(pattern_full_url, arg)
    if match:
        username_or_id = match.group(1)
        print(f"[DEBUG] Извлечено имя или id из URL: {username_or_id}")
        # Если строка начинается с "id" и за ней цифры, это числовой ID
        id_match = re.match(r'id(\d+)', username_or_id, re.IGNORECASE)
        if id_match:
            print(f"[DEBUG] Извлечено числовое id из URL: {id_match.group(1)}")
            return int(id_match.group(1))
        else:
            try:
                # Используем параметр user_ids для поиска по короткому имени
                users = await bot.api.users.get(user_ids=username_or_id)
                print(f"[DEBUG] Результат bot.api.users.get (user_ids): {users}")
                if users and len(users) > 0:
                    return users[0].id
            except Exception as e:
                print(f"[ERROR] Ошибка при вызове bot.api.users.get: {e}")
            return None
    
    # 2. Если аргумент начинается с "id" (например, "id1234567")
    match = re.match(r'id(\d+)', arg, re.IGNORECASE)
    if match:
        print(f"[DEBUG] Найден id с префиксом: {match.group(1)}")
        return int(match.group(1))
    
    # 3. Если аргумент состоит только из цифр
    if arg.isdigit():
        print(f"[DEBUG] Аргумент состоит только из цифр: {arg}")
        return int(arg)
    
    # 4. Если аргумент начинается с "@", удаляем его
    if arg.startswith('@'):
        arg = arg.lstrip('@')
        print(f"[DEBUG] Удалили @, осталось: {arg}")
    
    # 5. Пытаемся получить пользователя по имени через API
    try:
        users = await bot.api.users.get(user_ids=arg)
        print(f"[DEBUG] Результат bot.api.users.get (final): {users}")
        if users and len(users) > 0:
            return users[0].id
    except Exception as e:
        print(f"[ERROR] Ошибка при вызове bot.api.users.get: {e}")
    
    return None

async def get_application_verdict(nickname: str) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT verdict FROM applications WHERE nickname = ?", (nickname,)) as cursor:
            row = await cursor.fetchone()
    return row[0] if row else None

def calculate_days_until_promotion(last_promotion_date: str, current_position: str) -> str:
    """Функция для вычисления оставшихся дней до повышения."""
    
    # Парсим дату последнего повышения
    try:
        last_promotion = datetime.strptime(last_promotion_date, "%d.%m.%Y")
    except ValueError:
        return "Неверный формат даты."

    # Рассчитываем количество дней с момента последнего повышения
    days_since_promotion = (datetime.now() - last_promotion).days

    # Получаем количество дней до следующего повышения
    promotion_period = PROMOTIONS.get(current_position, None)
    if promotion_period is None:
        return "Неизвестная должность."

    # Проверка, если срок повышения уже подошел
    remaining_days = promotion_period - days_since_promotion

    if remaining_days <= 0:
        return f"Срок повышения подошел."
    else:
        return f"{remaining_days}"

def calculate_days_until_iskl(last_promotion_date: str, current_position: str) -> str:
    """Функция для вычисления оставшихся дней до повышения."""
    
    # Парсим дату последнего повышения
    try:
        last_promotion = datetime.strptime(last_promotion_date, "%d.%m.%Y")
    except ValueError:
        return "Неверный формат даты."

    # Рассчитываем количество дней с момента последнего повышения
    days_since_promotion = (datetime.now() - last_promotion).days

    # Получаем количество дней до следующего повышения
    promotion_period = ISKL.get(current_position, None)
    if promotion_period is None:
        return "нет"

    # Проверка, если срок повышения уже подошел
    remaining_days = promotion_period - days_since_promotion

    if remaining_days <= 0:
        return f"срок подошел"
    else:
        return f"{remaining_days}"

# ================================
# Утилита для извлечения никнейма из аргумента
# ================================
def get_nickname(user_id):
    conn = sqlite3.connect("database.db")  # Укажи путь к своей базе
    cursor = conn.cursor()

    cursor.execute("SELECT nickname FROM nicknames WHERE vk_id = ?", (user_id,))
    result = cursor.fetchone()

    conn.close()

    if result is None:
        return None  # Если никнейм не найден, возвращаем None

    return str(result[0]).strip()  # Приводим к строке и убираем пробелы

def only_chats(func):
    """Декоратор, который разрешает обработку сообщений только из бесед (чатов)."""
    async def wrapper(message, *args, **kwargs):
        # В личных сообщениях peer_id совпадает с id пользователя (меньше 2000000000),
        # а в беседах peer_id >= 2000000000
        if message.peer_id < 2000000000:
            return  # Игнорируем сообщение из ЛС
        return await func(message, *args, **kwargs)
    return wrapper

# ==============================
# Обработчики команд бота
# ==============================
@bot.on.message(text="/bid")
@bot.on.message(text="+bid")
@bot.on.message(text="!bid")
@only_chats
async def bid_handler(message):
    sender_role = get_user_role(message.from_id)
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["senadmin"]:
        await message.reply("Недостаточно прав.")
        return
    # Проверяем, что команда вызвана в беседе (peer_id >= 2000000000)
    if message.peer_id >= 2000000000:
        chat_id = message.peer_id - 2000000000
        await message.reply(f"ID этой беседы: {chat_id}")
    else:
        await message.reply("Эта команда доступна только в беседах.")

@bot.on.message(text="/aprint <chat_id:int> <text>")
@bot.on.message(text="+aprint <chat_id:int> <text>")
@bot.on.message(text="!aprint <chat_id:int> <text>")
async def print_handler(message, chat_id: int, text: str):
    # Проверяем, имеет ли отправитель достаточные права (только depspec и owner)
    sender_role = get_user_role(message.from_id)
    if sender_role not in ("senmoder", "admin", "senadmin", "depspec", "owner"):
        await message.reply("Недостаточно прав!")
        return

    peer_id = 2000000000 + chat_id  # Конвертируем chat_id в peer_id

    try:
        # Получаем название беседы
        chat_info = await bot.api.messages.get_conversations_by_id(peer_ids=peer_id)
        chat_name = chat_info.items[0].chat_settings.title if chat_info.items else f"ID {chat_id}"

        # Отправляем сообщение в указанную беседу
        await bot.api.messages.send(
            peer_id=peer_id,
            message=text,
            random_id=0
        )

        # Подтверждаем успешную отправку с названием беседы
        await message.reply(f"Сообщение успешно отправлено в беседу «{chat_name}».")
    
    except Exception as e:
        await message.reply(f"Ошибка при отправке сообщения: {e}")


@bot.on.message(text=[
    "/id <arg>", "/ид <arg>", "/айди <arg>", 
    "+id <arg>", "+ид <arg>", "+айди <arg>", 
    "!id <arg>", "!ид <arg>", "!айди <arg>"
])
async def id_handler(message, arg: str):
    print(f"[DEBUG] id_handler вызвана с аргументом: {arg}")
    uid = await resolve_user_id(arg, bot)
    if not uid:
        await message.reply("Не удалось извлечь идентификатор пользователя из аргумента.")
        return
    await message.reply(f"Оригинальная ссылка на пользователя: https://vk.com/id{uid}")

@bot.on.message(text=[
    "/id", "/ид", "/айди", 
    "+id", "+ид", "+айди", 
    "!id", "!ид", "!айди"
])
async def id_reply_handler(message):
    if message.reply_message:
        uid = message.reply_message.from_id
        await message.reply(f"Оригинальная ссылка на пользователя: https://vk.com/id{uid}")
    else:
        await message.reply("Вы не указали пользователя")

@bot.on.message(text="/снят <arg>")
@bot.on.message(text="+снят <arg>")
@bot.on.message(text="!снят <arg>")
async def snjat_handler(message, arg: str):
    # Разбиваем аргумент: первый элемент – упоминание/идентификатор, остальное – причина
    parts = arg.split(" ", 1)
    target = parts[0]
    reason = parts[1] if len(parts) > 1 else "Не указана причина"
    
    uid = await get_user_id_from_mention(target)
    if not uid:
        await message.reply("Не удалось извлечь идентификатор пользователя.")
        return

    chat_ids = get_all_chats()
    if not chat_ids:
        await message.reply("Нет синхронизированных бесед.")
        return

    kicked_chats = []  # Чаты, из которых пользователя успешно исключили.
    
    for chat_id in chat_ids:
        try:
            await bot.api.messages.remove_chat_user(chat_id=chat_id, member_id=uid)
            kicked_chats.append(chat_id)
        except Exception as e:
            error_message = str(e)
            # Если ошибка связана с тем, что пользователя нет в беседе, пропускаем её.
            if ("Пользователь не найден" in error_message or
                "не состоит" in error_message or
                "not found" in error_message):
                continue
            else:
                chat_name = await get_chat_name(chat_id)  # Получаем название беседы
                await message.reply(f"Я не могу кикнуть пользователя в беседе {chat_name}, необходимо забрать администратора (звездочку).")

    if kicked_chats:
        admin_id = message.from_id
        admin_name = await get_user_name(admin_id)
        user_name = await get_user_name(uid)
        broadcast_text = (f"[https://vk.com/id{admin_id}|{admin_name}] исключил-(а) "
                          f"[https://vk.com/id{uid}|{user_name}] из всех бесед модерации сервера <<86>>.\n"
                          f"Причина: {reason}")
        for chat_id in kicked_chats:
            try:
                peer_id = 2000000000 + chat_id
                await bot.api.messages.send(peer_id=peer_id, message=broadcast_text, random_id=0)
            except Exception as e:
                print(f"Ошибка при отправке в чат {chat_id}: {e}")


@bot.on.message(text="/снят")
@bot.on.message(text="+снят")
@bot.on.message(text="!снят")
async def snjat_reply_handler(message):
    if not message.reply_message:
        await message.reply("Вы не указали пользователя")
        return

    uid = message.reply_message.from_id
    parts = message.text.split(" ", 1)
    reason = parts[1] if len(parts) > 1 else "Не указана причина"

    chat_ids = get_all_chats()
    if not chat_ids:
        await message.reply("Нет синхронизированных бесед.")
        return

    failed = []  # Чаты, из которых не удалось исключить пользователя
    kicked_chats = []  # Чаты, из которых пользователя исключили
    for chat_id in chat_ids:
        try:
            # Пытаемся исключить пользователя из чата
            await bot.api.messages.remove_chat_user(chat_id=chat_id, member_id=uid)
            kicked_chats.append(chat_id)
        except Exception as e:
            error_message = str(e)
            # Если ошибка связана с тем, что пользователя нет в беседе, пропускаем её.
            if ("Пользователь не найден" in error_message or
                "не состоит" in error_message or
                "not found" in error_message):
                continue
            else:
                # Если ошибка другая, отправляем сообщение
                chat_name = await get_chat_name(chat_id)  # Получаем название беседы
                await message.reply(f"Я не могу кикнуть пользователя в беседе {chat_name}, необходимо забрать администратора (звездочку).")

    if kicked_chats:
        admin_id = message.from_id
        admin_name = await get_user_name(admin_id)
        user_name = await get_user_name(uid)
        broadcast_text = (f"[https://vk.com/id{admin_id}|{admin_name}] исключил-(а) "
                          f"[https://vk.com/id{uid}|{user_name}] из всех бесед модерации сервера <<86>>.\n"
                          f"Причина: {reason}")
        for chat_id in kicked_chats:
            try:
                # Для отправки сообщения в беседе используем peer_id = 2000000000 + chat_id
                peer_id = 2000000000 + chat_id
                await bot.api.messages.send(peer_id=peer_id, message=broadcast_text, random_id=0)
            except Exception as e:
                print(f"Ошибка при отправке в чат {chat_id}: {e}")



@bot.on.chat_message(text="/sync")
async def gsync_handler(message):
    chat_id = message.peer_id - 2000000000  # Определяем chat_id

    # Получаем информацию о беседе
    chat_info = await bot.api.messages.get_conversations_by_id(peer_ids=message.peer_id)
    chat_name = chat_info.items[0].chat_settings.title if chat_info.items else "Неизвестная беседа"

    add_chat(chat_id, chat_name)  # Добавляем в БД

    await message.reply(f"Беседа \"{chat_name}\" (ID: {chat_id}) успешно синхронизирована с базой данных.")


@bot.on.message(text="/kick <arg>")
@bot.on.message(text="/кик <arg>")
@bot.on.message(text="/исключить <arg>")
@bot.on.message(text="/выкинуть <arg>")
@bot.on.message(text="/убрать <arg>")
@bot.on.message(text="!kick <arg>")
@bot.on.message(text="!кик <arg>")
@bot.on.message(text="!исключить <arg>")
@bot.on.message(text="!выкинуть <arg>")
@bot.on.message(text="!убрать <arg>")
@bot.on.message(text="+kick <arg>")
@bot.on.message(text="+кик <arg>")
@bot.on.message(text="+исключить <arg>")
@bot.on.message(text="+выкинуть <arg>")
@bot.on.message(text="+убрать <arg>")
async def kick_handler(message, arg: str):
    # Извлекаем ID пользователя и причину
    parts = arg.split(" ", 1)
    uid = await get_user_id_from_mention(parts[0])
    if not uid:
        await message.reply("Не удалось извлечь идентификатор пользователя.")
        return

    reason = parts[1] if len(parts) > 1 else "не указана."  # Если причина есть, то берем, если нет  — по умолчанию

    chat_id = message.chat_id  # текущая беседа
    admin_id = message.from_id
    admin_name = await get_user_name(admin_id)
    user_name = await get_user_name(uid)

    try:
        # Исключаем пользователя из беседы
        await bot.api.messages.remove_chat_user(chat_id=chat_id, member_id=uid)
        # Отправляем сообщение с причиной кика
        await message.reply(f"[https://vk.com/id{admin_id}|{admin_name}] исключил-(а) "
                            f"[https://vk.com/id{uid}|{user_name}] из беседы. \n\nПричина: {reason}")
    except Exception as e:
        await message.reply(f"Ошибка при исключении пользователя: {e}")

@bot.on.message(text="/kick")
@bot.on.message(text="/кик")
@bot.on.message(text="/исключить")
@bot.on.message(text="/выкинуть")
@bot.on.message(text="/убрать")
@bot.on.message(text="!kick")
@bot.on.message(text="!кик")
@bot.on.message(text="!исключить")
@bot.on.message(text="!выкинуть")
@bot.on.message(text="!убрать")
@bot.on.message(text="+kick")
@bot.on.message(text="+кик")
@bot.on.message(text="+исключить")
@bot.on.message(text="+выкинуть")
@bot.on.message(text="+убрать")
async def kick_reply_handler(message):
    if message.reply_message:
        # Получаем ID пользователя и причину
        uid = message.reply_message.from_id
        parts = message.text.split(" ", 1)
        reason = parts[1] if len(parts) > 1 else "не указана."  # Если причина есть, то берем, если нет  — по умолчанию

        chat_id = message.chat_id
        admin_id = message.from_id
        admin_name = await get_user_name(admin_id)
        user_name = await get_user_name(uid)

        try:
            # Исключаем пользователя из беседы
            await bot.api.messages.remove_chat_user(chat_id=chat_id, member_id=uid)
            # Отправляем сообщение с причиной кика
            await message.reply(f"[https://vk.com/id{admin_id}|{admin_name}] исключил-(а) "
                                f"[https://vk.com/id{uid}|{user_name}] из беседы. \n\nПричина: {reason}")
        except Exception as e:
            await message.reply(f"Ошибка при исключении пользователя: {e}")
    else:
        await message.reply("Вы не указали пользователя")


@bot.on.message(text="/reg")
@bot.on.message(text="+reg")
@bot.on.message(text="!reg")
@only_chats
async def register_handler(message):
    user_id = message.from_id
    if add_user(user_id):
        await message.reply("Вы успешно зарегистрированы.")
    else:
        await message.reply("Вы уже зарегистрированы в системе.")

@bot.on.message(text="/buy")
@bot.on.message(text="/купить")
@bot.on.message(text="+buy")
@bot.on.message(text="+купить")
@bot.on.message(text="!buy")
@bot.on.message(text="!купить")
async def ainfo_no_argument(message):
    await message.reply("Вы не указали номер товара")

@bot.on.message(text="/buy <item_number:int>")
@bot.on.message(text="/купить <item_number:int>")
@bot.on.message(text="+buy <item_number:int>")
@bot.on.message(text="+купить <item_number:int>")
@bot.on.message(text="!buy <item_number:int>")
@bot.on.message(text="!купить <item_number:int>")
async def buy_handler(message, item_number: int):
    user_level = get_user_level(message.from_id)
    # Разрешены только уровни 1, 2 и 3
    if user_level > 3:
        await message.reply("Эта команда доступна только рядовой модерации.")
        return
    """
    Покупка товара из магазина.
    """
    user_id = message.from_id
    add_user(user_id)  # Регистрируем пользователя, если его ещё нет

    # Здесь проверяем наличие товара в магазине
    item = None
    for category, items in SHOP.items():
        if item_number in items:
            item = items[item_number]
            break
    if not item:
        await message.reply("Такого товара нет в магазине.")
        return

    balance = get_balance(user_id)
    price = item["price"]
    if balance < price:
        await message.reply("Недостаточно M-Coins для покупки.")
        return

    update_balance(user_id, -price)
    new_balance = get_balance(user_id)
    response = f"✅ Вы успешно купили {item['name']} за {price} коинов! Ваш новый баланс: {new_balance} M-Coins."
    user_name = await get_user_name(user_id)
    await message.reply(response)
    # Логирование покупки
    log_text = (f"[#LOGS_STORE] [id{user_id}|{user_name}] купил '{item['name']}' (товар №{item_number}) "
                f"за {price} коинов. Новый баланс: {new_balance} M-Coins. \n\n@n.ivanov.official")
    await log_event(log_text)

@bot.on.message(text="/tbalance")
@bot.on.message(text="/top")
@bot.on.message(text="/топ")
@bot.on.message(text="!tbalance")
@bot.on.message(text="!top")
@bot.on.message(text="!топ")
@bot.on.message(text="+tbalance")
@bot.on.message(text="+top")
@bot.on.message(text="+топ")
@only_chats
async def top_balance_handler(message):
    users = get_all_users_with_balance()
    if not users:
        await message.reply("⛔ Список пользователей пуст.")
        return

    sorted_users = sorted(users, key=lambda x: x[1], reverse=True)
    top_text = "🏆 Топ-10 пользователей по балансу:\n"
    for i, (user_id, balance) in enumerate(sorted_users[:10], 1):
        user_name = await get_user_name(user_id)
        top_text += f"{i}. [https://vk.com/id{user_id}|{user_name}]  — {balance} M-Coins\n"
    await message.reply(top_text)


@bot.on.message(text="/adelete")
@bot.on.message(text="+adelete")
@bot.on.message(text="!adelete")
@bot.on.message(text="/удалить")
@bot.on.message(text="+удалить")
@bot.on.message(text="!удалить")
async def ainfo_no_argument(message):
    # Получаем роль отправителя
    sender_role = get_user_role(message.from_id)
    # Если роль ниже "moder" – выдаём сообщение об отсутствии прав
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["depspec"]:
        await message.reply("Недостаточно прав.")
        return
    await message.reply("Вы не указали пользователя")

@bot.on.message(text="/adelete <mention>")
@bot.on.message(text="+adelete <mention>")
@bot.on.message(text="!adelete <mention>")
@bot.on.message(text="/удалить <mention>")
@bot.on.message(text="+удалить <mention>")
@bot.on.message(text="!удалить <mention>")
async def delete_user_handler(message, mention: str):
    # Получаем роль отправителя
    sender_role = get_user_role(message.from_id)
    # Если роль ниже "moder" – выдаём сообщение об отсутствии прав
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["depspec"]:
        await message.reply("Недостаточно прав.")
        return

    user_id = await get_user_id_from_mention(mention)
    if not user_id:
        await message.reply("Не удалось определить пользователя по упоминанию.")
        return

    try:
        remove_user(user_id)
        await message.reply(f"Аккаунт [https://vk.com/id{user_id}|пользователя] был успешно удален.")
    except Exception as e:
        await message.reply(f"Произошла ошибка при удалении пользователя: {e}")


@bot.on.message(text="/addcoins <mention> <amount:int>")
@bot.on.message(text="+addcoins <mention> <amount:int>")
@bot.on.message(text="!addcoins <mention> <amount:int>")
async def add_coins_handler(message, mention: str, amount: int):
    if message.from_id not in ADMINS:
        await message.reply("Недостаточно прав.")
        return

    if amount <= 0:
        await message.reply("Сумма должна быть больше 0.")
        return

    user_id = await get_user_id_from_mention(mention)
    if not user_id:
        await message.reply("Не удалось определить пользователя.")
        return

    update_balance(user_id, amount)
    new_balance = get_balance(user_id)
    await message.reply(f"Вы успешно выдали {amount} M-Coins [id{user_id}|пользователю]. \n\n💳 Новый баланс коинов: {new_balance}.")


@bot.on.message(text="/editcoins <mention> <amount>")
@bot.on.message(text="+editcoins <mention> <amount>")
@bot.on.message(text="+editcoins <mention> <amount>")
async def edit_balance_handler(message, mention: str, amount: str):
    try:
        staff = get_staff()
        user_role = next((role for uid, role in staff if uid == message.from_id), None)
        if user_role not in ['owner']:
            await message.reply("Недостаточно прав.")
            return

        target_id = await get_user_id_from_mention(mention)
        if not target_id:
            await message.reply("Не удалось определить пользователя.")
            return

        amount = int(amount)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, target_id))
        conn.commit()
        conn.close()

        target_name = await get_user_name(target_id)
        await message.reply(f"Баланс {target_name} изменен на {amount} коинов.")
    except ValueError:
        await message.reply("Укажите корректную сумму.")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")


@bot.on.message(text="/lvl <mention> <level:int>")
@bot.on.message(text="+lvl <mention> <level:int>")
@bot.on.message(text="!lvl <mention> <level:int>")
@bot.on.message(text="/уровень <mention> <level:int>")
@bot.on.message(text="+уровень <mention> <level:int>")
@bot.on.message(text="!уровень <mention> <level:int>")
@bot.on.message(text="/level <mention> <level:int>")
@bot.on.message(text="+level <mention> <level:int>")
@bot.on.message(text="!level <mention> <level:int>")
async def set_moderator_level_handler(message, mention: str, level: int):
    # Проверка прав: только администраторы могут менять уровень модератора.
    if message.from_id not in ADMINS:
        await message.reply("Недостаточно прав.")
        return

    if level < 1 or level > 6:
        await message.reply("Уровень должен быть от 1 до 6.")
        return

    target_id = await get_user_id_from_mention(mention)
    if not target_id:
        await message.reply("Не удалось определить пользователя.")
        return

    # Изменяем только уровень пользователя, не меняя его роль
    set_user_level(target_id, level)
    admin_name = await get_user_name(message.from_id)

    level_names = {
        1: "Младший модератор",
        2: "Модератор",
        3: "Старший модератор",
        4: "Куратор модерации",
        5: "Зам.главного модератора",
        6: "Администратор",
        7: "Главный модератор"
    }
    new_level_name = level_names.get(level, f"Уровень {level}")
    target_name = await get_user_name(target_id)
    await message.reply(
        f"[https://vk.com/id{message.from_id}|{admin_name}] изменил уровень [https://vk.com/id{target_id}|модератора] на {level} ({new_level_name})."
    )

# Функция привязки никнейма
@bot.on.message(text="/setnick <mention> <nickname>")
@bot.on.message(text="/snick <mention> <nickname>")
@bot.on.message(text="+snick <mention> <nickname>")
@bot.on.message(text="!snick <mention> <nickname>")
@bot.on.message(text="!setnick <mention> <nickname>")
@bot.on.message(text="+setnick <mention> <nickname>")
async def set_nick(message, mention: str, nickname: str):
    # Получаем роль отправителя
    sender_role = get_user_role(message.from_id)
    # Если роль ниже "moder" – выдаём сообщение об отсутствии прав
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["senmoder"]:
        await message.reply("Недостаточно прав.")
        return
    uid = await get_user_id_from_mention(mention)
    if not uid:
        await message.reply("❌ Не удалось определить пользователя.")
        return

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO nicknames (vk_id, nickname) VALUES (?, ?) ON CONFLICT(vk_id) DO UPDATE SET nickname = ?", (uid, nickname, nickname))
        conn.commit()
        admin_id = message.from_id
        admin_name = await get_user_name(admin_id)
        user_name = await get_user_name(uid)
    await message.reply(f"[https://vk.com/id{admin_id}|{admin_name}] установил-(а) никнейм {nickname} "
                         f"пользователю [https://vk.com/id{uid}|{user_name}].")
    
@bot.on.message(text="/rnick <mention>")
@bot.on.message(text="+rnick <mention>")
@bot.on.message(text="!rnick <mention>")
@bot.on.message(text="/removenick <mention>")
@bot.on.message(text="+removenick <mention>")
@bot.on.message(text="!removenick <mention>")
@bot.on.message(text="/снятьник <mention>")
@bot.on.message(text="+снятьник <mention>")
@bot.on.message(text="!снятьник <mention>")
async def remove_nick(message, mention: str):
    # Получаем роль отправителя
    sender_role = get_user_role(message.from_id)
    # Если роль ниже "moder" – выдаём сообщение об отсутствии прав
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["senmoder"]:
        await message.reply("Недостаточно прав.")
        return

    # Получаем ID пользователя по упоминанию
    uid = await get_user_id_from_mention(mention)
    if not uid:
        await message.reply("❌ Не удалось определить пользователя.")
        return

    # Проверяем, есть ли у пользователя никнейм
    nickname = get_nickname(uid)
    if not nickname:
        await message.reply(f"❌ У пользователя с VK ID {uid} нет привязанного никнейма.")
        return

    # Удаляем никнейм из базы данных
    remove_nickname_from_db(uid)

    admin_id = message.from_id
    admin_name = await get_user_name(admin_id)
    user_name = await get_user_name(uid)

    await message.reply(f"[https://vk.com/id{admin_id}|{admin_name}] удалил-(а) никнейм у пользователя "
                         f"[https://vk.com/id{uid}|{user_name}].")

@bot.on.message(text="/nlist")
@bot.on.message(text="!nlist")
@bot.on.message(text="+nlist")
@bot.on.message(text="/nicklist")
@bot.on.message(text="!nicklist")
@bot.on.message(text="+nicklist")
@bot.on.message(text="/ники")
@bot.on.message(text="!ники")
@bot.on.message(text="+ники")
@bot.on.message(text="/нлист")
@bot.on.message(text="!нлист")
@bot.on.message(text="+нлист")
async def nickname_list(message):
    # Получаем роль отправителя
    sender_role = get_user_role(message.from_id)
    # Если роль ниже "moder" – выдаём сообщение об отсутствии прав
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["senmoder"]:
        await message.reply("Недостаточно прав.")
        return

    # Получаем список всех никнеймов
    nickname_list = get_alll_nicknames()

    # Если никнеймов нет, сообщаем об этом
    if not nickname_list:
        await message.reply("Никнеймы отсутствуют.")
        return

    # Формируем список никнеймов для ответа
    nickname_list_text = ""
    for index, (vk_id, nickname) in enumerate(nickname_list):
        user_name = await get_user_name(vk_id)  # Получаем имя для каждого пользователя
        nickname_list_text += f"{index + 1}) [https://vk.com/id{vk_id}|{user_name}] — {nickname}\n"

    await message.reply(f"Пользователи с никами:\n{nickname_list_text}")


@bot.on.message(text=[
    "/баланс <mention>", "+баланс <mention>", "!баланс <mention>",
    "/balance <mention>", "+balance <mention>", "!balance <mention>",
    "/bal <mention>", "+bal <mention>", "!bal <mention>",
    "/я <mention>", "+я <mention>", "!я <mention>"
])
@bot.on.message(reply_message=True, text=[
    "/баланс", "+баланс", "!баланс",
    "/balance", "+balance", "!balance",
    "/bal", "+bal", "!bal"
])
async def stats_handler(message: Message, mention: str = None):
    # Проверяем права вызывающего (только модераторы и выше)
    invoker_id = message.from_id
    invoker_role = get_user_role(invoker_id).lower()
    allowed_roles = {"moder", "senmoder", "admin", "senadmin", "depspec", "owner"}
    if invoker_role not in allowed_roles:
        await message.reply("Недостаточно прав для использования этой команды.")
        return

    # Определяем целевого пользователя:
    # Если есть ответ на сообщение – используем его автора,
    # иначе пытаемся извлечь ID из упоминания или ссылки.
    if message.reply_message:
        target_id = message.reply_message.from_id
    elif mention:
        target_id = await get_user_id_from_mention(mention)
        if not target_id:
            await message.reply("Не удалось извлечь идентификатор из упоминания или ссылки.")
            return
    else:
        await message.reply("Укажите пользователя через упоминание, ссылку или ответ на сообщение.")
        return

    # Регистрируем целевого пользователя (если ещё не зарегистрирован)
    add_user(target_id)

    target_coins = get_balance(target_id)
    target_points = get_points(target_id)
    target_mod_level = get_user_level(target_id)
    messages_count, last_time = get_user_message_stats(target_id)
    level_names = {
        1: "Младший модератор",
        2: "Модератор",
        3: "Старший модератор",
        4: "Куратор модерации",
        5: "Зам.главного модератора",
        6: "Администратор",
        7: "Главный модератор"
    }
    mod_level_text = level_names.get(target_mod_level, str(target_mod_level))

    # Формируем и отправляем сообщение со статистикой
    await message.reply(
        f"Текущий баланс коинов: {target_coins} MC.\n"
    )



@bot.on.message(text="/balance")
@bot.on.message(text="+balance")
@bot.on.message(text="!balance")
@bot.on.message(text="/баланс")
@bot.on.message(text="+баланс")
@bot.on.message(text="!баланс")
@bot.on.message(text="/bal")
@bot.on.message(text="+bal")
@bot.on.message(text="!bal")
async def stats_without_mention(message):
    invoker_id = message.from_id
    add_user(invoker_id)  # Регистрируем вызывающего пользователя, если его ещё нет
    invoker_role = get_user_role(invoker_id).lower()
    allowed_roles = {"moder", "senmoder", "admin", "senadmin", "depspec", "owner"}

    user_id = message.from_id

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Дополнительные данные для вызывающего пользователя
    invoker_coins = get_balance(invoker_id)
    invoker_points = get_points(invoker_id)
    invoker_mod_level = get_user_level(invoker_id)
    messages, last_time = get_user_message_stats(user_id)
    level_names = {
        1: "Младший модератор",
        2: "Модератор",
        3: "Старший модератор",
        4: "Куратор модерации",
        5: "Зам.главного модератора",
        6: "Администратор",
        7: "Главный модератор"
    }
    mod_level_text = level_names.get(invoker_mod_level, invoker_mod_level)

    await message.reply(
        f"Ваш текущий баланс коинов: {invoker_coins} MC."
    )

@bot.on.message(text=["/moders", "!moders", "+moders", "/модеры", "!модеры", "+модеры"])
@only_chats
async def moders_handler(message):
    # Получаем роль отправителя
    sender_role = get_user_role(message.from_id)
    # Если роль ниже "moder" – выдаём сообщение об отсутствии прав
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["moder"]:
        await message.reply("Недостаточно прав.")
        return

    # Получаем всех пользователей из базы (user_id и уровень)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, level FROM users")
    users = cursor.fetchall()

    # Получаем никнеймы пользователей
    cursor.execute("SELECT vk_id, nickname FROM nicknames")
    nicknames = dict(cursor.fetchall())

    conn.close()

    if not users:
        await message.reply("Список пользователей пуст.")
        return

    # Определяем отображаемые названия для модераторских уровней
    mod_level_names = {
        1: "Младшие модераторы",
        2: "Модераторы",
        3: "Старшие модераторы",
        4: "Куратор модерации",
        5: "Зам.Главного модератора",
        6: "Администраторы",
        7: "Главный модератор"
    }

    # Группируем пользователей по категориям
    grouped = {}
    for user_id, level in users:
        group_name = mod_level_names.get(level, f"Уровень {level}")
        grouped.setdefault(group_name, []).append(user_id)

    # Сортируем группы по убыванию уровня (7 → 1)
    sorted_groups = sorted(grouped.items(), key=lambda x: -list(mod_level_names.keys()).index(next((k for k, v in mod_level_names.items() if v == x[0]), 0)))

    # Формируем итоговый текст
    output_lines = []
    for group_name, user_ids in sorted_groups:
        output_lines.append(f"{group_name}:")
        names = []
        for uid in user_ids:
            # Проверяем, есть ли никнейм в БД
            name = nicknames.get(uid)
            if not name:
                name = await get_user_name(uid)  # Если нет ника, берём имя ВК
            names.append(f"[https://vk.com/id{uid}|{name}]")
        output_lines.append("\n".join(names))
        output_lines.append("")  # пустая строка между группами

    await message.reply("\n".join(output_lines).strip())


@bot.on.message(text=["/staff", "!staff", "+staff", "!стафф", "/стафф", "+стафф", ])
@only_chats
async def staff_handler(message):
    # Получаем роль отправителя
    sender_role = get_user_role(message.from_id)
    # Если роль ниже "moder" – выдаём сообщение об отсутствии прав
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["moder"]:
        await message.reply("Недостаточно прав.")
        return

    # Получаем список сотрудников (это асинхронная функция, если она таковой является)
    staff = get_staff()
    if not staff:
        await message.reply("Список сотрудников пуст.")
        return

    staff_text = "Владелец беседы - @club229805529 (ASTRAKHAN MANAGER)\n"
    roles = {
        "owner": "Спец.администраторы",
        "depspec": "Зам.Спец администратора",
        "senadmin": "Старшие администраторы",
        "admin": "Администраторы",
        "senmoder": "Старшие модераторы",
        "moder": "Модераторы"
    }

    for role, description in roles.items():
        role_users = [
            f"[https://vk.com/id{user_id}|{await get_user_name(user_id)}]"
            for user_id, user_role in staff if user_role == role
        ]
        staff_text += f"\n{description}:\n"
        if role_users:
            staff_text += "\n".join(role_users) + "\n"
        else:
            staff_text += "Отсутствуют\n"

    await message.reply(staff_text.strip())

# Обработчик команды /help
@bot.on.message(text=["/help", "+help", "!help", "/хелп", "!хелп", "+хелп", "/помощь", "+помощь", "!помощь"])
async def help_handler(message: Message):
    global help_cmid
    logging.info(f"Получена команда /help от пользователя {message.from_id}")
    user_id = message.from_id
    user_role = get_user_role(user_id)

    # Базовые команды, доступные всем пользователям
    help_text = """
Команды пользователей:    
/balance  — баланс коинов 
/info  — информация о работе обменника
/getid  — узнать оригинальную ссылку пользователя
/bug  — сообщить разработчику о баге
/shop — показать доступные товары в магазине
/buy — купить товар из магазина
/roulette — играть в русскую рулетку
/duel — сразиться в дуэли с пользователем
/slot — играть в слот-машину
/top — топ пользователей по балансу
/reward — получить ежедневную награду
    """

    # Определяем команды по ролям
    role_commands = {
        "moder": """
Команды модератора:
/moders — полный список модерации
/staff — участники с ролями
/clear — очистить сообщение 
/gnick — проверить никнейм пользователя
        """,
        "senmoder": """
Команды старшего модератора:
/addmoder — выдать права модератора пользователю
/removerole — забрать роль пользователя
/kick — исключить пользователя из беседы
/send — отправить сообщение пользователям из базы данных модерации
        """,
        "admin": """
Команды администратора:
/addsenmoder  — выдать права старшего модератора
/sban  — заблокировать пользователя в сетке бесед
        """,
        "senadmin": """
Команды старшего администратора:
/addsenmoder — выдать права старшего модератора пользователю
/lvl — изменить уровень модератора
/снят — исключить пользователя из всех бесед модерации
        """,
        "depspec": """
Команды зам.спец администратора:
/addsenadmin — выдать права старшего администратора пользователю
/aban — закрыть пользователю доступ к экономике бота
/editcoins — назначить новое количество коинов пользователю
/addcoins — выдать коины пользователю 
        """,
        "owner": """
Команды спец.администратора:
/addzsa — выдать права заместителя спец.админа пользователю
/adelete — удалить пользователя из базы данных
/sync — синхронизировать беседу с базой данных
/deldb — удалить таблицу из базы данных
        """
    }

    # Порядок ролей для накопления команд
    role_order = ["moder", "senmoder", "admin", "senadmin", "depspec", "owner"]

    if user_role in role_order:
        role_index = role_order.index(user_role)
        for i in range(role_index + 1):
            help_text += role_commands[role_order[i]]

    # Формируем клавиатуру с кнопкой "Альтернативные команды"
    main_keyboard = {
        "inline": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "label": "Альтернативные команды",
                        "payload": json.dumps({"command": "alt_commands"})
                    },
                    "color": "primary"
                }
            ]
        ]
    }

    # Отправляем сообщение с командами
    try:
        sent_message = await message.reply(help_text, keyboard=json.dumps(main_keyboard))
        help_cmid = sent_message.conversation_message_id  # Сохраняем ID сообщения
        logging.info(f"/help сообщение отправлено, conversation_message_id: {help_cmid}")
    except Exception as e:
        logging.error(f"Ошибка при отправке /help: {e}")
        await message.answer("Ошибка при отправке сообщения.")


@bot.on.message(payload={"command": "alt_commands"})
async def alt_commands_callback(message: Message):
    global help_cmid, alt_cmid
    logging.info(f"Получена кнопка 'Альтернативные команды' от пользователя {message.from_id}")

    user_id = message.from_id
    user_role = get_user_role(user_id)
    
    # Базовые команды для всех пользователей
    alt_text = """
Альтернативные команды

Команды пользователей: 
/balance  — баланс,bal
/info  — инфо,бот
/getid  — айди,id,ид
/bug  — баг
/shop — магазин,store
/buy — купить
/roulette — рулетка,rr
/duel — дуэль,сразиться
/slot — слот
/top — топ
/reward — бонус,bonus
    """

    # Команды для ролей
    role_commands = {
        "moder": """
Команды модератора:
/moders — модеры
/staff — стафф
/clear — чистка,очистить
/gnick — nicklist,checknick
        """,
        "senmoder": """
Команды старшего модератора:
/addmoder — mod,moder,модер,addmod
/removerole — rrole,сроль,снятьроль
/kick — кик,исключить
/send — рассылка
        """,
        "admin": """
Команды администратора:
/addsenmoder — smod,senmoder,стмодер,addsmod
/lvl — level,уровень
/снят — null
        """,
        "senadmin": """
Команды старшего администратора:
/addadmin — adm,admin,админ,addadm
        """,
        "depspec": """
Команды зам.спец администратора:
/addsenadmin — sadm,senadmin,стадмин,addsadmin
/aban — абан
/editcoins — null
/addcoins — null
        """,
        "owner": """
Команды спец.администратора:
/addzsa — zsa,depspec,зса
/adelete — удалить
/gsync — синхрон
/deldb — delbd,delbase,deletedb
        """
    }

    # Определяем порядок ролей для накопления команд
    role_order = ["moder", "senmoder", "admin", "senadmin", "depspec", "owner"]

    if user_role in role_order:
        role_index = role_order.index(user_role)
        for i in range(role_index + 1):
            alt_text += role_commands[role_order[i]]

    # Удаляем сообщение с основными командами
    try:
        if help_cmid:
            await bot.api.messages.delete(
                cmids=[help_cmid],
                peer_id=message.peer_id,
                delete_for_all=True
            )
            logging.info(f"/help сообщение удалено, cmid: {help_cmid}")
            help_cmid = None
        else:
            logging.warning("help_cmid не найден.")
    except Exception as e:
        logging.error(f"Ошибка при удалении /help: {e}")

    # Удаляем сообщение пользователя (нажатие кнопки)
    try:
        user_cmid = message.conversation_message_id
        if user_cmid:
            await bot.api.messages.delete(
                cmids=[user_cmid],
                peer_id=message.peer_id,
                delete_for_all=True
            )
            logging.info(f"Сообщение вызова alt_commands удалено, cmid: {user_cmid}")
        else:
            logging.warning("Не найден cmid для сообщения вызова alt_commands.")
    except Exception as e:
        logging.error(f"Ошибка при удалении вызова alt_commands: {e}")


    # Отправляем альтернативные команды
    try:
        sent_message = await message.answer(alt_text)
        logging.info(f"Альтернативные команды отправлены, cmid: {sent_message.conversation_message_id}")
    except Exception as e:
        logging.error(f"Ошибка при отправке альтернативных команд: {e}")

# Команда "магазин"
@bot.on.message(text="/shop")
@bot.on.message(text="/магазин") 
@bot.on.message(text="/store")
@bot.on.message(text="/магаз")
@bot.on.message(text="!shop")
@bot.on.message(text="!магазин") 
@bot.on.message(text="!store")
@bot.on.message(text="!магаз")
@bot.on.message(text="+shop")
@bot.on.message(text="+магазин") 
@bot.on.message(text="+store")
@bot.on.message(text="+магаз")
@only_chats
async def shop_handler(message):
    shop_text = "📜 Магазин:\n"
    for category, items in SHOP.items():
        shop_text += f"\n🔹 {category}\n"
        for item_id, item in items.items():
            shop_text += f"  {item_id}. {item['name']}  — {item['price']} M-Coins\n"
    await message.reply(shop_text)

# —----------------------------
# Новые команды для выдачи ролей
# —----------------------------
@bot.on.message(text="/aban <mention>")
@bot.on.message(text="+aban <mention>")
@bot.on.message(text="!aban <mention>")
@bot.on.message(text="/абан <mention>")
@bot.on.message(text="+абан <mention>")
@bot.on.message(text="!абан <mention>")
async def ban_user_handler(message, mention: str):
    """
    Команда /aban <mention>
    Закрывает пользователю доступ к боту навсегда, устанавливая роль "banned".
    Использование: доступно только владельцу.
    """
    sender_role = get_user_role(message.from_id)
    # Разрешаем команду только владельцу (при необходимости можно расширить список)
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["owner"]:
        await message.reply("⛔ Только владелец может закрыть доступ пользователю к боту.")
        return

    target_id = await get_user_id_from_mention(mention)
    if not target_id:
        await message.reply("Не удалось определить пользователя по упоминанию.")
        return
    
    admin_name = await get_user_name(message.from_id)
    target_name = await get_user_name(target_id)

    # Обновляем роль пользователя на "banned"
    update_user_role(target_id, "banned")
    target_name = await get_user_name(target_id)
    await message.reply(f"[https://vk.com/id{message.from_id}|{admin_name}] выдал-(а) блокировку доступа к командам бота модератору [https://vk.com/id{target_id}|{target_name}].\n\nСрок блокировки: навсегда.")

# Команда выдачи прав администратора (role = "admin")
@bot.on.message(text="/aunban <mention>")
@bot.on.message(text="+aunban <mention>")
@bot.on.message(text="!aunban <mention>")
@bot.on.message(text="/снять абан <mention>")
@bot.on.message(text="+снять абан <mention>")
@bot.on.message(text="!снять абан <mention>")
async def add_admin_handler(message, mention: str):
    sender_role = get_user_role(message.from_id)
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["depspec"]:
        await message.reply("Недостаточно прав.")
        return

    target_id = await get_user_id_from_mention(mention)
    if not target_id:
        await message.reply("Не удалось определить пользователя по упоминанию.")
        return

    update_user_role(target_id, "user")
    admin_name = await get_user_name(message.from_id)
    target_name = await get_user_name(target_id)
    await message.reply(
        f"[https://vk.com/id{message.from_id}|{admin_name}] снял-(а) блокировку доступа к командам бота модератору [https://vk.com/id{target_id}|{target_name}]."
    )

@bot.on.message(text="/addmoder")
@bot.on.message(text="/модер")
@bot.on.message(text="/mod")
@bot.on.message(text="/addmod")
@bot.on.message(text="+mod")
@bot.on.message(text="+модер")
@bot.on.message(text="+addmoder")
@bot.on.message(text="+addmod")
@bot.on.message(text="!mod")
@bot.on.message(text="!модер")
@bot.on.message(text="!addmoder")
@bot.on.message(text="!addmod")
async def ainfo_no_argument(message):
    # Получаем роль отправителя
    sender_role = get_user_role(message.from_id)
    # Если роль ниже "moder" – выдаём сообщение об отсутствии прав
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["senmoder"]:
        await message.reply("Недостаточно прав.")
        return
    await message.reply("Вы не указали пользователя")

# Команда выдачи прав модератора (role = "moder")
@bot.on.message(text="/addmoder <mention>")
@bot.on.message(text="/модер <mention>")
@bot.on.message(text="/mod <mention>")
@bot.on.message(text="/addmod <mention>")
@bot.on.message(text="+mod <mention>")
@bot.on.message(text="+модер <mention>")
@bot.on.message(text="+addmoder <mention>")
@bot.on.message(text="+addmod <mention>")
@bot.on.message(text="!mod <mention>")
@bot.on.message(text="!модер <mention>")
@bot.on.message(text="!addmoder <mention>")
@bot.on.message(text="!addmod <mention>")
async def add_moder_handler(message, mention: str):
    sender_role = get_user_role(message.from_id)
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["senmoder"]:
        await message.reply("Недостаточно прав.")
        return

    target_id = await get_user_id_from_mention(mention)
    if not target_id:
        await message.reply("Не удалось определить пользователя по упоминанию.")
        return

    update_user_role(target_id, "moder")
    admin_name = await get_user_name(message.from_id)
    target_name = await get_user_name(target_id)
    await message.reply(
        f"[https://vk.com/id{message.from_id}|{admin_name}] выдал-(а) права модератора [https://vk.com/id{target_id}|{target_name}]."
    )

@bot.on.message(text="/addsenmoder")
@bot.on.message(text="/стмодер")
@bot.on.message(text="/smod")
@bot.on.message(text="/addsmod")
@bot.on.message(text="+smod")
@bot.on.message(text="+стмодер")
@bot.on.message(text="+addsenmoder")
@bot.on.message(text="+addsmod")
@bot.on.message(text="!smod")
@bot.on.message(text="!стмодер")
@bot.on.message(text="!addsenmoder")
@bot.on.message(text="!addsmod")
async def ainfo_no_argument(message):
    # Получаем роль отправителя
    sender_role = get_user_role(message.from_id)
    # Если роль ниже "moder" – выдаём сообщение об отсутствии прав
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["admin"]:
        await message.reply("Недостаточно прав.")
        return
    await message.reply("Вы не указали пользователя")

# Команда выдачи прав старшего модератора (role = "senmoder")
@bot.on.message(text="/addsenmoder <mention>")
@bot.on.message(text="/стмодер <mention>")
@bot.on.message(text="/smod <mention>")
@bot.on.message(text="/addsmod <mention>")
@bot.on.message(text="+smod <mention>")
@bot.on.message(text="+стмодер <mention>")
@bot.on.message(text="+addsenmoder <mention>")
@bot.on.message(text="+addsmod <mention>")
@bot.on.message(text="!smod <mention>")
@bot.on.message(text="!стмодер <mention>")
@bot.on.message(text="!addsenmoder <mention>")
@bot.on.message(text="!addsmod <mention>")
async def add_senmoder_handler(message, mention: str):
    sender_role = get_user_role(message.from_id)
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["admin"]:
        await message.reply("Недостаточно прав.")
        return

    target_id = await get_user_id_from_mention(mention)
    if not target_id:
        await message.reply("Не удалось определить пользователя по упоминанию.")
        return

    update_user_role(target_id, "senmoder")
    admin_name = await get_user_name(message.from_id)
    target_name = await get_user_name(target_id)
    await message.reply(
        f"[https://vk.com/id{message.from_id}|{admin_name}] выдал-(а) права старшего модератора [https://vk.com/id{target_id}|{target_name}]."
    )

@bot.on.message(text="/addadmin")
@bot.on.message(text="/админ")
@bot.on.message(text="/adm")
@bot.on.message(text="/addadm")
@bot.on.message(text="+adm")
@bot.on.message(text="+админ")
@bot.on.message(text="+addadmin")
@bot.on.message(text="+addadm")
@bot.on.message(text="!adm")
@bot.on.message(text="!админ")
@bot.on.message(text="!addadmin")
@bot.on.message(text="!addadm")
async def ainfo_no_argument(message):
    # Получаем роль отправителя
    sender_role = get_user_role(message.from_id)
    # Если роль ниже "moder" – выдаём сообщение об отсутствии прав
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["senadmin"]:
        await message.reply("Недостаточно прав.")
        return
    await message.reply("Вы не указали пользователя")

# Команда выдачи прав администратора (role = "admin")
@bot.on.message(text="/addadmin <mention>")
@bot.on.message(text="/админ <mention>")
@bot.on.message(text="/adm <mention>")
@bot.on.message(text="/addadm <mention>")
@bot.on.message(text="+adm <mention>")
@bot.on.message(text="+админ <mention>")
@bot.on.message(text="+addadmin <mention>")
@bot.on.message(text="+addadm <mention>")
@bot.on.message(text="!adm <mention>")
@bot.on.message(text="!админ <mention>")
@bot.on.message(text="!addadmin <mention>")
@bot.on.message(text="!addadm <mention>")
async def add_admin_handler(message, mention: str):
    sender_role = get_user_role(message.from_id)
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["senadmin"]:
        await message.reply("Недостаточно прав.")
        return

    target_id = await get_user_id_from_mention(mention)
    if not target_id:
        await message.reply("Не удалось определить пользователя по упоминанию.")
        return

    update_user_role(target_id, "admin")
    admin_name = await get_user_name(message.from_id)
    target_name = await get_user_name(target_id)
    await message.reply(
        f"[https://vk.com/id{message.from_id}|{admin_name}] выдал-(а) права администратора [https://vk.com/id{target_id}|{target_name}]."
    )

@bot.on.message(text="/addsenadmin")
@bot.on.message(text="/стадмин")
@bot.on.message(text="/sadm")
@bot.on.message(text="/addsadm")
@bot.on.message(text="+sadm")
@bot.on.message(text="+стадмин")
@bot.on.message(text="+addsenadmin")
@bot.on.message(text="+addsadm")
@bot.on.message(text="!sadm")
@bot.on.message(text="!стадмин")
@bot.on.message(text="!addsenadmin")
@bot.on.message(text="!addsadm")
async def ainfo_no_argument(message):
    # Получаем роль отправителя
    sender_role = get_user_role(message.from_id)
    # Если роль ниже "moder" – выдаём сообщение об отсутствии прав
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["depspec"]:
        await message.reply("Недостаточно прав.")
        return
    await message.reply("Вы не указали пользователя")

# Команда выдачи прав старшего администратора (role = "senadmin")
@bot.on.message(text="/addsenadmin <mention>")
@bot.on.message(text="/стадмин <mention>")
@bot.on.message(text="/sadm <mention>")
@bot.on.message(text="/addsadm <mention>")
@bot.on.message(text="+sadm <mention>")
@bot.on.message(text="+стадмин <mention>")
@bot.on.message(text="+addsenadmin <mention>")
@bot.on.message(text="+addsadm <mention>")
@bot.on.message(text="!sadm <mention>")
@bot.on.message(text="!стадмин <mention>")
@bot.on.message(text="!addsenadmin <mention>")
@bot.on.message(text="!addsadm <mention>")
async def add_senadmin_handler(message, mention: str):
    sender_role = get_user_role(message.from_id)
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["depspec"]:
        await message.reply("Недостаточно прав.")
        return

    target_id = await get_user_id_from_mention(mention)
    if not target_id:
        await message.reply("Не удалось определить пользователя по упоминанию.")
        return

    update_user_role(target_id, "senadmin")
    admin_name = await get_user_name(message.from_id)
    target_name = await get_user_name(target_id)
    await message.reply(
        f"[https://vk.com/id{message.from_id}|{admin_name}] выдал-(а) права старшего администратора [https://vk.com/id{target_id}|{target_name}]."
    )

@bot.on.message(text="/addzsa")
@bot.on.message(text="/зса")
@bot.on.message(text="/zsa")
@bot.on.message(text="+zsa")
@bot.on.message(text="+зса")
@bot.on.message(text="+addzsa")
@bot.on.message(text="!zsa")
@bot.on.message(text="!зса")
@bot.on.message(text="!addzsa")
async def ainfo_no_argument(message):
    # Получаем роль отправителя
    sender_role = get_user_role(message.from_id)
    # Если роль ниже "moder" – выдаём сообщение об отсутствии прав
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["owner"]:
        await message.reply("Недостаточно прав.")
        return
    await message.reply("Вы не указали пользователя")

# Команда выдачи прав заместителя спец. администратора (role = "depspec")
@bot.on.message(text="/addzsa <mention>")
@bot.on.message(text="/зса <mention>")
@bot.on.message(text="/zsa <mention>")
@bot.on.message(text="+zsa <mention>")
@bot.on.message(text="+зса <mention>")
@bot.on.message(text="+addzsa <mention>")
@bot.on.message(text="!zsa <mention>")
@bot.on.message(text="!зса <mention>")
@bot.on.message(text="!addzsa <mention>")
async def add_deputyspec_handler(message, mention: str):
    sender_role = get_user_role(message.from_id)
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["owner"]:
        await message.reply("Недостаточно прав.")
        return

    target_id = await get_user_id_from_mention(mention)
    if not target_id:
        await message.reply("Не удалось определить пользователя по упоминанию.")
        return

    update_user_role(target_id, "depspec")
    admin_name = await get_user_name(message.from_id)
    target_name = await get_user_name(target_id)
    await message.reply(
        f"[https://vk.com/id{message.from_id}|{admin_name}] выдал-(а) права заместителя спец.администратора [https://vk.com/id{target_id}|{target_name}]."
    )


@bot.on.message(text="/removerole")
@bot.on.message(text="/rrole")
@bot.on.message(text="/сроль")
@bot.on.message(text="/снятьроль")
@bot.on.message(text="/user")
@bot.on.message(text="!removerole")
@bot.on.message(text="!rrole")
@bot.on.message(text="!сроль")
@bot.on.message(text="!снятьроль")
@bot.on.message(text="!user")
@bot.on.message(text="+removerole")
@bot.on.message(text="+rrole")
@bot.on.message(text="+сроль")
@bot.on.message(text="+снятьроль")
@bot.on.message(text="+user")
async def ainfo_no_argument(message):
    # Получаем роль отправителя
    sender_role = get_user_role(message.from_id)
    # Если роль ниже "moder" – выдаём сообщение об отсутствии прав
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["senmoder"]:
        await message.reply("Недостаточно прав.")
        return
    await message.reply("Вы не указали пользователя")

@bot.on.message(text="/removerole <mention>")
@bot.on.message(text="/rrole <mention>")
@bot.on.message(text="/сроль <mention>")
@bot.on.message(text="/снятьроль <mention>")
@bot.on.message(text="/user <mention>")
@bot.on.message(text="!removerole <mention>")
@bot.on.message(text="!rrole <mention>")
@bot.on.message(text="!сроль <mention>")
@bot.on.message(text="!снятьроль <mention>")
@bot.on.message(text="!user <mention>")
@bot.on.message(text="+removerole <mention>")
@bot.on.message(text="+rrole <mention>")
@bot.on.message(text="+сроль <mention>")
@bot.on.message(text="+снятьроль <mention>")
@bot.on.message(text="+user <mention>")
async def remove_role_handler(message, mention: str = None):
    sender_id = message.from_id
    sender_role = get_user_role(sender_id)

    # Определяем target_id:
    if mention:
        target_id = await get_user_id_from_mention(mention)
    elif message.reply_message:
        target_id = message.reply_message.from_id
    else:
        await message.reply("Вы не указали пользователя")
        return

    if not target_id:
        await message.reply("Не удалось определить пользователя по указанному аргументу.")
        return

    # Получаем роль целевого пользователя
    target_role = get_user_role(target_id)
    # Проверяем, что приоритет роли отправителя выше, чем у цели
    if ROLE_PRIORITY.get(sender_role, 0) <= ROLE_PRIORITY.get(target_role, 0):
        await message.reply("Недостаточно прав.")
        return

    # Возвращаем пользователю базовую роль "user"
    update_user_role(target_id, "user")
    sender_name = await get_user_name(sender_id)
    target_name = await get_user_name(target_id)
    await message.reply(
        f"[https://vk.com/id{sender_id}|{sender_name}] забрал(а) роль у [https://vk.com/id{target_id}|{target_name}]."
    )

# —----------------------------
# Команды: Русская рулетка и Ежедневная награда
# —----------------------------
@bot.on.message(text="/reward")
@bot.on.message(text="/бонус")
@bot.on.message(text="/bonus")
@bot.on.message(text="!reward")
@bot.on.message(text="!бонус")
@bot.on.message(text="!bonus")
@bot.on.message(text="+reward")
@bot.on.message(text="+бонус")
@bot.on.message(text="+bonus")
@only_chats
async def daily_reward_handler(message):
    sender_role = get_user_role(message.from_id)
    if sender_role not in ("user", "moder", "senmoder", "admin", "senadmin", "depspec", "owner"):
        await message.reply("Доступ к использованию команд бота закрыт.")
        return
    user_id = message.from_id

    conn = get_db_connection()
    cursor = conn.cursor()

    # Получаем время последнего получения награды и баланс пользователя
    cursor.execute("SELECT last_reward_time, balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if not result:
        await message.reply("Вы не зарегистрированы. Используйте /reg для регистрации.")
        conn.close()
        return

    last_reward_time, balance = result
    current_time = int(time.time())  # Текущее время (секунды)
    cooldown_time = 12 * 60 * 60      # 24 часа в секундах

    # Проверка на кулдаун
    if last_reward_time and current_time - last_reward_time < cooldown_time:
        remaining_time = cooldown_time - (current_time - last_reward_time)
        hours = remaining_time // 3600
        minutes = (remaining_time % 3600) // 60
        seconds = remaining_time % 60
        await message.reply(
            f"⏳ Недавно вы уже забирали свой временной бонус, \nвозвращайтесь через {hours} ч. {minutes} мин."
        )
        conn.close()
        return

    # Определяем бонус в зависимости от уровня пользователя
    bonus_by_level = {
        1: 5,
        2: 10,
        3: 15,
        4: 20,
        5: 22,
        6: 100,
        7: 500
    }
    mod_level = get_user_level(user_id)
    bonus = bonus_by_level.get(mod_level, 0)

    # Вычисляем новый баланс с начисленным бонусом
    new_balance = balance + bonus

    # Обновляем время последнего получения награды и новый баланс в базе данных
    cursor.execute(
        "UPDATE users SET last_reward_time = ?, balance = ? WHERE user_id = ?",
        (current_time, new_balance, user_id)
    )
    conn.commit()
    conn.close()

    await message.reply(f"🎉 Вы успешно забрали свой ежедневный бонус - {bonus} коинов. \n\n💳 Ваш текущий баланс: {new_balance} M-Coins.")

@bot.on.message(text="/rr")
@bot.on.message(text="/roulette")
@bot.on.message(text="/рулетка")
@bot.on.message(text="+rr")
@bot.on.message(text="+roulette")
@bot.on.message(text="+рулетка")
@bot.on.message(text="!rr")
@bot.on.message(text="!roulette")
@bot.on.message(text="!рулетка")
@only_chats
async def russian_roulette_handler(message):
    sender_role = get_user_role(message.from_id)
    if sender_role not in ("user", "moder", "senmoder", "admin", "senadmin", "depspec", "owner"):
        await message.reply("Доступ к использованию команд бота закрыт.")
        return
    user_id = message.from_id

    conn = get_db_connection()
    cursor = conn.cursor()

    # Получаем время последнего использования команды и баланс пользователя
    cursor.execute("SELECT last_russian_roulette, balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if not result:
        await message.reply("Вы не зарегистрированы. Используйте /reg для регистрации.")
        conn.close()
        return

    last_used, balance = result
    current_time = int(time.time())  # Текущее время (секунды)
    cooldown_time = 2 * 60         # 30 минут в секундах

    if last_used and current_time - last_used < cooldown_time:
        remaining_time = cooldown_time - (current_time - last_used)
        minutes = remaining_time // 60
        seconds = remaining_time % 60
        await message.reply(f"⏳ Подождите {minutes} мин. {seconds} сек. перед повторным использованием команды.")
        conn.close()
        return

    # Логика русской рулетки
    outcome = random.choice(["win_big", "win_small", "draw", "lose"])

    if outcome == "win_big":
        reward = 15
        balance += reward
        result_message = f"🎉 Вы победили и сорвали большой куш! Награда: +{reward} коинов. Ваш баланс: {balance}."
    elif outcome == "win_small":
        reward = 10
        balance += reward
        result_message = f"🎉 Вы победили! Награда: +{reward} коинов. Ваш баланс: {balance}."
    elif outcome == "draw":
        result_message = f"🤝 Ничья! Ваш баланс: {balance}."
    elif outcome == "lose":
        penalty = 20
        balance -= penalty
        result_message = f"💀 Вы проиграли! Потеря: -{penalty} коинов. Ваш баланс: {balance}."

    # Обновляем время последнего использования и баланс в базе данных
    cursor.execute(
        "UPDATE users SET last_russian_roulette = ?, balance = ? WHERE user_id = ?",
        (current_time, balance, user_id)
    )
    conn.commit()
    conn.close()

    await message.reply(result_message)



@bot.on.message(text="/info")
@bot.on.message(text="/инфо")
@bot.on.message(text="/информация")
@bot.on.message(text="/information")
@bot.on.message(text="/bot")
@bot.on.message(text="/бот")
@bot.on.message(text="!info")
@bot.on.message(text="!инфо")
@bot.on.message(text="!информация")
@bot.on.message(text="!information")
@bot.on.message(text="!bot")
@bot.on.message(text="!бот")
@bot.on.message(text="+info")
@bot.on.message(text="+инфо")
@bot.on.message(text="+информация")
@bot.on.message(text="+information")
@bot.on.message(text="+bot")
@bot.on.message(text="+бот")
@only_chats
async def info_command(message):
    await message.reply(
        """
✨ Уникальная валюта магазина модерации  — Moderation Coins. Данная валюта отлична от баллов и зарабатывается нижеизложенными методами.

 — Как заработать M-Coins?
🔹 Команда /reward - ежедневный бонус (количество коинов зависит от должности).
🔹 Рулетка (/rr) - можно использовать каждые 2 минуты.
🔹 Слоты (/slot <ставка>) - можно использовать раз в 5 минут.
🔹 Повышение: 100 Coins.

 — Штрафные санкции со стороны руководства:
🔸 Предупреждение: -50 Coins.
🔸 Выговор: -100 Coins.
🔸 Отсутствие активности долгое время (5+ дней): обнуление.

❗️ Важно: за распространение любой информации из обменника будет выдан Черный Список Модерации (ЧСМ) без возможности обжалования.
        """
    )

@bot.on.message(text="/duel <mention> <value:int>")
async def duel_handler(message, mention: str, value: int):
    challenger = message.from_id
    target = await get_user_id_from_mention(mention)

    if not target:
        await message.reply("Не удалось определить пользователя из упоминания.")
        return
    if challenger == target:
        await message.reply("Нельзя вызвать себя на дуэль.")
        return
    if value < MIN_BET or value > MAX_BET:
        await message.reply(f"Ставка должна быть от {MIN_BET} до {MAX_BET} коинов.")
        return
    if get_balance(challenger) < value:
        await message.reply("У вас недостаточно коинов для дуэли.")
        return
    if get_balance(target) < value:
        await message.reply("У указанного пользователя недостаточно коинов для дуэли.")
        return

    now = time.time()
    # Проверяем кулдаун для инициатора
    if challenger in duel_cooldowns and now - duel_cooldowns[challenger] < DUEL_COOLDOWN:
        remaining = int(DUEL_COOLDOWN - (now - duel_cooldowns[challenger]))
        await message.reply(f"Вы недавно участвовали в дуэли. Попробуйте через {remaining} секунд.")
        return
    # Проверяем наличие активного предложения у цели
    if target in pending_duels:
        await message.reply("У этого пользователя уже есть активное предложение дуэли.")
        return

    pending_duels[target] = {"challenger": challenger, "bet": value, "time": now}
    challenger_name = await get_user_name(challenger)
    target_name = await get_user_name(target)

    duel_keyboard = {
        "inline": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "label": "Принять",
                        "payload": json.dumps({"command": "accept_duel"})
                    },
                    "color": "positive"
                },
                {
                    "action": {
                        "type": "text",
                        "label": "Отклонить",
                        "payload": json.dumps({"command": "decline_duel"})
                    },
                    "color": "negative"
                }
            ]
        ]
    }

    sent_message = await message.reply(
        f"[id{target}|{target_name}], пользователь [id{challenger}|{challenger_name}] вызвал вас на дуэль!\nСтавка: {value} коинов.",
        keyboard=json.dumps(duel_keyboard)
    )
    # Сохраняем id сообщения для последующего удаления
    pending_duels[target]["cmid"] = sent_message.conversation_message_id

# Обработчик callback – принятие дуэли
@bot.on.message(payload={"command": "accept_duel"})
async def accept_duel_handler(message):
    target = message.from_id
    if target not in pending_duels:
        await message.reply("У вас нет активного предложения дуэли.")
        return

    duel = pending_duels.pop(target)
    challenger = duel["challenger"]
    bet = duel["bet"]

    # Удаляем исходное сообщение с кнопками
    try:
        cmid = duel.get("cmid")
        if cmid:
            await bot.api.messages.delete(cmids=[cmid], peer_id=message.peer_id, delete_for_all=True)
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщения дуэли: {e}")

    if get_balance(challenger) < bet or get_balance(target) < bet:
        await message.reply("У одного из участников недостаточно коинов. Дуэль отменена.")
        return

    # Случайный выбор победителя (50/50)
    result = random.choice(["win", "lose"])
    winner, loser = (target, challenger) if result == "win" else (challenger, target)

    update_balance(loser, -bet)
    update_balance(winner, bet)

    now = time.time()
    duel_cooldowns[challenger] = now
    duel_cooldowns[target] = now

    winner_name = await get_user_name(winner)
    loser_name = await get_user_name(loser)
    await message.reply(
        f"🔥 Дуэль завершена!\n🏆 Победитель: [id{winner}|{winner_name}]\n😞 Проигравший: [id{loser}|{loser_name}]\n💰 Ставка: {bet} коинов."
    )

# Обработчик callback – отказ от дуэли
@bot.on.message(payload={"command": "decline_duel"})
async def decline_duel_handler(message):
    target = message.from_id
    if target not in pending_duels:
        await message.reply("У вас нет активного предложения дуэли.")
        return

    duel = pending_duels.pop(target)
    challenger = duel["challenger"]

    # Удаляем исходное сообщение с кнопками
    try:
        cmid = duel.get("cmid")
        if cmid:
            await bot.api.messages.delete(cmids=[cmid], peer_id=message.peer_id, delete_for_all=True)
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщения дуэли: {e}")

    challenger_name = await get_user_name(challenger)
    target_name = await get_user_name(target)
    await message.reply(
        f"❌ [id{target}|{target_name}] отказался от дуэли с [id{challenger}|{challenger_name}]."
    )

# =========================================
# Команда /slot <ставка> – слот-машина с КД 5 минут
# =========================================
@bot.on.message(text="/slot")
@bot.on.message(text="/слоты")
@bot.on.message(text="/slots")
@bot.on.message(text="/слот")
@bot.on.message(text="+slot")
@bot.on.message(text="+слоты")
@bot.on.message(text="+slots")
@bot.on.message(text="+слот")
@bot.on.message(text="!slot")
@bot.on.message(text="!слоты")
@bot.on.message(text="!slots")
@bot.on.message(text="!слот")
async def ainfo_no_argument(message):
    await message.reply("Укажите ставку.")

@bot.on.message(text="/slot <bet:int>")
@bot.on.message(text="/слоты <bet:int>")
@bot.on.message(text="/slots <bet:int>")
@bot.on.message(text="/слот <bet:int>")
@bot.on.message(text="+slot <bet:int>")
@bot.on.message(text="+слоты <bet:int>")
@bot.on.message(text="+slots <bet:int>")
@bot.on.message(text="+слот <bet:int>")
@bot.on.message(text="!slot <bet:int>")
@bot.on.message(text="!слоты <bet:int>")
@bot.on.message(text="!slots <bet:int>")
@bot.on.message(text="!слот <bet:int>")
async def slot_handler(message, bet: int = None):
    if bet < 50:
        await message.reply("Минимальная ставка: 50 коинов")
        return
    if bet > 500:
        await message.reply("Максимальная ставка: 500 коинов")
        return

    user_id = message.from_id
    balance = get_balance(user_id)
    if balance < bet:
        await message.reply("Недостаточно средств для ставки")
        return

    now = time.time()
    if user_id in slot_cooldowns and now - slot_cooldowns[user_id] < 5 * 60:
        remaining = int(5 * 60 - (now - slot_cooldowns[user_id]))
        await message.reply(f"Подождите {remaining} секунд до следующей игры.")
        return

    slot_cooldowns[user_id] = now
    # Симуляция слота: шанс 50/50 выиграть
    outcome = random.choice(["win", "lose"])
    if outcome == "win":
        # Победа: добавляем ставку (например, выигрыш равен ставке)
        update_balance(user_id, bet)
        new_balance = get_balance(user_id)
        await message.reply(f"🎉 Поздравляем, вы выиграли! Ваша ставка {bet} коинов удвоилась. Новый баланс: {new_balance} коинов.")
    else:
        # Проигрыш: списываем ставку (она уже проверена)
        update_balance(user_id, -bet)
        new_balance = get_balance(user_id)
        await message.reply(f"💥 К сожалению, вы проиграли ставку {bet} коинов. Новый баланс: {new_balance} коинов.")

@bot.on.message(text="/clear")
@bot.on.message(text="+clear")
@bot.on.message(text="!clear")
@bot.on.message(text="/чистка")
@bot.on.message(text="+чистка")
@bot.on.message(text="!чистка")
@bot.on.message(text="/очистить")
@bot.on.message(text="+очистить")
@bot.on.message(text="!очистить")
@bot.on.message(text="/удалить")
@bot.on.message(text="+удалить")
@bot.on.message(text="!удалить")
async def clear_message(message):
    sender_role = get_user_role(message.from_id)
    
    # Проверка на доступность команды для пользователей с ролью senmoder или выше
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["senmoder"]:
        await message.reply("У вас недостаточно прав для использования этой команды.")
        return

    if not message.reply_message:
        return await message.reply("Ответьте на сообщение, которое необходимо удалить.")

    # Получаем роль того, кто написал сообщение, на которое отвечают
    replied_user_role = get_user_role(message.reply_message.from_id)

    # Если роль отправителя не выше роли того, на чье сообщение он отвечает, запрещаем удаление
    if ROLE_PRIORITY.get(sender_role, 0) <= ROLE_PRIORITY.get(replied_user_role, 0):
        await message.reply("Вы не можете удалить сообщение этого пользователя.")
        return

    try:
        await bot.api.messages.delete(
            message_ids=[message.reply_message.id],  # Для ЛС
            cmids=[message.reply_message.conversation_message_id],  # Для бесед
            peer_id=message.peer_id,
            delete_for_all=True
        )
        admin_name = await get_user_name(message.from_id)
        await message.reply(f"[https://vk.com/id{message.from_id}|{admin_name}], успешно очистил-(а) сообщение.")
    except Exception as e:
        await message.reply(f"⚠ Ошибка при удалении: {e}.")

@bot.on.message(text="/base")
@bot.on.message(text="+base")
@bot.on.message(text="!base")
@bot.on.message(text="/бд")
@bot.on.message(text="+бд")
@bot.on.message(text="!бд")
@bot.on.message(text="/база данных")
@bot.on.message(text="+база данных")
@bot.on.message(text="!база данных")
@bot.on.message(text="/db")
@bot.on.message(text="+db")
@bot.on.message(text="!db")
@bot.on.message(text="/bd")
@bot.on.message(text="+bd")
@bot.on.message(text="!bd")
async def view_database_tables(message):
    if message.from_id != OWNER_ID:
        return await message.reply("Недостаточно прав.")

    try:
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = await cursor.fetchall()
            table_names = [table[0] for table in tables]

        if table_names:
            await message.reply("📂 Таблицы в базе данных:\n" + "\n".join(table_names))
        else:
            await message.reply("В базе данных нет таблиц.")
    except Exception as e:
        await message.reply(f"Ошибка при чтении базы данных: {e}")

@bot.on.message(text="/bug")
@bot.on.message(text="!bug")
@bot.on.message(text="+bug")
@bot.on.message(text="/баг")
@bot.on.message(text="!баг")
@bot.on.message(text="+баг")
async def ainfo_no_argument(message):
    await message.reply("Опишите проблему.")

@bot.on.message(text="/bug <text>")
@bot.on.message(text="!bug <text>")
@bot.on.message(text="+bug <text>")
@bot.on.message(text="/баг <text>")
@bot.on.message(text="!баг <text>")
@bot.on.message(text="+баг <text>")
async def bug_report_handler(message, text):
    if not text.strip():
        await message.reply("Укажите описание бага.")
        return

    sender_id = message.from_id
    sender_name = await get_user_name(sender_id)  # Получаем имя отправителя

    report_message = (f"🚨 Новый баг-репорт!\n"
                      f"👤 Отправитель: [https://vk.com/id{sender_id}|{sender_name}]\n"
                      f"💬 Сообщение: {text}")

    # Отправляем сообщение каждому админу
    for admin_id in ADMINS:
        try:
            await bot.api.messages.send(
                user_id=admin_id,
                random_id=0,
                message=report_message
            )
        except Exception as e:
            print(f"Ошибка при отправке админу {admin_id}: {e}")

    await message.reply("Ваш баг-репорт отправлен администратору!")

@bot.on.message(text="/pay")
@bot.on.message(text="+pay")
@bot.on.message(text="!pay")
@bot.on.message(text="/передать")
@bot.on.message(text="+передать")
@bot.on.message(text="!передать")
async def ainfo_no_argument(message):
    await message.reply("Укажите пользователя и сумму")

@bot.on.message(text="/pay <mention> <amount:int>")
@bot.on.message(text="+pay <mention> <amount:int>")
@bot.on.message(text="!pay <mention> <amount:int>")
@bot.on.message(text="/передать <mention> <amount:int>")
@bot.on.message(text="+передать <mention> <amount:int>")
@bot.on.message(text="!передать <mention> <amount:int>")
async def pay_handler(message, mention: str, amount: int):
    sender = message.from_id
    receiver = await get_user_id_from_mention(mention)

    if not receiver:
        await message.reply("Не удалось определить пользователя из упоминания.")
        return

    if sender == receiver:
        await message.reply("Нельзя переводить коины самому себе.")
        return

    if amount < 10 or amount > 5000:
        await message.reply("Сумма перевода должна быть от 10 до 5000 коинов.")
        return

    if get_balance(sender) < amount:
        await message.reply("У вас недостаточно коинов для перевода.")
        return

    # Перевод коинов
    update_balance(sender, -amount)
    update_balance(receiver, amount)

    sender_name = await get_user_name(sender)
    receiver_name = await get_user_name(receiver)

    await message.reply(f"✅ Вы успешно передали {amount} коинов пользователю [id{receiver}|{receiver_name}].")


@bot.on.message(text="/рассылка <text>")
@bot.on.message(text="+рассылка <text>")
@bot.on.message(text="!рассылка <text>")
@bot.on.message(text="/send <text>")
@bot.on.message(text="+send <text>")
@bot.on.message(text="!send <text>")
async def mass_send_handler(message, text: str):
    sender_role = get_user_role(message.from_id)
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["senmoder"]:
        await message.reply("Недостаточно прав.")
        return
    try:
        # Подключаемся к базе данных и извлекаем список vk_id
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT vk_id FROM nicknames")
        users = cursor.fetchall()
        conn.close()

        sent_count = 0
        for user in users:
            vk_id = user[0]
            try:
                # Генерируем случайный идентификатор для предотвращения дублирования сообщений
                random_id = random.randint(0, 2**31 - 1)
                await bot.api.messages.send(peer_id=vk_id, message=text, random_id=random_id)
                sent_count += 1
            except Exception as e:
                logging.error(f"Ошибка отправки для vk_id {vk_id}: {e}")

        await message.reply(f"Рассылка завершена. Сообщение отправлено {sent_count} пользователям.")
    except Exception as e:
        logging.error(f"Ошибка рассылки: {e}")
        await message.reply("Ошибка при выполнении рассылки.")

@bot.on.message(text="/deldb <name>")
@bot.on.message(text="!deldb <name>")
@bot.on.message(text="+deldb <name>")
@bot.on.message(text="/delbd <name>")
@bot.on.message(text="!delbd <name>")
@bot.on.message(text="+delbd <name>")
@bot.on.message(text="/delbase <name>")
@bot.on.message(text="!delbase <name>")
@bot.on.message(text="+delbase <name>")
@bot.on.message(text="/deletebase <name>")
@bot.on.message(text="!deletebase <name>")
@bot.on.message(text="+deletebase <name>")
@bot.on.message(text="/deletebd <name>")
@bot.on.message(text="!deletebd <name>")
@bot.on.message(text="+deletebd <name>")
@bot.on.message(text="/deletedb <name>")
@bot.on.message(text="!deletedb <name>")
@bot.on.message(text="+deletedb <name>")
async def delete_table_handler(message, name: str):
    sender_role = get_user_role(message.from_id)
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["owner"]:
        await message.reply("Недостаточно прав.")
        return
    # Проверка корректности имени таблицы: разрешаем только буквы, цифры и знак подчёркивания
    if not re.match(r'^\w+$', name):
        await message.reply("Недопустимое имя таблицы. Допустимы только буквы, цифры и символ подчеркивания.")
        return

    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {name}")
        conn.commit()
        conn.close()
        await message.reply(f"Таблица '{name}' успешно удалена.")
    except Exception as e:
        logging.error(f"Ошибка при удалении таблицы {name}: {e}")
        await message.reply("Ошибка при удалении таблицы.")

async def delete_message(message):
    """Удаляет сообщение пользователя"""
    try:
        if message.conversation_message_id:
            await bot.api.messages.delete(
                cmids=[message.conversation_message_id],
                peer_id=message.peer_id,
                delete_for_all=True
            )
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщения {message.conversation_message_id}: {e}")

@bot.on.message(text="/gnick <mention>")
@bot.on.message(text="+gnick <mention>")
@bot.on.message(text="!gnick <mention>")
@bot.on.message(text="/гетник <mention>")
@bot.on.message(text="+гетник <mention>")
@bot.on.message(text="!гетник <mention>")
@bot.on.message(text="/getnick <mention>")
@bot.on.message(text="+getnick <mention>")
@bot.on.message(text="!getnick <mention>")
@bot.on.message(reply_message=True, text="/gnick")
@bot.on.message(reply_message=True, text="+gnick")
@bot.on.message(reply_message=True, text="!gnick")
@bot.on.message(reply_message=True, text="/гетник")
@bot.on.message(reply_message=True, text="+гетник")
@bot.on.message(reply_message=True, text="!гетник")
@bot.on.message(reply_message=True, text="/getnick")
@bot.on.message(reply_message=True, text="+getnick")
@bot.on.message(reply_message=True, text="!getnick")
async def gnick_handler(message, mention: str = None):
    # Получаем роль отправителя
    sender_role = get_user_role(message.from_id)
    # Если роль ниже "senmoder" – выдаём сообщение об отсутствии прав
    if ROLE_PRIORITY.get(sender_role, 0) < ROLE_PRIORITY["senmoder"]:
        await message.reply("Недостаточно прав.")
        return
    # Если указан mention, получаем ID из упоминания
    if mention:
        mention_id = extract_user_id(mention)
    elif message.reply_message:
        mention_id = message.reply_message.from_id
    else:
        await message.reply("Вы не указали пользователя!")
        return

    # Проверяем, есть ли ник в БД
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nickname FROM nicknames WHERE vk_id = ?", (mention_id,))
        result = cursor.fetchone()

    if result:
        nickname = result[0]
    else:
        nickname = "Не найден"

    # Отправляем ответ
    vk_link = f"https://vk.com/id{mention_id}"
    await message.reply(f"Ник [{vk_link}|пользователя] - {nickname}")


@bot.on.message()
async def handle_message(message: Message):
    # Подсчет сообщений
    update_user_message_count(message.from_id)

    # Проверяем, является ли сообщение приглашением
    if not hasattr(message, 'action') or not message.action:
        print("Не удалось найти действие в сообщении.")
        return

    # Отладка: выводим тип действия
    action_type = message.action.type
    print(f"Тип действия: {action_type}")

    # Проверяем, что действие является приглашением в чат
    if action_type != MessagesMessageActionStatus.CHAT_INVITE_USER:
        print(f"Получено действие {action_type}, но это не chat_invite_user.")
        return

    # Получаем ID пользователя, который был приглашён
    uid = message.action.member_id
    if not uid:
        print("Не удалось получить ID пользователя.")
        return

    # Получаем имя пользователя (только имя, без фамилии)
    user_name = await get_user_first_name(uid)

    # Формируем приветственное сообщение в зависимости от ID беседы
    if message.peer_id == 2000000007:  # ID беседы 7
        welcome_text = (f"[https://vk.com/id{uid}|{user_name}], добро пожаловать в беседу!\n\n"
                        "Не забудь прочитать закреплённое сообщение! Обзвон будет назначен ГМ/ЗГМ. \nВ Discord должен стоять префикс [К/ММ]")
    elif message.peer_id == 2000000001:  # ID беседы 2
        welcome_text = (f"[https://vk.com/id{uid}|{user_name}], добро пожаловать в беседу руководства модерации сервера!\n\n"
                        "Не забудь прочитать закреплённое сообщение! По всем вопросам обращайся к коллегам по стаффу. ")
    elif message.peer_id == 2000000008:  # ID беседы 8
        welcome_text = (f"[https://vk.com/id{uid}|{user_name}], добро пожаловать в беседу логирования действий руководства и модерации по отношению к боту.")
    else:  # Для всех остальных бесед
        welcome_text = (f"[https://vk.com/id{uid}|{user_name}], добро пожаловать в беседу!\n\n"
                        "Не забудь прочитать закреплённое сообщение! \nПосмотреть подробную информацию по обменнику и командам бота - «/info» и «/help» (исключительно в чате обменника).")

    try:
        # Отправляем приветственное сообщение
        await bot.api.messages.send(
            peer_id=message.peer_id,  # Отправляем в тот же чат
            random_id=0,
            message=welcome_text
        )
        print(f"Приветственное сообщение отправлено для пользователя {uid}")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

@bot.on.message()
async def on_message_handler(message: Message):
    user_id = message.from_id

    # Получаем текущее количество сообщений у пользователя
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT total_messages FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        current_messages = result[0]
        new_message_count = current_messages + 1
        cursor.execute("UPDATE users SET total_messages = ? WHERE user_id = ?", (new_message_count, user_id))
        conn.commit()
    conn.close()

# ==============================
# Основной запуск
# ==============================

async def main():
    # Запускаем периодическую проверку
    asyncio.create_task(periodic_check())


# Функция для запуска планировщика
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    initialize_database()
    initialize_columns()
    print("База данных и таблицы инициализированы.")
    initialize_punishments_table()
    print("База данных наказаний инициализирована.")
    initialize_applications_table()
    print("База данных заявлений инициализирована.")

    import threading
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    bot.run_forever()