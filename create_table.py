import os
import psycopg2

# Устанавливаем соединение с базой данных
conn = psycopg2.connect(
    host=os.environ['DB_HOST'],
    database=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    port=os.environ['DB_PORT']
)

# Создаем таблицу problems в БД
try:
    with open('create_table.sql', 'r') as file:
        create_table_query = file.read()
        cur = conn.cursor()
        cur.execute(create_table_query)
        conn.commit()
except FileNotFoundError:
    print('Файл для создания таблицы problems (create_table_query.sql) не найден')

# Создаем представление для запроса
try:
    with open('create_view.sql', 'r') as file:
        create_view_query = file.read()
        cur = conn.cursor()
        cur.execute(create_view_query)
        conn.commit()
except FileNotFoundError:
    print('Файл для создания VIEW (create_view.sql) не найден')

conn.close()