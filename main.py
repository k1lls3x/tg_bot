import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from functional_student_code.student_menu import TelegramBot  
from sql_logic.connect_to_sql import SqlConnection
from functional_student_code.student_registration import request_student_number, request_full_name, request_group
from logs.log_settings import Logs  # Импортируем кастомный логгер

# Импортируем SQL-запросы
from sql_logic.queries import (
    GET_USER_ROLE,
    SELECT_TEACHER_BY_CHAT_ID,
    INSERT_TEACHER,
    SELECT_STUDENT_BY_CHAT_ID,
    INSERT_STUDENT
)

TOKEN = "8056279378:AAGX8tILI43XHYhJrQC3JF3xUFUoyPCr9vY"
bot = telebot.TeleBot(TOKEN)
log = Logs()  # Создаём объект логирования

user_data = {}
bot_last_message = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start — проверка роли пользователя и/или регистрация."""
    chat_id = message.chat.id
  
     
    bot.set_my_commands([
        BotCommand("start", "Перезапуск бота"),
        BotCommand("menu", "Открыть меню"),
        BotCommand("help", "Помощь"),
        BotCommand("meow", "Сказать meow"),
        BotCommand("clear", "Очистить чат"),
        ])
    
    
   
    

    # if message.chat.id == 1164837622:
    #     bot.send_message(chat_id, "Чипман")
    #     return
    try:
        with SqlConnection() as (conn, cursor):
            cursor.execute(GET_USER_ROLE, (chat_id, chat_id))
            result = cursor.fetchone()

            if result:
                role = result[0]
                if role == 'student':
                    markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.row(KeyboardButton("🏠 Главное меню"))
                    bot.send_message(chat_id, "Вы уже зарегистрированы как студент! ✅\nИспользуйте /menu для открытия меню.", reply_markup=markup)
                else:
                    bot.send_message(chat_id, "Вы уже зарегистрированы как преподаватель! ✅")
            else:
                markup = InlineKeyboardMarkup()
                markup.add(
                    InlineKeyboardButton("Преподаватель", callback_data="teacher_button"),
                    InlineKeyboardButton("Студент", callback_data="student_button")
                )
                bot.send_message(chat_id, "Добро пожаловать! Выберите вашу роль:", reply_markup=markup)

    except Exception as e:
        bot.send_message(chat_id, "❌ Произошла ошибка. Попробуйте позднее")
        log.error(f"❌ Ошибка проверки данных в чате - {chat_id}. Код ошибки: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "teacher_button")
def handle_teacher(call):
    chat_id = call.message.chat.id

    try:
        with SqlConnection() as (conn, cursor):
            cursor.execute(SELECT_TEACHER_BY_CHAT_ID, (chat_id,))
            existing_teacher = cursor.fetchone()

            if existing_teacher:
                bot.send_message(chat_id, "Вы уже зарегистрированы как преподаватель! ✅")
            else:
                cursor.execute(INSERT_TEACHER, (chat_id, "Фамилия", "Имя", "Отчество", 0))
                conn.commit()
                bot.send_message(chat_id, "✅ Вы успешно зарегистрированы как преподаватель!")
    except Exception as e:
        bot.send_message(chat_id, "❌ Произошла ошибка. Попробуйте позднее")
        log.error(f"Ошибка регистрации преподавателя (Chat ID: {chat_id}): {e}")

@bot.callback_query_handler(func=lambda call: call.data == "student_button")
def handle_student(call):
    chat_id = call.message.chat.id
    try:
        with SqlConnection() as (conn, cursor):
            cursor.execute(SELECT_STUDENT_BY_CHAT_ID, (chat_id,))
            existing_student = cursor.fetchone()

            if existing_student:
                bot.send_message(chat_id, "Вы уже зарегистрированы как студент! ✅\nИспользуйте /menu для открытия меню.")
            else:
                msg = bot.send_message(chat_id, "Введите ваш номер зачётки:")
                bot.register_next_step_handler(msg, lambda m: request_student_number(m, bot))
    except Exception as e:
        log.error(f"Ошибка регистрации студента (Chat ID: {chat_id}): {e}")

@bot.message_handler(func=lambda message: message.text == "🏠 Главное меню")
def handle_main_menu(message):
    chat_id = message.chat.id
    user_message_id = message.message_id

    delete_previous_message(chat_id, user_message_id)

    if chat_id in bot_last_message:
        try:
            delete_previous_message(chat_id, bot_last_message[chat_id])
        except Exception as e:
            log.error(f"Ошибка удаления последнего сообщения бота (Chat ID: {chat_id}): {e}")

    try:
        with SqlConnection() as (conn, cursor):
            cursor.execute(GET_USER_ROLE, (chat_id, chat_id))
            result = cursor.fetchone()

            if result:
                role = result[0]
                if role == "student":
                    telegram_bot = TelegramBot(bot)
                    new_message = telegram_bot.send_menu(chat_id)
                    if new_message:
                        bot_last_message[chat_id] = new_message.message_id
                    else:
                        log.error("❌ Ошибка: send_menu() не вернул сообщение!")
                elif role == "teacher":
                    bot.send_message(chat_id, "Coming soon...")
            else:
                delete_previous_message(chat_id, bot_last_message[chat_id])
                bot.send_message(chat_id, "Сначала пройдите регистрацию командой /start.")
    except Exception as e:
        log.error(f"Ошибка обработки главного меню (Chat ID: {chat_id}): {e}")

def delete_previous_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        log.error(f"Ошибка при удалении сообщения {message_id} (Chat ID: {chat_id}): {e}")

@bot.message_handler(commands=['menu'])
def open_menu(message):
    chat_id = message.chat.id
    user_message_id = message.message_id

    delete_previous_message(chat_id, user_message_id)

    if chat_id in bot_last_message:
        try:
            delete_previous_message(chat_id, bot_last_message[chat_id])
        except Exception as e:
            log.error(f"Ошибка удаления последнего сообщения бота (Chat ID: {chat_id}): {e}")

    try:
        with SqlConnection() as (conn, cursor):
            cursor.execute(GET_USER_ROLE, (chat_id, chat_id))
            result = cursor.fetchone()

            if result:
                role = result[0]
                if role == "student":
                    telegram_bot = TelegramBot(bot)
                    new_message = telegram_bot.send_menu(chat_id)
                    if new_message:
                        bot_last_message[chat_id] = new_message.message_id
                    else:
                        log.error("❌ Ошибка: send_menu() не вернул сообщение!")
                elif role == "teacher":
                    bot.send_message(chat_id, "Coming soon...")
            else:
                delete_previous_message(chat_id, bot_last_message[chat_id])
                bot.send_message(chat_id, "Сначала пройдите регистрацию командой /start.")
    except Exception as e:
        log.error(f"Ошибка открытия меню (Chat ID: {chat_id}): {e}")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "Вам никто не поможет")

@bot.message_handler(commands=['meow'])
def send_meow(message):
    bot.send_message(message.chat.id, "Ты еблан? Тг боты не мяукают.")


@bot.message_handler(commands=['clear'])
def clear_chat(message):
    chat_id = message.chat.id
    message_id = message.message_id

    for i in range(200):
        try:
            bot.delete_message(chat_id, message_id - i)
        except telebot.apihelper.ApiException as e:
            if "message to delete not found" in str(e):
                continue

    bot.send_message(chat_id, "Чат очищен!", disable_notification=True)

bot.infinity_polling()
