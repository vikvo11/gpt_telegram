# common_db.py

import sqlite3
#from flask_mysqldb import MySQL

# По умолчанию пусть будет SQLite
# is_mysql = True
# mysql = None  # Позже инициализируем
sqlite_db_path = 'mydatabase.db'

def get_sqlite_conn():
    conn = sqlite3.connect(sqlite_db_path)
    conn.row_factory = sqlite3.Row
    return conn

# def init_app(db_engine, flask_app):
#     """
#     Инициализируем движок: либо MySQL, либо SQLite
#     db_engine: str ('mysql' или 'sqlite')
#     flask_app: Flask-приложение
#     """
#     global is_mysql, mysql

#     if db_engine.lower() == 'mysql':
#         is_mysql = True
#         # Настройка MySQL
#         flask_app.config['MYSQL_HOST'] = 'vorovik.mysql.pythonanywhere-services.com'
#         flask_app.config['MYSQL_USER'] = 'vorovik'
#         flask_app.config['MYSQL_PASSWORD'] = 'cb.,fq12-'
#         flask_app.config['MYSQL_DB'] = 'vorovik$vorovikapp'
#         flask_app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#         mysql = MySQL(flask_app)
#         print("Используем MySQL.")
#     else:
#         is_mysql = False
#         # Если SQLite — можем инициализировать базу (db_init.init_sqlite()),
#         # но тогда нужно аккуратно импортировать db_init здесь или вызывать init_sqlite() в app.py
#         print("Используем SQLite (common_db).")
