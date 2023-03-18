import os
import psycopg2
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Создаем бота
bot = Bot(token=os.environ['BOT_TOKEN'])
# Создаем диспетчер для обработки сообщений
dp = Dispatcher(bot)

# Устанавливаем соединение с базой данных
conn = psycopg2.connect(
    host=os.environ['DB_HOST'],
    database=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    port=os.environ['DB_PORT']
)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я могу помочь тебе найти задачи по теме и сложности. Пожалуйста, выбери тему и сложность:", reply_markup=get_topics_keyboard())

# Обработчик выбора темы
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('topics_'))
async def process_topics_callback(callback_query: types.CallbackQuery):
    topics = callback_query.data.split('_')[1]
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"Ты выбрал тему {topics}. Теперь выбери сложность:", reply_markup=get_difficulties_keyboard(topics))

# Обработчик выбора сложности
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('difficulty_') or c.data == "back")
async def process_difficulty_callback(callback_query: types.CallbackQuery):
    # обработка кнопки "Назад"
    print(callback_query.data)
    if callback_query.data == "back":
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "Выбери тему:", reply_markup=get_topics_keyboard())
        return
    difficulty = int(callback_query.data.split('_')[1])
    topics = callback_query.data.split('_')[2]
    await bot.answer_callback_query(callback_query.id)
    task_subset = get_task_subset(topics, difficulty)
    if task_subset:
        message = f"Вот твои задачи для темы {topics} и сложности {difficulty}:"
    else:
        message = f"К сожалению, задачи для темы {topics} и сложности {difficulty} не найдены."
    await bot.send_message(callback_query.from_user.id, message, reply_markup=get_task_buttons(task_subset))

# Функция для получения подборки задач по теме и сложности
def get_task_subset(topics, difficulty):
    cur = conn.cursor()
    cur.execute(f"SELECT task_subset FROM view1 WHERE topics @> ARRAY['{topics}']::text[] AND difficulty={difficulty};")
    row = cur.fetchone()
    if row:
        task_subset = row[0]
        return task_subset
    else:
        return None

def create_message_with_tasks(task_subset):
    message = ""
    for task_id in task_subset:
        link = get_link_by_title(task_id)
        name = get_name_by_title(task_id)
        task_url = f"https://codeforces.com{link}"
        message += f"{name}:\n{task_url}\n"
    return message

def get_name_by_title(title):
    cur = conn.cursor()
    cur.execute(f"SELECT name FROM problems WHERE title='{title}';")
    rows = cur.fetchone()
    return rows[0]

def get_link_by_title(title):
    cur = conn.cursor()
    cur.execute(f"SELECT link FROM problems WHERE title='{title}';")
    rows = cur.fetchone()
    return rows[0]

# Функция для получения клавиатуры с темами
def get_topics_keyboard():
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT UNNEST(topics) FROM problems;")
    rows = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for row in rows:
        topics = row[0]
        button = types.InlineKeyboardButton(text=topics, callback_data=f"topics_{topics}")
        keyboard.add(button)
    return keyboard

# Функция для получения клавиатуры со сложностями
def get_difficulties_keyboard(topics):
    cur = conn.cursor()
    cur.execute(f"SELECT DISTINCT difficulty FROM view1 WHERE '{topics}' = ANY (topics);")
    rows = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for row in rows:
        difficulty = row[0]
        button = types.InlineKeyboardButton(text=str(difficulty), callback_data=f"difficulty_{difficulty}_{topics}")
        keyboard.add(button)
    button = types.InlineKeyboardButton(text="Назад", callback_data="back")
    keyboard.add(button)
    return keyboard

# Функция для получения клавиатуры с кнопками задач
def get_task_buttons(task_subset):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for task_id in task_subset:
        link = get_link_by_title(task_id)
        name = get_name_by_title(task_id)
        button = types.InlineKeyboardButton(text=name, url=f"https://codeforces.com{link}")
        keyboard.add(button)
    return keyboard

# Функция для получения списка задач по заданным параметрам
def get_tasks(difficulty, topic):
    cur = conn.cursor()
    cur.execute(f"SELECT title, link, solutions FROM tasks WHERE difficulty = {difficulty} AND topics LIKE '%{topic}%'")
    tasks = cur.fetchall()
    return tasks

# Функция для поиска информации о задаче по названию и номеру
def find_task(title, number):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM problems WHERE title LIKE '%{title}%' AND link LIKE '%{number}%'")
    task = cur.fetchone()
    return task

# Запускаем бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    conn.close()