# api_limits.py

from flask import Blueprint, request, jsonify
import common_db  # Модуль, где у вас определены is_mysql, get_sqlite_conn, mysql и т.д.

api_limits_bp = Blueprint('api_limits_bp', __name__)

MY_SECRET_API_KEY = "MY_SUPER_SECRET_KEY_123"

def check_api_key():
    api_key_header = request.headers.get("X-API-KEY", None)
    if api_key_header == MY_SECRET_API_KEY:
        return True
    
    api_key_param = request.args.get('api_key')
    if api_key_param == MY_SECRET_API_KEY:
        return True

    return False

@api_limits_bp.before_request
def before_request_api():
    if not check_api_key():
        return jsonify({"error": "Forbidden: Invalid API Key"}), 403

def get_sqlite_conn():
    """Вспомогательная функция для подключения к SQLite, если используется."""
    import sqlite3
    conn = sqlite3.connect('mydatabase.db')
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------------------------------------------------------
# Вспомогательные функции для пересчёта "общего" лимита
# -----------------------------------------------------------------------------
def calculate_limits_sum():
    """
    Возвращает (sum_others, current_total), где:
      sum_others — сумма limit_value для всех title != 'общий'
      current_total — значение limit_value для title='общий' (или 0, если нет)
    """
    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(limit_value),0) as sum_others "
            "FROM limit_dict WHERE title != ?",
            ("общий",)
        )
        sum_others = cur.fetchone()["sum_others"]

        cur.execute(
            "SELECT COALESCE(limit_value,0) as total_value "
            "FROM limit_dict WHERE title = ?",
            ("общий",)
        )
        row = cur.fetchone()
        current_total = row["total_value"] if row else 0
        conn.close()
    else:
        cur = common_db.mysql.connection.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(limit_value),0) as sum_others "
            "FROM limit_dict WHERE title != %s",
            ("общий",)
        )
        sum_others = cur.fetchone()["sum_others"]

        cur.execute(
            "SELECT COALESCE(limit_value,0) as total_value "
            "FROM limit_dict WHERE title = %s",
            ("общий",)
        )
        row = cur.fetchone()
        current_total = row["total_value"] if row else 0
        cur.close()

    return sum_others, current_total

def ensure_total_not_less_than(sum_others):
    """
    Если 'общий' лимит меньше, чем sum_others, поднимаем его до sum_others.
    Если 'общий' нет — создаём.
    """
    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM limit_dict WHERE title = ?", ("общий",))
        row = cur.fetchone()
        if row:
            if row["limit_value"] < sum_others:
                cur.execute(
                    "UPDATE limit_dict SET limit_value=? WHERE id=?",
                    (sum_others, row["id"])
                )
        else:
            cur.execute(
                "INSERT INTO limit_dict (title, limit_value) VALUES (?,?)",
                ("общий", sum_others)
            )
        conn.commit()
        conn.close()
    else:
        cur = common_db.mysql.connection.cursor()
        cur.execute("SELECT * FROM limit_dict WHERE title=%s", ("общий",))
        row = cur.fetchone()
        if row:
            if row["limit_value"] < sum_others:
                cur.execute(
                    "UPDATE limit_dict SET limit_value=%s WHERE id=%s",
                    (sum_others, row["id"])
                )
        else:
            cur.execute(
                "INSERT INTO limit_dict (title, limit_value) VALUES (%s, %s)",
                ("общий", sum_others)
            )
        common_db.mysql.connection.commit()
        cur.close()

# -----------------------------------------------------------------------------
# GET /limits — получить список лимитов
# -----------------------------------------------------------------------------
@api_limits_bp.route('/limits', methods=['GET'])
def get_all_limits():
    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM limit_dict")
        rows = cur.fetchall()
        conn.close()
    else:
        cur = common_db.mysql.connection.cursor()
        cur.execute("SELECT * FROM limit_dict")
        rows = cur.fetchall()
        cur.close()

    data = []
    if not common_db.is_mysql:
        data = [dict(r) for r in rows]
    else:
        data = rows  # MySQL DictCursor -> list of dict
    return jsonify(data), 200

# -----------------------------------------------------------------------------
# POST /limits — добавить или обновить лимит
# -----------------------------------------------------------------------------
@api_limits_bp.route('/limits', methods=['POST'])
def upsert_limit():
    payload = request.get_json() or {}
    title = payload.get("title")
    limit_value = payload.get("limit_value")

    if not title or limit_value is None:
        return jsonify({"error": "title and limit_value are required"}), 400

    # Преобразуем limit_value к int
    try:
        limit_value = int(limit_value)
        if limit_value < 0:
            return jsonify({"error": "limit_value must be non-negative"}), 400
    except ValueError:
        return jsonify({"error": "limit_value must be an integer"}), 400

    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()
        # Ищем запись
        cur.execute("SELECT * FROM limit_dict WHERE title = ?", (title,))
        row = cur.fetchone()

        if row:
            # update
            cur.execute(
                "UPDATE limit_dict SET limit_value=? WHERE id=?",
                (limit_value, row["id"])
            )
        else:
            # insert
            cur.execute(
                "INSERT INTO limit_dict (title, limit_value) VALUES (?, ?)",
                (title, limit_value)
            )
        conn.commit()

        # Пересчитываем сумму остальных
        sum_others, current_total = calculate_limits_sum()
        if title != "общий":
            if sum_others > current_total:
                ensure_total_not_less_than(sum_others)
        else:
            if limit_value < sum_others:
                ensure_total_not_less_than(sum_others)

        # Итоговый список
        cur.execute("SELECT * FROM limit_dict")
        rows = cur.fetchall()
        conn.close()
    else:
        # MySQL
        cur = common_db.mysql.connection.cursor()
        cur.execute("SELECT * FROM limit_dict WHERE title=%s", (title,))
        row = cur.fetchone()

        if row:
            cur.execute(
                "UPDATE limit_dict SET limit_value=%s WHERE id=%s",
                (limit_value, row["id"])
            )
        else:
            cur.execute(
                "INSERT INTO limit_dict (title, limit_value) VALUES (%s, %s)",
                (title, limit_value)
            )
        common_db.mysql.connection.commit()

        sum_others, current_total = calculate_limits_sum()
        if title != "общий":
            if sum_others > current_total:
                ensure_total_not_less_than(sum_others)
        else:
            if limit_value < sum_others:
                ensure_total_not_less_than(sum_others)

        cur.execute("SELECT * FROM limit_dict")
        rows = cur.fetchall()
        cur.close()

    data = []
    if not common_db.is_mysql:
        data = [dict(r) for r in rows]
    else:
        data = rows

    return jsonify(data), 200

# -----------------------------------------------------------------------------
# DELETE /limits/<title> — удалить лимит (кроме "общий")
# -----------------------------------------------------------------------------
@api_limits_bp.route('/limits/<string:title>', methods=['DELETE'])
def delete_limit(title):
    """
    Удаляет лимит (record) из limit_dict по указанному title, кроме "общий".
    Пример curl:
      curl -X DELETE \
           -H "X-API-KEY: MY_SUPER_SECRET_KEY_123" \
           http://localhost:5005/api/limits/Groceries
    """
    # Проверяем, не пытаются ли удалить "общий"
    if title == "общий":
        return jsonify({"error": "Cannot delete the main 'общий' limit"}), 403

    # Удаляем
    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()

        # Проверяем, есть ли такая запись
        cur.execute("SELECT * FROM limit_dict WHERE title = ?", (title,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return jsonify({"error": f"Limit '{title}' not found"}), 404

        # Удаляем
        cur.execute("DELETE FROM limit_dict WHERE title = ?", (title,))
        conn.commit()

        # После удаления пересчитываем сумму (на случай, 
        # если хотите автоматически уменьшать/увеличивать "общий", 
        # но обычно "общий" не занижаем. 
        # Хотите — можете добавить логику уменьшения.
        sum_others, current_total = calculate_limits_sum()
        # Если вдруг sum_others > current_total (маловероятно, но всё же)
        if sum_others > current_total:
            ensure_total_not_less_than(sum_others)

        # Возвращаем обновлённый список
        cur.execute("SELECT * FROM limit_dict")
        rows = cur.fetchall()
        conn.close()
    else:
        # MySQL
        cur = common_db.mysql.connection.cursor()
        cur.execute("SELECT * FROM limit_dict WHERE title=%s", (title,))
        row = cur.fetchone()
        if not row:
            cur.close()
            return jsonify({"error": f"Limit '{title}' not found"}), 404

        # Удаляем
        cur.execute("DELETE FROM limit_dict WHERE title=%s", (title,))
        common_db.mysql.connection.commit()

        sum_others, current_total = calculate_limits_sum()
        if sum_others > current_total:
            ensure_total_not_less_than(sum_others)

        cur.execute("SELECT * FROM limit_dict")
        rows = cur.fetchall()
        cur.close()

    data = []
    if not common_db.is_mysql:
        data = [dict(r) for r in rows]
    else:
        data = rows

    return jsonify(data), 200
