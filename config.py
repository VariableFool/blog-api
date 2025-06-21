from dotenv import load_dotenv
import os
import pymysql
import pymysql.cursors

load_dotenv()

db_config = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "cursorclass": pymysql.cursors.DictCursor,
}

SECRET_KEY = os.getenv("SECRET_KEY")


def get_db_connection():
    return pymysql.connect(**db_config)
