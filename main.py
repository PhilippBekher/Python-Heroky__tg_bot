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


        db_object.execute("INSERT INTO users(id, username, current_exercise, fullname, right_answers_number) VALUES(%s,%s,%s,%s,%s)",(id, username, 1, fullname, 0,))
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
    questions = db_object.execute("SELECT * FROM questions")
    question_records = db_object.fetchall()

    id = message.from_user.id
    db_object.execute(f"SELECT current_exercise, right_answers_number FROM users WHERE id = {id}")
    result = db_object.fetchone()

    if result[0] == len(question_records):
        current_exercise_right_answer = db_object.execute(
            f"SELECT right_answer FROM questions WHERE question_id = {result[0]}")
        right_answer_object = db_object.fetchone()
        final_right_answers_number = result[1]

        if message.text == right_answer_object[0]:
            current_exercise_right_answer = db_object.execute(
                f"SELECT right_answer FROM questions WHERE question_id = {result[0]}")
            right_answer_object = db_object.fetchone()
            current_right_answers_number = result[1] + 1
            final_right_answers_number = current_right_answers_number
            db_object.execute(f"UPDATE users SET right_answers_number = %s WHERE id = {id}",
                              (current_right_answers_number,))
            db_connection.commit();

        level = ''
        percent_of_right_answers = final_right_answers_number/len(question_records)

        if 0 <= percent_of_right_answers <= 0.17:
            level = 'Beginner'
        elif 0.17 < percent_of_right_answers <= 0.37:
            level = 'Elementary'
        elif 0.37 < percent_of_right_answers <= 0.53:
            level = 'Pre-Intermediate'
        elif 0.53 < percent_of_right_answers <= 0.73:
            level = 'Intermediate'
        elif 0.73 < percent_of_right_answers <= 0.9:
            level = 'Upper-Intermediate'
        else:
            level = 'Advanced'

        db_object.execute(f"SELECT right_answers_number FROM users WHERE id = {id}")
        current_number_of_right_answers = db_object.fetchone()
        bot.send_message(message.chat.id,
f"""Thank you for taking the test😊
Number of right answers is: { current_number_of_right_answers[0] } 
Your level is: {level}
We'll contact you very soon🙂""", reply_markup = ReplyKeyboardRemove())
        db_object.execute(f"UPDATE users SET level = %s WHERE id = {id}", (level,))
        db_connection.commit()

    if result[0] < len(question_records):
        next_exercise_id = result[0] + 1
        db_object.execute(f"SELECT * FROM questions WHERE question_id = {next_exercise_id}")
        next_exercise = db_object.fetchone()
        db_object.execute(f"UPDATE users SET current_exercise = %s WHERE id = {id}", (next_exercise_id,))

        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row(f'{next_exercise[2]}', f'{next_exercise[3]}', f'{next_exercise[4]}', f'{next_exercise[5]}')
        bot.send_message(message.chat.id,
f"""{next_exercise[0]}. Fill in the gap:
{next_exercise[1]}""", reply_markup=keyboard)

        current_exercise_right_answer = db_object.execute(
            f"SELECT right_answer FROM questions WHERE question_id = {result[0]}")
        right_answer_object = db_object.fetchone()

        if message.text == right_answer_object[0]:
            current_right_answers_number = result[1] + 1
            db_object.execute(f"UPDATE users SET right_answers_number = %s WHERE id = {id}",
                              (current_right_answers_number,))
            db_connection.commit();

        db_connection.commit()





















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
