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
    ТОЛЬКО в том случае, если они пусты (costs, limit_dict).
    """
    conn = get_sqlite_conn()
    cur = conn.cursor()

    # 1) Таблица costs
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

    # 2) Таблица limit_dict
    cur.execute("""
        CREATE TABLE IF NOT EXISTS limit_dict (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            limit_value INTEGER
        );
    """)

    # ----------------------------------------------------------------
    # 3) Новая таблица users (для создания пользователей)
    # ----------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT,
            created_at TEXT
        );
    """)

    # ----------------------------------------------------------------
    # 4) Новая таблица main_goals (основные цели).
    #    Связана с пользователем (user_id).
    # ----------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS main_goals (
            goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            goal_name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );
    """)

    # ----------------------------------------------------------------
    # 5) Новая таблица training_goals (для целей обучения).
    #    Хранит user_id, goal_id (ссылка на main_goals), название цели (дубль),
    #    время занятия, шаги обучения за день, тест, результат теста,
    #    флаги выполнения, счётчик без пропущенных дней.
    # ----------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS training_goals (
            training_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            goal_id INTEGER,
            goal_name TEXT,
            study_time TEXT,       -- время занятия
            daily_steps INTEGER,   -- шаги обучения на текущий день
            test TEXT,             -- название теста (или описание)
            test_result TEXT,      -- результат теста
            daily_completed BOOLEAN, -- выполнено обучение за текущий день?
            test_passed BOOLEAN,     -- сдан ли тест?
            streak_count INTEGER,    -- счётчик без пропущенных дней
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (goal_id) REFERENCES main_goals (goal_id)
        );
    """)

    conn.commit()
    conn.close()
    print("SQLite: Таблицы инициализированы (если их не было).")
    
    # Заполнение тестовыми данными (только для costs/limit_dict)
    fill_test_data()

def fill_test_data():
    """
    Заполняет таблицы costs и limit_dict тестовыми данными 
    ТОЛЬКО если они пусты.
    (Если нужно — расширьте логику для заполнения users/main_goals/training_goals)
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
