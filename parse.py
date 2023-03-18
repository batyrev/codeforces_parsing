import os
import psycopg2
import requests
from bs4 import BeautifulSoup
import settings
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Устанавливаем соединение с базой данных
conn = psycopg2.connect(
    host=os.environ['DB_HOST'],
    database=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    port=os.environ['DB_PORT']
)

# Функция для выполнения парсинга страницы с задачами
def parse_tasks():
    url = settings.START_URL
    headers = settings.HEADERS
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    tasks = []

    while True:
        # Парсим страницу
        for row in soup.select('.problems tr')[1:]:
            topics = row.select('.notice')
            topics = [t.text.strip() for t in topics]
            link = row.select('.id a')[0]['href']
            name = row.find_all(href=link)[1].parent.text.strip()
            # проверка на существование элемента
            if len(row.select('a[title^="Количество"]')) > 0:
                solutions = row.select('a[title^="Количество"]')[0].text.strip().replace('x', '')
            else:
                solutions = None
            title = row.select('.id a')[0].text.strip()
            # проверка на существование элемента
            if len(row.select('.ProblemRating')) > 0:
                difficulty = row.select('.ProblemRating')[0].text.strip()
            else:
                difficulty = None

            task = {'title': title, 'name': name, 'link': link, 'topics': topics, 'solutions': solutions, 'difficulty': difficulty}
            tasks.append(task)

        # Проверяем, есть ли еще страницы с задачами
        next_link = soup.find(string='→').parent
        # проверка, что класс не inactive
        if next_link and 'inactive' not in next_link['class']:
            next_url = 'https://codeforces.com' + next_link['href']
            response = requests.get(next_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
        else:
            break
    cur = conn.cursor()

    for task in tasks:
        cur.execute(f"SELECT * FROM problems WHERE title = '{task['title']}'")
        exists = cur.fetchone()
        if not exists:
            cur.execute("INSERT INTO problems (title, name link, topics, solutions, difficulty) VALUES (%s, %s, %s, %s, %s)",
                        (task['title'], task['name'], task['link'], task['topics'], task['solutions'], task['difficulty']))
            conn.commit()
        else:
            cur.execute("UPDATE problems SET title = %s, name = %s, topics = %s, solutions = %s, difficulty = %s WHERE link = %s",
                        (task['title'], task['name'], task['topics'], task['solutions'], task['difficulty'], task['link']))
            conn.commit()
    conn.close()

if __name__ == '__main__':
    parse_tasks()