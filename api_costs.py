# api_costs.py

from flask import Blueprint, request, jsonify
import common_db

api_bp = Blueprint('api_bp', __name__)

# Ваш секретный ключ (для примера оставлен в коде)
MY_SECRET_API_KEY = "MY_SUPER_SECRET_KEY_123"

def check_api_key():
    api_key_header = request.headers.get("X-API-KEY", None)
    if api_key_header == MY_SECRET_API_KEY:
        return True
    api_key_param = request.args.get('api_key')
    if api_key_param == MY_SECRET_API_KEY:
        return True
    return False

@api_bp.before_request
def before_request_api():
    if not check_api_key():
        return jsonify({"error": "Forbidden: Invalid API Key"}), 403

def get_sqlite_conn():
    """Помощник для SQLite (если не используете, уберите)."""
    import sqlite3
    conn = sqlite3.connect('mydatabase.db')
    conn.row_factory = sqlite3.Row
    return conn

# --------------------------------------------------------------------
# СТАРЫЕ ЭНДПОИНТЫ (оставляем на случай совместимости)
# --------------------------------------------------------------------
@api_bp.route('/costs/year', methods=['POST'])
def get_costs_by_year():
    """
    Пример:
      POST /api/costs/year
      {
        "year": "2025"
      }
    Возвращает все расходы за указанный год.
    """
    data = request.get_json() or {}
    year = data.get('year')
    if not year:
        return jsonify({"error": "year is required"}), 400

    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()
        sql = "SELECT * FROM costs WHERE year = ?"
        cur.execute(sql, (year,))
        rows = cur.fetchall()
        conn.close()
    else:
        cur = common_db.mysql.connection.cursor()
        sql = "SELECT * FROM costs WHERE year = %s"
        cur.execute(sql, (year,))
        rows = cur.fetchall()
        cur.close()

    data_list = [dict(r) if not common_db.is_mysql else r for r in rows]
    return jsonify(data_list), 200

@api_bp.route('/costs/month', methods=['POST'])
def get_costs_by_month():
    """
    Пример:
      POST /api/costs/month
      {
        "year": "2025",
        "month": "01"
      }
    Возвращает все расходы за указанный год+месяц.
    """
    data = request.get_json() or {}
    year = data.get('year')
    month = data.get('month')
    if not year or not month:
        return jsonify({"error": "year, month are required"}), 400

    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()
        sql = "SELECT * FROM costs WHERE year = ? AND month = ?"
        cur.execute(sql, (year, month))
        rows = cur.fetchall()
        conn.close()
    else:
        cur = common_db.mysql.connection.cursor()
        sql = "SELECT * FROM costs WHERE year = %s AND month = %s"
        cur.execute(sql, (year, month))
        rows = cur.fetchall()
        cur.close()

    data_list = [dict(r) if not common_db.is_mysql else r for r in rows]
    return jsonify(data_list), 200

# --------------------------------------------------------------------
# НОВЫЙ ЭНДПОИНТ: /costs/range (POST) для диапазона (start_year/month -> end_year/month)
# --------------------------------------------------------------------
@api_bp.route('/costs/range', methods=['POST'])
def get_costs_by_range():
    """
    Пример запроса:
      POST /api/costs/range
      {
        "start_year": "2024",
        "start_month": "03",
        "end_year": "2025",
        "end_month": "05"
      }

    Если какое-то поле не передано:
      - start_month по умолчанию "01"
      - end_month по умолчанию "12"
      - start_year / end_year обязательны.

    Возвращает все расходы, у которых (year||month) находится между
    (start_year||start_month) и (end_year||end_month) включительно.
    """
    data = request.get_json() or {}

    start_year = data.get('start_year')
    end_year = data.get('end_year')

    if not start_year or not end_year:
        return jsonify({"error": "start_year and end_year are required"}), 400

    start_month = data.get('start_month', '01')
    end_month = data.get('end_month', '12')

    # Проверка, что они двухзначные (например, "01".."12")
    if len(start_month) == 1:
        start_month = f"0{start_month}"
    if len(end_month) == 1:
        end_month = f"0{end_month}"

    # Создаём сравнимые строки "YYYYMM"
    start_ym = f"{start_year}{start_month}"
    end_ym = f"{end_year}{end_month}"

    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()
        # Поскольку year и month - текст, формируем "year||month"
        # Сравниваем как строки ("202401" <= "202402" и т.п.)
        sql = """
            SELECT * FROM costs
            WHERE (year || month) >= ?
              AND (year || month) <= ?
            ORDER BY year, month
        """
        cur.execute(sql, (start_ym, end_ym))
        rows = cur.fetchall()
        conn.close()
    else:
        cur = common_db.mysql.connection.cursor()
        # В MySQL можно объединять year и month (оба строки)
        # если они хранятся в VARCHAR(4) и VARCHAR(2), то CONCAT(year, month)
        # пример:
        sql = """
            SELECT * FROM costs
            WHERE CONCAT(year, LPAD(month, 2, '0')) >= %s
              AND CONCAT(year, LPAD(month, 2, '0')) <= %s
            ORDER BY year, month
        """
        # LPAD(month,2,'0') на случай, если month может быть '1' вместо '01'.
        cur.execute(sql, (start_ym, end_ym))
        rows = cur.fetchall()
        cur.close()

    data_list = [dict(r) if not common_db.is_mysql else r for r in rows]
    return jsonify(data_list), 200
