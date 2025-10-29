import mysql.connector
from mysql.connector import errorcode

DB_CONFIG = {
    'user': 'chatbot_user',
    'password': '1234@',
    'host': 'localhost',
    'database': 'groq_chatbot_db'
}

CREATE_TABLE_chats_SQL = """
CREATE TABLE chats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""
CREATE_TABLE_conversations_SQL = """
CREATE TABLE conversations (
     id INT AUTO_INCREMENT PRIMARY KEY,
     client VARCHAR(100) NOT NULL,
     message TEXT NOT NULL,
     time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     chat_id INT NOT NULL,
     CONSTRAINT fk_converations_chats
     FOREIGN KEY (chat_id) REFERENCES chats(id)
     );
"""



connection = None

try:
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    try:
        print("creating table")
        cursor.execute(CREATE_TABLE_chats_SQL)
        cursor.execute(CREATE_TABLE_conversations_SQL)
        print("OK")
    except mysql.connector.Error as err:
        print(err.msg)
except mysql.connector.Error as err:
    print(err.msg)
finally:
    if connection and connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection closed")



