import os;
import telebot;
import logging;
from config import * ;
from flask import Flask, request
import psycopg2

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)

db_connection = psycopg2.connect( DB_URI, sslmode = "require")
db_object = db_connection.cursor()


@bot.message_handler(commands=["start"])
def start(message):
    id = message.from_user.id
    username = message.from_user.username
    fullname = message.from_user.first_name + ' ' + message.from_user.last_name

    db_object.execute(f"SELECT id FROM users WHERE id = {id}")
    result = db_object.fetchone()

    if not result:
        questions = db_object.execute("SELECT * FROM questions")
        question_records = db_object.fetchall()
        bot.send_message(message.chat.id,
f"""Hello👋🏼
I'm going to take you through {len(question_records)} questions to find out your English level 📚🎓
Please be patient and carefully reply to all the questions🙏🏼
The test will take no more than 20 minutes😊
Good luck🤞🏼""")


        db_object.execute("INSERT INTO users(id, username, current_exercise, fullname) VALUES(%s,%s,%s,%s)",(id, username, 1, fullname))
        db_object.execute("SELECT * FROM questions WHERE question_id = 1 ")
        first_question = db_object.fetchone()
        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row(f'{first_question[2]}', f'{first_question[3]}', f'{first_question[4]}', f'{first_question[5]}')
        bot.send_message(message.chat.id,
f"""{first_question[0]}. Fill in the gap:
{first_question[1]}""",reply_markup=keyboard)
        db_connection.commit();

@bot.message_handler(content_types=['text'])
def after_text(message):
    id = message.from_user.id
    db_object.execute(f"SELECT current_exercise FROM users WHERE id = {id}")
    result = db_object.fetchone()
    next_exercise_id = result[0] + 1
    db_object.execute(f"SELECT * FROM questions WHERE question_id = { next_exercise }")
    next_exercise = db_object.fetchone()
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    keyboard.row(f'{next_exercise[2]}', f'{next_exercise[3]}', f'{next_exercise[4]}', f'{next_exercise[5]}')
    bot.send_message(message.chat.id,
                     f"""{next_exercise[0]}. Fill in the gap:
    {next_exercise[1]}""", reply_markup=keyboard)
    db_connection.commit();



    print(next_exercise)

    # if message.text=="Кнопка":
    #     bot.send_message(message.chat.id,"https://habr.com/ru/users/lubaznatel/")


@server.route(f"/{BOT_TOKEN}",methods = ["POST"])
def redirect_message():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url = APP_URL)
    server.run(host="0.0.0.0", port= int(os.environ.get("PORT",5000)))
