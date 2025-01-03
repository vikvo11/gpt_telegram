# api_delete.py

from flask import Blueprint, request, jsonify
import common_db  # <-- Ваш модуль, где is_mysql, mysql, get_sqlite_conn

api_delete_bp = Blueprint('api_delete_bp', __name__)

def get_sqlite_conn():
    """Вспомогательная функция для подключения к SQLite (если не используете MySQL)."""
    import sqlite3
    conn = sqlite3.connect('mydatabase.db')
    conn.row_factory = sqlite3.Row
    return conn


@api_delete_bp.route('/delete_record', methods=['POST'])
def delete_record():
    """
    Удаляет запись из одной из трёх таблиц: users, main_goals, training_goals.
    Принимает JSON вида:
    {
      "table": "users",          // или "main_goals", "training_goals"
      "id_field": "user_id",     // или "goal_id", "training_id"
      "id_value": 123
    }

    Возвращает JSON со статусом:
    {
      "deleted": true,
      "message": "Record deleted successfully"
    }
    либо ошибку, если не найдена запись или некорректные поля.
    """
    data = request.get_json() or {}
    table = data.get("table")      # "users", "main_goals", "training_goals"
    id_field = data.get("id_field")  # "user_id", "goal_id", "training_id"
    id_value = data.get("id_value")  # значение этого поля

    if not table or not id_field or id_value is None:
        return jsonify({"error": "table, id_field, and id_value are required"}), 400

    # Допустимые комбинации
    valid_tables = {
        "users": "user_id",
        "main_goals": "goal_id",
        "training_goals": "training_id"
    }

    # Проверяем корректность
    if table not in valid_tables:
        return jsonify({"error": f"Unknown table '{table}'"}), 400

    # Дополнительно убеждаемся, что id_field сходится с тем, что ожидается
    if valid_tables[table] != id_field:
        return jsonify({"error": f"For table '{table}', id_field must be '{valid_tables[table]}'"}), 400

    # Удаляем
    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()

        # Проверяем, что запись существует
        cur.execute(f"SELECT * FROM {table} WHERE {id_field} = ?", (id_value,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return jsonify({"error": f"Record with {id_field}={id_value} not found in table '{table}'"}), 404

        # Удаляем запись
        cur.execute(f"DELETE FROM {table} WHERE {id_field} = ?", (id_value,))
        conn.commit()
        conn.close()

    else:
        cur = common_db.mysql.connection.cursor()
        # Проверяем, что запись существует
        check_sql = f"SELECT * FROM {table} WHERE {id_field}=%s"
        cur.execute(check_sql, (id_value,))
        row = cur.fetchone()
        if not row:
            cur.close()
            return jsonify({"error": f"Record with {id_field}={id_value} not found in table '{table}'"}), 404

        del_sql = f"DELETE FROM {table} WHERE {id_field}=%s"
        cur.execute(del_sql, (id_value,))
        common_db.mysql.connection.commit()
        cur.close()

    return jsonify({
        "deleted": True,
        "message": f"Record with {id_field}={id_value} deleted successfully from '{table}'"
    }), 200
