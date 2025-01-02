# api_costs.py

from flask import Blueprint, request, jsonify
# from common_db import is_mysql, get_sqlite_conn, mysql
import common_db  # <-- импортируем наш общий модуль

api_bp = Blueprint('api_bp', __name__)

# Ваш секретный ключ (для примера оставлен в коде)
MY_SECRET_API_KEY = "MY_SUPER_SECRET_KEY_123"

def check_api_key():
    """
    Проверяем, что передан корректный API-ключ.
    Возвращаем True/False. 
    """
    # 1) Смотрим заголовок X-API-KEY
    api_key_header = request.headers.get("X-API-KEY", None)
    if api_key_header == MY_SECRET_API_KEY:
        return True
    
    # 2) Или параметр ?api_key=...
    api_key_param = request.args.get('api_key')
    if api_key_param == MY_SECRET_API_KEY:
        return True

    return False

@api_bp.before_request
def before_request_api():
    """
    Хук, вызывается ПЕРЕД каждым запросом в Blueprint `api_bp`.
    Если ключ неверный, возвращаем 403 Forbidden.
    """
    if not check_api_key():
        return jsonify({"error": "Forbidden: Invalid API Key"}), 403


# --------------------------------------------------------------------
# Маршрут POST: выборка по году
# --------------------------------------------------------------------
@api_bp.route('/costs/year', methods=['POST'])
def get_costs_by_year():
    """
    Пример запроса:
      POST /api/costs/year
      Заголовок: X-API-KEY: MY_SUPER_SECRET_KEY_123
      Тело (JSON):
        {
          "year": "2025"
        }

    Возвращает JSON со всеми расходами за указанный год.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    year = data.get('year')
    if not year:
        return jsonify({"error": "year is required"}), 400

    if not is_mysql:
        # SQLite
        conn = get_sqlite_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM costs WHERE year = ?", (year,))
        rows = cur.fetchall()
        conn.close()
    else:
        # MySQL
        cur = common_db.mysql.connection.cursor()
        cur.execute("SELECT * FROM costs WHERE year = %s", (year,))
        rows = cur.fetchall()
        cur.close()

    data_list = []
    for row in rows:
        if not is_mysql:
            data_list.append(dict(row))  # sqlite3.Row -> dict
        else:
            data_list.append(row)        # MySQL DictCursor -> dict

    return jsonify(data_list), 200


# --------------------------------------------------------------------
# Маршрут POST: выборка по месяцу
# --------------------------------------------------------------------
@api_bp.route('/costs/month', methods=['POST'])
def get_costs_by_month():
    """
    Пример запроса:
      POST /api/costs/month
      Заголовок: X-API-KEY: MY_SUPER_SECRET_KEY_123
      Тело (JSON):
        {
          "year": "2025",
          "month": "01"
        }

    Возвращает JSON со всеми расходами за указанный месяц.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    year = data.get('year')
    month = data.get('month')
    if not (year and month):
        return jsonify({"error": "year, month are required"}), 400

    if not is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM costs WHERE year = ? AND month = ?", (year, month))
        rows = cur.fetchall()
        conn.close()
    else:
        cur = common_db.mysql.connection.cursor()
        cur.execute("SELECT * FROM costs WHERE year = %s AND month = %s", (year, month))
        rows = cur.fetchall()
        cur.close()

    data_list = []
    for row in rows:
        if not is_mysql:
            data_list.append(dict(row))
        else:
            data_list.append(row)

    return jsonify(data_list), 200
