from flask import Flask, redirect, url_for, request, render_template, session
from openai import OpenAI
from dotenv import load_dotenv
import os
import markdown
from mysql.connector import Error

from db_connector import get_db_connection, close_db_connection

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)




app = Flask(__name__)

@app.teardown_appcontext
def teardown_db(exception):
    close_db_connection(exception)

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

@app.route('/')
def root():
    return redirect(url_for('home'))

@app.route('/home', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        user_prompt = request.form['query']
        response = client.responses.create(
            input=user_prompt,
            model="openai/gpt-oss-20b",
        )
        raw_markdown_from_api = response.output_text
        html_content = markdown.markdown(raw_markdown_from_api, extensions=['tables'])

        try:
            conn = get_db_connection()

            sql1 = """
                INSERT INTO CHATS
                (question, answer)
                VALUES (%s, %s)
            """
            sql2 = """
                INSERT INTO conversations
                (client, message, chat_id)
                VALUE(%s, %s, %s)
            """
            with conn.cursor() as cursor:

                cursor.execute(sql1,(user_prompt, html_content))
                new_chats_id = cursor.lastrowid
                cursor.execute(sql2,('user', user_prompt, new_chats_id))
                cursor.execute(sql2,('model', html_content, new_chats_id))
                conn.commit()
                print("data saved in DB via home")
                session['fid'] = new_chats_id

        except Exception as e:
            conn.rollback()
            print(f"database error: {e}")
        
        return redirect(url_for('conversation'))
    elif request.method == 'GET':
        return render_template('home.html')
    
@app.route('/home/conversation', methods=['POST','GET'])
def conversation():

    fid = session.pop('fid', None)
    data = None

    if fid and request.method == 'POST':
        user_prompt = request.form['query']

        try:
            conn = get_db_connection()
            sql = """
                SELECT id, client, message FROM conversations WHERE chat_id = %s ORDER BY time ASC
            """
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(sql,(fid,))
                data = cursor.fetchall()
            bot_input = "this is the previous conversation you had (ignore all the html tags or MD format you see, just focus on the content, also user: and model: flags the start of the question and your response respectively, they were not part of the conversation they are just pointing the qquestion and response):-  "
            for dict in data:
                for key, value in dict.items():
                    if key == 'client' or key == 'user':
                        bot_input += dict['client'] + ": " + dict['message'] + " "
            bot_input+=user_prompt
                
        except Error as e:
            print(f"Error: {e}")
            data = []

        response = client.responses.create(
            input=bot_input,
            model="openai/gpt-oss-20b",
        )
        raw_markdown_from_api = response.output_text
        html_content = markdown.markdown(raw_markdown_from_api, extensions=['tables'])

        try:
            conn = get_db_connection()

            sql = """
                INSERT INTO conversations
                (client, message, chat_id)
                VALUE(%s, %s, %s)
            """
            with conn.cursor() as cursor:
                cursor.execute(sql,('user', user_prompt, fid)) 
                cursor.execute(sql,('model', html_content, fid))
                conn.commit()
                print("data saved in DB via conversation")
                session['fid'] = fid

        except Exception as e:
            conn.rollback()
            print(f"database error: {e}")

    if fid:
        try:

            conn = get_db_connection()

            sql = """
                SELECT id, client, message, time, chat_id FROM conversations WHERE chat_id = %s ORDER BY time ASC
            """

            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(sql,(fid,))
                data = cursor.fetchall()
            session['fid'] = fid


        except Error as e:
            print(f"Error: {e}")
            data = []
        
    else:
        print("Warning: fid missing")
        data = None
    return render_template('conversation.html', convo=data)

    
@app.route('/chats')
def history():
    try:
        conn = get_db_connection()

        sql = """
            SELECT id, question, time FROM chats ORDER BY time DESC
        """

        data = None
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql)
            data = cursor.fetchall()
    except Error as e:
        print(f"error reading data: {e}")
        data = []

    return render_template('chats.html', conversations=data)

@app.route('/chats/<qid>')
def solution(qid):
    session['fid'] = qid
    return redirect(url_for('conversation'))



if __name__ == '__main__':
    app.run(debug=True)
