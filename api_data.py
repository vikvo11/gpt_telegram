# api_data.py

from flask import Blueprint, request, jsonify
import common_db  # <-- Модуль, где определены is_mysql, mysql, get_sqlite_conn (как в предыдущих примерах)

api_data_bp = Blueprint('api_data_bp', __name__)

def get_sqlite_conn():
    """Помощник для подключения к SQLite (если используется)."""
    import sqlite3
    conn = sqlite3.connect('mydatabase.db')
    conn.row_factory = sqlite3.Row
    return conn

# ------------------------------------------------------------------------------
# USERS
# ------------------------------------------------------------------------------
@api_data_bp.route('/users', methods=['GET'])
def get_all_users():
    """
    GET /users
    Возвращает список всех пользователей (таблица users).
    """
    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, email, created_at FROM users")
        rows = cur.fetchall()
        conn.close()
    else:
        cur = common_db.mysql.connection.cursor()
        cur.execute("SELECT user_id, username, email, created_at FROM users")
        rows = cur.fetchall()
        cur.close()

    # Преобразуем в список словарей
    data = []
    if not common_db.is_mysql:
        data = [dict(r) for r in rows]  # sqlite3.Row -> dict
    else:
        data = rows  # MySQL DictCursor -> list of dict

    return jsonify(data), 200

@api_data_bp.route('/users', methods=['POST'])
def upsert_user():
    """
    POST /users
    Принимает JSON, где либо есть user_id (тогда обновляем), либо нет (тогда создаём).
    Пример тела:
    {
      "user_id": 1,
      "username": "Alice",
      "email": "alice@example.com"
    }
    """
    payload = request.get_json() or {}
    user_id = payload.get("user_id")  # Может быть None, если создаём нового
    username = payload.get("username")
    email = payload.get("email")

    if not username:
        return jsonify({"error": "username is required"}), 400

    # Если нужно - можно генерировать created_at = сейчас, если user_id отсутствует
    import datetime
    now_str = datetime.datetime.utcnow().isoformat()

    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()

        if user_id:
            # Проверяем, есть ли такой user
            cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            if row:
                # update
                cur.execute("""
                    UPDATE users
                    SET username = ?, email = ?
                    WHERE user_id = ?
                """, (username, email, user_id))
            else:
                # insert
                # используем user_id, если хотим задать вручную, 
                # но обычно PRIMARY KEY AUTOINCREMENT не задают вручную
                cur.execute("""
                    INSERT INTO users (user_id, username, email, created_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, username, email, now_str))
        else:
            # создаём нового без user_id
            cur.execute("""
                INSERT INTO users (username, email, created_at)
                VALUES (?, ?, ?)
            """, (username, email, now_str))

        conn.commit()

        # Возвращаем весь список после изменения
        cur.execute("SELECT user_id, username, email, created_at FROM users")
        rows = cur.fetchall()
        conn.close()
    else:
        # MySQL
        cur = common_db.mysql.connection.cursor()

        if user_id:
            cur.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
            row = cur.fetchone()
            if row:
                # update
                cur.execute("""
                    UPDATE users
                    SET username=%s, email=%s
                    WHERE user_id=%s
                """, (username, email, user_id))
            else:
                # insert
                cur.execute("""
                    INSERT INTO users (user_id, username, email, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, username, email, now_str))
        else:
            # создаём нового
            cur.execute("""
                INSERT INTO users (username, email, created_at)
                VALUES (%s, %s, %s)
            """, (username, email, now_str))

        common_db.mysql.connection.commit()

        cur.execute("SELECT user_id, username, email, created_at FROM users")
        rows = cur.fetchall()
        cur.close()

    data = []
    if not common_db.is_mysql:
        data = [dict(r) for r in rows]
    else:
        data = rows

    return jsonify(data), 200

# ------------------------------------------------------------------------------
# MAIN_GOALS
# ------------------------------------------------------------------------------
@api_data_bp.route('/main_goals', methods=['GET'])
def get_main_goals():
    """
    GET /main_goals
    Возвращает список всех целей (main_goals).
    """
    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT goal_id, user_id, goal_name
            FROM main_goals
        """)
        rows = cur.fetchall()
        conn.close()
    else:
        cur = common_db.mysql.connection.cursor()
        cur.execute("""
            SELECT goal_id, user_id, goal_name
            FROM main_goals
        """)
        rows = cur.fetchall()
        cur.close()

    data = []
    if not common_db.is_mysql:
        data = [dict(r) for r in rows]
    else:
        data = rows

    return jsonify(data), 200

@api_data_bp.route('/main_goals', methods=['POST'])
def upsert_main_goal():
    """
    POST /main_goals
    Пример тела:
    {
      "goal_id": 10,
      "user_id": 1,
      "goal_name": "Lose weight"
    }
    Если goal_id указан и существует -> обновляем, иначе -> создаём.
    """
    payload = request.get_json() or {}
    goal_id = payload.get("goal_id")  # Может быть None
    user_id = payload.get("user_id")
    goal_name = payload.get("goal_name")

    if not user_id or not goal_name:
        return jsonify({"error": "user_id and goal_name are required"}), 400

    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()

        if goal_id:
            # Ищем
            cur.execute("SELECT * FROM main_goals WHERE goal_id=?", (goal_id,))
            row = cur.fetchone()
            if row:
                # update
                cur.execute("""
                    UPDATE main_goals
                    SET user_id=?, goal_name=?
                    WHERE goal_id=?
                """, (user_id, goal_name, goal_id))
            else:
                # insert (если хотим сохранить указанный goal_id, но обычно PK autoincrement)
                cur.execute("""
                    INSERT INTO main_goals (goal_id, user_id, goal_name)
                    VALUES (?, ?, ?)
                """, (goal_id, user_id, goal_name))
        else:
            # insert
            cur.execute("""
                INSERT INTO main_goals (user_id, goal_name)
                VALUES (?, ?)
            """, (user_id, goal_name))

        conn.commit()

        # Возвращаем список
        cur.execute("SELECT goal_id, user_id, goal_name FROM main_goals")
        rows = cur.fetchall()
        conn.close()
    else:
        # MySQL
        cur = common_db.mysql.connection.cursor()

        if goal_id:
            cur.execute("SELECT * FROM main_goals WHERE goal_id=%s", (goal_id,))
            row = cur.fetchone()
            if row:
                # update
                cur.execute("""
                    UPDATE main_goals
                    SET user_id=%s, goal_name=%s
                    WHERE goal_id=%s
                """, (user_id, goal_name, goal_id))
            else:
                # insert
                cur.execute("""
                    INSERT INTO main_goals (goal_id, user_id, goal_name)
                    VALUES (%s, %s, %s)
                """, (goal_id, user_id, goal_name))
        else:
            cur.execute("""
                INSERT INTO main_goals (user_id, goal_name)
                VALUES (%s, %s)
            """, (user_id, goal_name))

        common_db.mysql.connection.commit()

        cur.execute("SELECT goal_id, user_id, goal_name FROM main_goals")
        rows = cur.fetchall()
        cur.close()

    data = []
    if not common_db.is_mysql:
        data = [dict(r) for r in rows]
    else:
        data = rows

    return jsonify(data), 200

# ------------------------------------------------------------------------------
# TRAINING_GOALS
# ------------------------------------------------------------------------------
@api_data_bp.route('/training_goals', methods=['GET'])
def get_training_goals():
    """
    GET /training_goals
    Возвращает список всех записей (training_goals).
    """
    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT training_id, user_id, goal_id, goal_name, study_time,
                   daily_steps, test, test_result, daily_completed, test_passed, streak_count
            FROM training_goals
        """)
        rows = cur.fetchall()
        conn.close()
    else:
        cur = common_db.mysql.connection.cursor()
        cur.execute("""
            SELECT training_id, user_id, goal_id, goal_name, study_time,
                   daily_steps, test, test_result, daily_completed, test_passed, streak_count
            FROM training_goals
        """)
        rows = cur.fetchall()
        cur.close()

    data = []
    if not common_db.is_mysql:
        data = [dict(r) for r in rows]
    else:
        data = rows

    return jsonify(data), 200

@api_data_bp.route('/training_goals', methods=['POST'])
def upsert_training_goal():
    """
    POST /training_goals
    Пример тела:
    {
      "training_id": 5,
      "user_id": 1,
      "goal_id": 10,
      "goal_name": "Lose weight",
      "study_time": "1h",
      "daily_steps": 5000,
      "test": "Nutrition quiz",
      "test_result": "90%",
      "daily_completed": true,
      "test_passed": true,
      "streak_count": 3
    }
    Если training_id указан и существует -> обновляем, иначе -> создаём.
    """
    payload = request.get_json() or {}

    training_id    = payload.get("training_id")
    user_id        = payload.get("user_id")
    goal_id        = payload.get("goal_id")
    goal_name      = payload.get("goal_name")
    study_time     = payload.get("study_time")
    daily_steps    = payload.get("daily_steps")
    test           = payload.get("test")
    test_result    = payload.get("test_result")
    daily_completed= payload.get("daily_completed")
    test_passed    = payload.get("test_passed")
    streak_count   = payload.get("streak_count")

    # Обязательно проверить как минимум user_id и goal_id, goal_name?
    if not user_id or not goal_id or not goal_name:
        return jsonify({"error": "user_id, goal_id, and goal_name are required"}), 400

    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()

        if training_id:
            # проверяем, есть ли такая запись
            cur.execute("SELECT * FROM training_goals WHERE training_id=?", (training_id,))
            row = cur.fetchone()
            if row:
                # update
                cur.execute("""
                    UPDATE training_goals
                    SET user_id=?, goal_id=?, goal_name=?, study_time=?, daily_steps=?,
                        test=?, test_result=?, daily_completed=?, test_passed=?, streak_count=?
                    WHERE training_id=?
                """, (user_id, goal_id, goal_name, study_time, daily_steps,
                      test, test_result, daily_completed, test_passed, streak_count, training_id))
            else:
                # insert
                cur.execute("""
                    INSERT INTO training_goals
                    (training_id, user_id, goal_id, goal_name, study_time,
                     daily_steps, test, test_result, daily_completed, test_passed, streak_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (training_id, user_id, goal_id, goal_name, study_time,
                      daily_steps, test, test_result, daily_completed, test_passed, streak_count))
        else:
            # insert без training_id
            cur.execute("""
                INSERT INTO training_goals
                (user_id, goal_id, goal_name, study_time,
                 daily_steps, test, test_result, daily_completed, test_passed, streak_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, goal_id, goal_name, study_time,
                  daily_steps, test, test_result, daily_completed, test_passed, streak_count))

        conn.commit()

        # Возвращаем всё
        cur.execute("""
            SELECT training_id, user_id, goal_id, goal_name, study_time,
                   daily_steps, test, test_result, daily_completed, test_passed, streak_count
            FROM training_goals
        """)
        rows = cur.fetchall()
        conn.close()

    else:
        # MySQL
        cur = common_db.mysql.connection.cursor()
        if training_id:
            cur.execute("SELECT * FROM training_goals WHERE training_id=%s", (training_id,))
            row = cur.fetchone()
            if row:
                # update
                cur.execute("""
                    UPDATE training_goals
                    SET user_id=%s, goal_id=%s, goal_name=%s, study_time=%s, daily_steps=%s,
                        test=%s, test_result=%s, daily_completed=%s, test_passed=%s, streak_count=%s
                    WHERE training_id=%s
                """, (user_id, goal_id, goal_name, study_time, daily_steps,
                      test, test_result, daily_completed, test_passed, streak_count, training_id))
            else:
                # insert
                cur.execute("""
                    INSERT INTO training_goals
                    (training_id, user_id, goal_id, goal_name, study_time,
                     daily_steps, test, test_result, daily_completed, test_passed, streak_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (training_id, user_id, goal_id, goal_name, study_time,
                      daily_steps, test, test_result, daily_completed, test_passed, streak_count))
        else:
            cur.execute("""
                INSERT INTO training_goals
                (user_id, goal_id, goal_name, study_time,
                 daily_steps, test, test_result, daily_completed, test_passed, streak_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, goal_id, goal_name, study_time,
                  daily_steps, test, test_result, daily_completed, test_passed, streak_count))

        common_db.mysql.connection.commit()

        cur.execute("""
            SELECT training_id, user_id, goal_id, goal_name, study_time,
                   daily_steps, test, test_result, daily_completed, test_passed, streak_count
            FROM training_goals
        """)
        rows = cur.fetchall()
        cur.close()

    data = []
    if not common_db.is_mysql:
        data = [dict(r) for r in rows]
    else:
        data = rows

    return jsonify(data), 200
