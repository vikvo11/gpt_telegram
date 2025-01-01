#import pymongo
#from pymongo import MongoClient
import json
#from bson import BSON
#from bson import json_util

# Импортируем blueprint из api_costs
from api_costs import api_bp
from api_limits import api_limits_bp  # <-- Импортируем ваш новый Blueprint

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    abort,
    url_for,
    logging,
    jsonify,
    make_response
)
import requests
import re
import telebot
from telebot import types
from functools import wraps
from HTTP_basic_Auth import auths
from flask_sslify import SSLify
from misck import token, chat_id_old

# Подключаем нашу инициализацию
import db_init  # модуль инициализации таблиц для SQLite
import common_db  # <-- импортируем наш общий модуль

# ----------------------------------------------------
# Для MySQL
from flask_mysqldb import MySQL

# Для SQLite
import sqlite3




def get_sqlite_conn():
    """Подключение к локальной базе SQLite."""
    conn = sqlite3.connect('mydatabase.db')  # <-- Путь к вашему файлу БД
    conn.row_factory = sqlite3.Row
    return conn

# ----------------------------------------------------
# Настройки Flask
# ----------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'morkovka18'
app.debug = True
sslify = SSLify(app)

# Выбираем движок БД
#  'mysql' или 'sqlite'
# ----------------------------------------------------
db_engine = 'mysql'
# db_engine = 'sqlite'
if db_engine == "mysql":
        
        mysql = MySQL(app)
        print("Используем MySQL.")
# ----------------------------------------------------

# Инициализируем движок
common_db.init_app(db_engine,app)


# Если выбрали SQLite, создаём таблицы (если их нет)
if not common_db.is_mysql:
    db_init.init_sqlite()

# После создания объекта `app = Flask(__name__)` регистрируем Blueprint:
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(api_limits_bp, url_prefix='/api')

# Проверяем, какой движок используем
is_mysql = (db_engine.lower() == 'mysql')


global last_msg
last_msg = ''

curs = 3    # 1=RUB; 3=CZK
currency = 'CZK'  # 'RUB'
limit_value = 'limit_czk_value'  # 'limit_value' - RUB

URL = 'https://api.telegram.org/bot{}/'.format(token)
bot = telebot.TeleBot(token)

# key_default = types.ReplyKeyboardMarkup(resize_keyboard=True)
# key_default.row(types.KeyboardButton('Button 1'))
# key_default.row(types.KeyboardButton('Button 2'))
# key_default.row(types.KeyboardButton('Button 3'))

# @bot.message_handler(content_types=["text"])
# def default_test(message):
#     keyboard = types.InlineKeyboardMarkup()
#     url_button = types.InlineKeyboardButton(text="Перейти на Яндекс", url="https://ya.ru")
#     keyboard.add(url_button)
#     bot.send_message(message.chat.id, "Привет! Нажми на кнопку и перейди в поисковик.", reply_markup=keyboard)

# @bot.message_handler(func=lambda message: message.text == u'Button 1')
# def button(message):
#     bot.send_message(chat_id_old, 'Сюда пишем текст типо - Привет')

def write_json(data, filename='answer.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_updates():
    url = URL + 'getUpdates'
    r = requests.get(url)
    write_json(r.json())
    return r.json()

def send_message(chatId, text='Please wait a few seconds...!'):
    url = URL + 'sendMessage'
    answer = {'chat_id': chatId, 'text': text}
    print(answer)
    request = requests.post(url, data=answer)
    print(request.json())
    return request.json()

def parc_text(text):
    pattern = r'/\S+'
    crypto = re.search(pattern, text).group()
    return crypto[1:]

def parc_text_cost(text):
    pattern = r' \-?[0-9]\d*(\.\d+)?$'
    cost = re.search(pattern, text).group()
    return cost[1:]

def get_price(crypto):
    url = 'https://api.coinmarketcap.com/v1/ticker/{}/'.format(crypto)
    r = requests.get(url).json()
    price = r[-1]['price_usd']
    return price

#Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            return redirect(url_for('login'))
    return wrap

@app.route('/')
@is_logged_in
def home():
    return redirect(url_for('dashbord'))

#Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))

#User Login
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        if auths(username, password_candidate):
            session['logged_in'] = True
            return redirect(url_for('dashbord'))
        else:
            error='Invalid login'
            return render_template('login.html', error=error)
    return render_template('login.html')

#Dashbord
@app.route('/dashbord',methods=['GET','POST'])
@is_logged_in
def dashbord():
    msg = mysqls('costs')
    return render_template('dashbordpymongo.html', articles=msg)


@app.route('/webhooks/',methods=['POST','GET'])
def webhook():
    if request.method == 'POST':
        r = request.get_json()
        answer = {'chat_id': 488735610, 'text': 'text'}
        requests.post('https://api.telegram.org/bot{}/sendMessage'.format(token), data=answer).text
        return '', 200
    return '<h1>Hello bot</h1>'

@app.route('/webhooks_test/',methods=['POST','GET'])
def webhook_test():
    if request.method == 'POST':
        try:
            r = request.get_json()
            chat_id = r['message']['chat']['id']
            text = r['message']['text']
            global last_msg
            last_msg=json.dumps(r, ensure_ascii=False)

            pattern = r'/\S+'
            patternSum = r'/сумма'
            patternLim = r'/лимит'
            patternStart = r'/start'
            patternChat =r'/чат'

            if re.search(patternLim, text):
                # Показать лимиты
                if not is_mysql:
                    # SQLite
                    conn = get_sqlite_conn()
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT title, limits, cost 
                        FROM costs 
                        WHERE year=strftime('%Y', 'now')
                          AND month=strftime('%m','now')
                          AND title != ?
                    """, ('кредит',))
                    Lims = cur.fetchall()
                    conn.close()

                    limmsg_final = []
                    for Lim in Lims:
                        t = Lim['title']
                        c = Lim['cost']
                        l = Lim['limits']
                        limmsg_final.append(f"{t}: текущий = {c}{currency}, лимит={l}{currency}")

                    send_message(chat_id, "\n".join(limmsg_final))
                else:
                    # MySQL
                    cur = mysql.connection.cursor()
                    cur.execute("""
                        SELECT title, limits, cost 
                        FROM costs
                        WHERE year = (Select Year(CURDATE()))
                          AND month = (Select Month(CURDATE()))
                          AND title != %s
                    """, ('кредит',))
                    Lims = cur.fetchall()
                    cur.close()
                    limmsg_final = []
                    for Lim in Lims:
                        t = Lim['title']
                        c = Lim['cost']
                        l = Lim['limits']
                        limmsg_final.append(f"{t}: текущий = {c}{currency}, лимит={l}{currency}")

                    send_message(chat_id, "\n".join(limmsg_final))

                return jsonify(r)

            if re.search(patternSum, text):
                # Показать сумму
                if not is_mysql:
                    # SQLite
                    conn = get_sqlite_conn()
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT SUM(cost) as summa 
                        FROM costs 
                        WHERE year=strftime('%Y', 'now') 
                          AND month=strftime('%m','now') 
                          AND title != ?
                    """, ('кредит',))
                    Sum = cur.fetchone()
                    conn.close()
                    send_message(chat_id, 'Общая потраченная сумма в этом месяце = '+str(Sum['summa']))
                else:
                    # MySQL
                    cur = mysql.connection.cursor()
                    cur.execute("""
                        SELECT SUM(cost) as summa
                        FROM costs
                        WHERE year = (Select Year(CURDATE()))
                          AND month = (Select Month(CURDATE()))
                          AND title != %s
                    """, ('кредит',))
                    Sum = cur.fetchone()
                    cur.close()
                    send_message(chat_id, 'Общая потраченная сумма в этом месяце = '+str(Sum['summa']))

                return jsonify(r)
            
            if re.search(patternChat,text):
                send_message(chat_id,'Chat_ID = '+str(chat_id))
                return jsonify(r)

            if re.search(pattern, text) and not re.search(patternLim, text) and not re.search(patternSum, text) and not re.search(patternStart, text):
                cost = parc_text_cost(text).replace(" ", "")
                title = str(parc_text(text))
                msg_text = update_costs('costs', title, int(cost))
                send_message(chat_id, msg_text)
                return jsonify(r)

        except Exception as ex:
            print('EXCEPT:', ex)
            return '', 200
        return '', 200
    return '<h1>Hello bot</h1>'


@app.route('/last_msg/',methods=['POST','GET'])
def teslast():
    r = '<h2>{}</h2>'.format(str(last_msg))
    return r


# ------------------------------------------------------------------------------
# Универсальные функции для SELECT, INSERT, UPDATE
# ------------------------------------------------------------------------------
def mysqls(table):
    """Получить все данные из таблицы (замена предыдущего mysqls)."""
    if not is_mysql:
        # SQLite
        conn = get_sqlite_conn()
        cur = conn.cursor()
        sql = f"SELECT * FROM {table}"
        cur.execute(sql)
        rows = cur.fetchall()
        conn.close()
        return rows
    else:
        # MySQL
        cur = mysql.connection.cursor()
        result = cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        cur.close()
        return rows

def add_costs(table, title, cost):
    """Добавляем данные в таблицу costs."""
    if not is_mysql:
        # SQLite
        conn = get_sqlite_conn()
        cur = conn.cursor()
        sql = f"""
          INSERT INTO {table}(title, cost, year, month)
          VALUES (?, ?, strftime('%Y','now'), strftime('%m','now'))
        """
        cur.execute(sql, (title, cost))
        conn.commit()
        conn.close()
        return 'ok'
    else:
        # MySQL
        cur = mysql.connection.cursor()
        cur.execute(f"""
            INSERT INTO {table}(title, cost, year, month)
            VALUES (%s, %s, (Select Year(CURDATE())), (Select Month(CURDATE())))
        """, (title, cost))
        mysql.connection.commit()
        cur.close()
        return 'ok'

def update_costs(table, title, cost):
    """
    Обновляем запись, либо вставляем новую.
    Учитываем таблицу limit_dict (аналоги в SQLite и в MySQL).
    """
    if not is_mysql:
        # ================== SQLite ===================
        conn = get_sqlite_conn()
        cur = conn.cursor()

        # Проверяем, есть ли уже строка за текущий год и месяц
        sql_check = f"""
            SELECT * FROM {table}
            WHERE title=?
              AND year=strftime('%Y','now')
              AND month=strftime('%m','now')
        """
        cur.execute(sql_check, (title,))
        row = cur.fetchone()

        # Проверяем, есть ли запись в limit_dict
        sql_limit = "SELECT * FROM limit_dict WHERE title=?"
        cur.execute(sql_limit, (title,))
        limit_row = cur.fetchone()
        limit_exists = (limit_row is not None)

        if row:
            # UPDATE
            if limit_exists:
                cur.execute(f"""
                    UPDATE {table}
                    SET cost=cost+?,
                        limits=limits-?
                    WHERE title=?
                      AND year=strftime('%Y','now')
                      AND month=strftime('%m','now')
                """, (cost, cost, title))
            else:
                cur.execute(f"""
                    UPDATE {table}
                    SET cost=cost+?
                    WHERE title=?
                      AND year=strftime('%Y','now')
                      AND month=strftime('%m','now')
                """, (cost, title))

            conn.commit()
            # Получаем обновлённую запись
            cur.execute(sql_check, (title,))
            updated_row = cur.fetchone()
        else:
            # INSERT
            if limit_exists:
                new_limit = int(limit_row[limit_value]) - cost
                cur.execute(f"""
                    INSERT INTO {table}(title, cost, year, month, limits)
                    VALUES (?, ?, strftime('%Y','now'), strftime('%m','now'), ?)
                """, (title, cost, new_limit))
            else:
                cur.execute(f"""
                    INSERT INTO {table}(title, cost, year, month)
                    VALUES (?, ?, strftime('%Y','now'), strftime('%m','now'))
                """, (title, cost))

            conn.commit()
            cur.execute(sql_check, (title,))
            updated_row = cur.fetchone()

        # Если есть лимит, выводим «остаток общего лимита»
        if limit_exists:
            # Смотрим общий лимит
            cur.execute("SELECT * FROM limit_dict WHERE title=?", ('общий',))
            limitsSum = cur.fetchone()

            # Считаем сумму (кроме 'кредит')
            cur.execute(f"""
                SELECT SUM(cost) as summa
                FROM {table}
                WHERE year=strftime('%Y','now')
                  AND month=strftime('%m','now')
                  AND title != ?
            """, ('кредит',))
            total_sum = cur.fetchone()

            if limitsSum and total_sum:
                total_spent = total_sum['summa'] if total_sum['summa'] else 0
                test_sum = int(limitsSum[limit_value]) - int(total_spent)
                if test_sum < 10000/curs:
                    totallimit = f'Заканчивается общий лимит!!! Осталось ={test_sum} {currency}'
                else:
                    totallimit = ''
            else:
                totallimit = ''

            conn.close()
            return (f"Затраты в текущем месяце на {updated_row['title']}= {updated_row['cost']} {currency}. "
                    f"Лимит = {updated_row['limits']} {currency} {totallimit}")
        else:
            conn.close()
            return (f"Затраты в текущем месяце на {updated_row['title']}= {updated_row['cost']} {currency}")

    else:
        # ================== MySQL ===================
        cur = mysql.connection.cursor()

        # Проверяем, есть ли уже строка за текущий год и месяц
        sql_check = f"""
            SELECT * FROM {table}
            WHERE title=%s
              AND year=(SELECT YEAR(CURDATE()))
              AND month=(SELECT MONTH(CURDATE()))
        """
        cur.execute(sql_check, (title,))
        row = cur.fetchone()

        # Проверяем, есть ли запись в limit_dict
        sql_limit = "SELECT * FROM limit_dict WHERE title=%s"
        cur.execute(sql_limit, (title,))
        limit_row = cur.fetchone()
        limit_exists = (limit_row is not None)

        if row:
            # UPDATE
            if limit_exists:
                cur.execute(f"""
                    UPDATE {table}
                    SET cost=cost+%s,
                        limits=limits-%s
                    WHERE title=%s
                      AND year=(SELECT YEAR(CURDATE()))
                      AND month=(SELECT MONTH(CURDATE()))
                """, (cost, cost, title))
            else:
                cur.execute(f"""
                    UPDATE {table}
                    SET cost=cost+%s
                    WHERE title=%s
                      AND year=(SELECT YEAR(CURDATE()))
                      AND month=(SELECT MONTH(CURDATE()))
                """, (cost, title))

            mysql.connection.commit()
            # Получаем обновлённую запись
            cur.execute(sql_check, (title,))
            updated_row = cur.fetchone()
        else:
            # INSERT
            if limit_exists:
                new_limit = int(limit_row[limit_value]) - cost
                cur.execute(f"""
                    INSERT INTO {table}(title, cost, year, month, limits)
                    VALUES (%s, %s, YEAR(CURDATE()), MONTH(CURDATE()), %s)
                """, (title, cost, new_limit))
            else:
                cur.execute(f"""
                    INSERT INTO {table}(title, cost, year, month)
                    VALUES (%s, %s, YEAR(CURDATE()), MONTH(CURDATE()))
                """, (title, cost))

            mysql.connection.commit()
            cur.execute(sql_check, (title,))
            updated_row = cur.fetchone()

        # Выводим результат. Если есть лимит, покажем общий лимит
        if limit_exists:
            # Получаем запись про общий лимит
            cur.execute("SELECT * FROM limit_dict WHERE title=%s", ('общий',))
            limitsSum = cur.fetchone()

            # Считаем сумму расходов (кроме 'кредит')
            cur.execute(f"""
                SELECT SUM(cost) as summa
                FROM {table}
                WHERE year=(SELECT YEAR(CURDATE()))
                  AND month=(SELECT MONTH(CURDATE()))
                  AND title != %s
            """, ('кредит',))
            total_sum = cur.fetchone()

            if limitsSum and total_sum:
                total_spent = total_sum['summa'] if total_sum['summa'] else 0
                test_sum = int(limitsSum[limit_value]) - int(total_spent)
                if test_sum < 10000/curs:
                    totallimit = f'Заканчивается общий лимит!!! Осталось ={test_sum} {currency}'
                else:
                    totallimit = ''
            else:
                totallimit = ''

            cur.close()
            return (f"Затраты в текущем месяце на {updated_row['title']}= {updated_row['cost']} {currency}. "
                    f"Лимит = {updated_row['limits']} {currency} {totallimit}")
        else:
            cur.close()
            return (f"Затраты в текущем месяце на {updated_row['title']}= {updated_row['cost']} {currency}")

def main():
    pass

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5005, debug=True)


if __name__ == '__main__':
    #bot.polling(none_stop=True)
    main()