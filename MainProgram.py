import os
import dotenv
from openai import OpenAI

import re
import prettytable

import psycopg2
from prettytable import PrettyTable

dotenv.load_dotenv()
client = OpenAI(api_key=os.getenv('DEEP_SEEK_API'), base_url="https://api.deepseek.com")

def send_sql_query(user_query: str, schema: str) -> str:
    prompt = f"""Переведи этот запрос в SQL. Используй схему: {schema}.
       Запрос: {user_query}. Отправь только код, без пояснений."""
    response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": prompt},
    ],
    stream=False
    )

    return response.choices[0].message.content

def validate_ai_query(input_query: str):
    pattern = r'```sql\n(.*?)\n```'  # `(.*?)` — ленивое совпадение (до первого ```)
    match = re.search(pattern, input_query, re.DOTALL)  # re.DOTALL учитывает переносы строк

    if match:
        return match.group(1)  # group(1) — содержимое внутри скобок
    else:
        print("Не найдено")
        return None

# Подключение к БД и выполнение запроса
def execute_sql(sql_query: str) -> tuple[tuple, list[tuple]]:
    conn = psycopg2.connect(
        dbname="shop",
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_IP')
    )
    cursor = conn.cursor()
    cursor.execute(sql_query)
    field_names = [desc[0] for desc in cursor.description]
    result = cursor.fetchall()  # реальное выполнение команд sql1

    cursor.close()
    conn.close()
    return field_names, result

def table_output(field_names: tuple ,table_rows: list[tuple]):
    table = PrettyTable()
    table.field_names = field_names
    table.add_rows(table_rows)
    return table

if __name__ == "__main__":
    schema = "Таблица clients (id, name, email)"
    user_input = "Покажи всех пользователей с почтой на gmail.com"
    generated_sql = send_sql_query(user_input, schema)

    print("Результат AI:", generated_sql)
    print("Сгенерированный SQL:", validate_ai_query(generated_sql))

    generated_sql = "SELECT * FROM clients WHERE email LIKE '%@gmail.com'"
    field_names, result = execute_sql(generated_sql)

    print("Результат:\n", table_output(field_names, result))