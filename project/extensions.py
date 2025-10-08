import pymysql
from pymysql.cursors import DictCursor
from flask import g, current_app

def get_db():
    if "db" not in g:
        c = current_app.config
        g.db = pymysql.connect(
            host=c["MYSQL_HOST"],
            port=c["MYSQL_PORT"],
            user=c["MYSQL_USER"],
            password=c["MYSQL_PASSWORD"],
            database=c["MYSQL_DB"],
            cursorclass=DictCursor,
            autocommit=False,
            charset="utf8mb4",
        )
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()
