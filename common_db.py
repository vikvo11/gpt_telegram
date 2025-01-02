# common_db.py

import sqlite3
from flask_mysqldb import MySQL

# По умолчанию используем SQLite
is_mysql = True
mysql = None
sqlite_db_path = 'mydatabase.db'

def get_sqlite_conn():
    """Подключение к локальной базе SQLite."""
    conn = sqlite3.connect(sqlite_db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_app(db_engine, flask_app):
    """
    Инициализируем движок: либо MySQL, либо SQLite
    db_engine: str ('mysql' или 'sqlite')
    flask_app: Flask-приложение
    """
    global is_mysql, mysql

    if db_engine.lower() == 'mysql':
        is_mysql = True
        # Настройка MySQL (пример для PythonAnywhere)
        flask_app.config['MYSQL_HOST'] = 'vorovik.mysql.pythonanywhere-services.com'
        flask_app.config['MYSQL_USER'] = 'vorovik'
        flask_app.config['MYSQL_PASSWORD'] = 'cb.,fq12-'
        flask_app.config['MYSQL_DB'] = 'vorovik$vorovikapp'
        flask_app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
        mysql = MySQL(flask_app)
        print("Используем MySQL.")
    else:
        is_mysql = False
        print("Используем SQLite (common_db).")