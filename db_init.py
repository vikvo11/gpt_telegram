import sqlite3
import random

DB_FILE = 'mydatabase.db'

def get_sqlite_conn():
    """Подключение к локальной базе SQLite."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite():
    """
    Создаёт необходимые таблицы в SQLite, если их ещё нет.
    Затем вызывает fill_test_data() — он заполнит таблицы 
    ТОЛЬКО в том случае, если они пусты.
    """
    conn = get_sqlite_conn()
    cur = conn.cursor()

    # Пример таблицы costs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            cost INTEGER,
            year TEXT,
            month TEXT,
            limits INTEGER
        );
    """)

    # Пример таблицы limit_dict
    cur.execute("""
        CREATE TABLE IF NOT EXISTS limit_dict (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            limit_value INTEGER
        );
    """)

    conn.commit()
    conn.close()
    print("SQLite: Таблицы инициализированы (если их не было).")
    
    fill_test_data()


def fill_test_data():
    """
    Заполняет таблицы costs и limit_dict тестовыми данными 
    ТОЛЬКО если они пусты.
    """
    conn = get_sqlite_conn()
    cur = conn.cursor()

    # Проверяем, пустая ли таблица costs
    cur.execute("SELECT COUNT(*) AS cnt FROM costs")
    costs_count = cur.fetchone()["cnt"]

    # Проверяем, пустая ли таблица limit_dict
    cur.execute("SELECT COUNT(*) AS cnt FROM limit_dict")
    limit_dict_count = cur.fetchone()["cnt"]

    # Заполняем costs, если она пуста
    if costs_count == 0:
        titles = ["Rent", "Groceries", "Utilities", "Entertainment", 
                  "Education", "Transportation", "Healthcare", "Savings"]
        years = ["2022", "2023", "2024"]
        months = [f"{m:02d}" for m in range(1, 13)]  # "01".."12"

        # Генерация тестовых записей
        for year in years:
            for month in months:
                for _ in range(random.randint(2, 5)):  
                    title = random.choice(titles)
                    cost = random.randint(50, 2000)
                    limit_val = random.randint(1000, 5000)
                    cur.execute("""
                        INSERT INTO costs (title, cost, year, month, limits)
                        VALUES (?, ?, ?, ?, ?);
                    """, (title, cost, year, month, limit_val))
        print("Таблица costs заполнена тестовыми данными.")
    else:
        print("Таблица costs уже содержит данные, пропускаем вставку.")

    # Заполняем limit_dict, если она пуста
    if limit_dict_count == 0:
        # Для примера берём те же titles (или можно отдельно определить)
        titles = ["Rent", "Groceries", "Utilities", "Entertainment", 
                  "Education", "Transportation", "Healthcare", "Savings"]
        for title in titles:
            limit_value = random.randint(1000, 35000)
            cur.execute("INSERT INTO limit_dict (title, limit_value) VALUES (?, ?);",
                        (title, limit_value))

        # Вставляем запись для "общий"
        cur.execute("INSERT INTO limit_dict (title, limit_value) VALUES (?, ?);",
                    ("общий", 100000))

        print("Таблица limit_dict заполнена тестовыми данными.")
    else:
        print("Таблица limit_dict уже содержит данные, пропускаем вставку.")

    conn.commit()
    conn.close()
    print("SQLite: Заполнение тестовыми данными (при необходимости) завершено.")


if __name__ == "__main__":
    init_sqlite()
