import mysql.connector
from mysql.connector import pooling
from flask import g
from dotenv import load_dotenv
import os
load_dotenv()

connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="chatbot_pool",
    pool_size=5,
    user = os.environ.get("USER"),
    password = os.environ.get("PW"),
    host = os.environ.get("HOST"),
    database = os.environ.get("DB")
)

def get_db_connection():
    """
    Gets a connection from the pool.
    We store it in Flask's 'g' object to reuse it within the same request.
    """
    if 'db_conn' not in g:
        g.db_conn = connection_pool.get_connection()
    return g.db_conn

def close_db_connection(e=None):
    """
    Returns the connection to the pool.
    This is automatically called by Flask at the end of each request.
    """
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close() # .close() on a pooled connection returns it to the pool

