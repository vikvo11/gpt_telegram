# api_limits.py

from flask import Blueprint, request, jsonify
# Импорт из вашего общего модуля, где объявлены:
#   is_mysql  -> bool
#   get_sqlite_conn() -> sqlite connection
#   mysql -> объект MySQL (или None)
#   check_api_key() -> если вы хотите повторно использовать общую проверку API-ключа
try:
    # from common_db import is_mysql, get_sqlite_conn, mysql
    import common_db  # <-- импортируем наш общий модуль
except ImportError:
    # или другой способ импорта, если у вас нет кольцевой зависимости
    pass

api_limits_bp = Blueprint('api_limits_bp', __name__)

# Для простоты берём тот же подход с API Key, как в предыдущих примерах
MY_SECRET_API_KEY = "MY_SUPER_SECRET_KEY_123"
# mysql = common_db.mysql

def check_api_key():
    """
    Проверяем, что передан корректный API-ключ.
    Возвращаем True/False.
    """
    api_key_header = request.headers.get("X-API-KEY")
    if api_key_header == MY_SECRET_API_KEY:
        return True
    
    api_key_param = request.args.get('api_key')
    if api_key_param == MY_SECRET_API_KEY:
        return True

    return False

@api_limits_bp.before_request
def before_request_api():
    """
    Перед каждым запросом к Blueprint `api_limits_bp` проверяем ключ.
    """
    if not check_api_key():
        return jsonify({"error": "Forbidden: Invalid API Key"}), 403


# -----------------------------------------------------------------------------
# Вспомогательная функция: пересчитать сумму всех лимитов (кроме "общий").
# Возвращает (sum_limits, общий_лимит)
# -----------------------------------------------------------------------------
def calculate_limits_sum():
    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()
        # Сумма всех, где title != "общий"
        cur.execute("SELECT COALESCE(SUM(limit_value),0) as sum_others FROM limit_dict WHERE title != ?", ("общий",))
        sum_others = cur.fetchone()["sum_others"]

        # Смотрим текущий общий
        cur.execute("SELECT COALESCE(limit_value,0) as total_value FROM limit_dict WHERE title = ?", ("общий",))
        row = cur.fetchone()
        current_total = row["total_value"] if row else 0

        conn.close()
    else:
        cur = common_db.mysql.connection.cursor()
        cur.execute("SELECT COALESCE(SUM(limit_value),0) as sum_others FROM limit_dict WHERE title != %s", ("общий",))
        sum_others = cur.fetchone()["sum_others"]

        cur.execute("SELECT COALESCE(limit_value,0) as total_value FROM limit_dict WHERE title = %s", ("общий",))
        row = cur.fetchone()
        current_total = row["total_value"] if row else 0
        cur.close()
    return sum_others, current_total


# -----------------------------------------------------------------------------
# Вспомогательная функция: обновить (или создать) общий лимит, если он меньше sum_others
# -----------------------------------------------------------------------------
def ensure_total_not_less_than(sum_others):
    """
    Если 'общий' лимит существует и меньше, чем sum_others,
    то поднимаем его до sum_others.
    Если 'общий' не существует, создаём со значением sum_others.
    """
    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()
        # Проверим, есть ли уже строка "общий"
        cur.execute("SELECT * FROM limit_dict WHERE title = ?", ("общий",))
        row = cur.fetchone()
        if row:
            # Сравнить
            if row["limit_value"] < sum_others:
                cur.execute("UPDATE limit_dict SET limit_value=? WHERE id=?", (sum_others, row["id"]))
        else:
            # Нет записи "общий" — создаём
            cur.execute("INSERT INTO limit_dict (title, limit_value) VALUES (?,?)", ("общий", sum_others))
        
        conn.commit()
        conn.close()

    else:
        cur = common_db.mysql.connection.cursor()
        cur.execute("SELECT * FROM limit_dict WHERE title=%s", ("общий",))
        row = cur.fetchone()
        if row:
            if row["limit_value"] < sum_others:
                cur.execute("UPDATE limit_dict SET limit_value=%s WHERE id=%s", (sum_others, row["id"]))
        else:
            cur.execute("INSERT INTO limit_dict (title, limit_value) VALUES (%s, %s)", ("общий", sum_others))

        common_db.mysql.connection.commit()
        cur.close()


# -----------------------------------------------------------------------------
# 1) GET /limits
#    Возвращает весь список лимитов (limit_dict), включая "общий".
# -----------------------------------------------------------------------------
@api_limits_bp.route('/limits', methods=['GET'])
def get_all_limits():
    """
    Пример запроса:
      GET /api/limits
      Заголовок: X-API-KEY: MY_SUPER_SECRET_KEY_123  (или ?api_key=)

    Возвращает JSON со всеми лимитами (title, limit_value).
    """
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
    for row in rows:
        if not common_db.is_mysql:
            data.append(dict(row))
        else:
            data.append(row)  # MySQL dictCursor -> dict

    return jsonify(data), 200


# -----------------------------------------------------------------------------
# 2) POST /limits
#    Добавляет или обновляет лимит. 
#    Если это "общий", проверяем, чтобы он не стал меньше суммы остальных.
#    Если это любой другой title, после добавления/обновления 
#    проверяем, чтобы "общий" >= сумма остальных.
# -----------------------------------------------------------------------------
@api_limits_bp.route('/limits', methods=['POST'])
def upsert_limit():
    """
    Пример curl:
      curl -X POST \
           -H "X-API-KEY: MY_SUPER_SECRET_KEY_123" \
           -H "Content-Type: application/json" \
           -d '{"title": "Groceries", "limit_value": 5000}' \
           http://localhost:5005/api/limits

    Если title не существует, создаём новую запись.
    Если есть — обновляем.
    Затем проверяем общую сумму (кроме "общий") и 
    делаем ensure_total_not_less_than(...).
    Если title == "общий", то тоже проверяем, 
    чтобы пользователь не занизил "общий" 
    (автоматически поднимем, если надо).
    
    Возвращаем весь список лимитов.
    """
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "No JSON body"}), 400

    title = payload.get("title")
    limit_value = payload.get("limit_value")

    if not title or limit_value is None:
        return jsonify({"error": "title and limit_value are required"}), 400

    try:
        limit_value = int(limit_value)
        if limit_value < 0:
            return jsonify({"error": "limit_value must be non-negative"}), 400
    except ValueError:
        return jsonify({"error": "limit_value must be an integer"}), 400

    # Добавляем / обновляем запись
    if not common_db.is_mysql:
        conn = get_sqlite_conn()
        cur = conn.cursor()

        # Ищем запись
        cur.execute("SELECT * FROM limit_dict WHERE title = ?", (title,))
        row = cur.fetchone()

        if row:
            # UPDATE
            cur.execute("UPDATE limit_dict SET limit_value=? WHERE id=?", (limit_value, row["id"]))
        else:
            # INSERT
            cur.execute("INSERT INTO limit_dict (title, limit_value) VALUES (?, ?)", (title, limit_value))

        conn.commit()

        # Теперь, если title != "общий", нужно пересчитать сумму остальных 
        # и убедиться, что общий >= sum_others.
        # Или, если title == "общий", нужно убедиться, 
        # что новый общий не меньше суммы остальных (поднять при необходимости).
        sum_others, current_total = calculate_limits_sum()
        if title != "общий":
            # Если sum_others > общий, поднимаем общий
            if sum_others > current_total:
                ensure_total_not_less_than(sum_others)
        else:
            # Если пользователь обновил "общий" и сделал его меньше sum_others
            if limit_value < sum_others:
                ensure_total_not_less_than(sum_others)

        # Возвращаем весь список лимитов
        cur.execute("SELECT * FROM limit_dict")
        rows = cur.fetchall()
        conn.close()

    else:
        # MySQL
        cur = common_db.mysql.connection.cursor()
        cur.execute("SELECT * FROM limit_dict WHERE title=%s", (title,))
        row = cur.fetchone()

        if row:
            cur.execute("UPDATE limit_dict SET limit_value=%s WHERE id=%s", (limit_value, row["id"]))
        else:
            cur.execute("INSERT INTO limit_dict (title, limit_value) VALUES (%s, %s)", (title, limit_value))
        common_db.mysql.connection.commit()

        # Аналогично, пересчёт
        sum_others, current_total = calculate_limits_sum()
        if title != "общий":
            if sum_others > current_total:
                ensure_total_not_less_than(sum_others)
        else:
            if limit_value < sum_others:
                ensure_total_not_less_than(sum_others)

        # Возвращаем весь список лимитов
        cur.execute("SELECT * FROM limit_dict")
        rows = cur.fetchall()
        cur.close()

    # Собираем итоговый JSON
    data = []
    if not common_db.is_mysql:
        for r in rows:
            data.append(dict(r))
    else:
        for r in rows:
            data.append(r)

    return jsonify(data), 200
