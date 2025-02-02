import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from functional_student_code.student_menu import TelegramBot  # Ваш модуль с меню для студента
from sql_logic.connect_to_sql import SqlConnection
from functional_student_code.student_registration import request_student_number, request_full_name, request_group

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

# Храним временно введенные данные от пользователя (например, номер зачётки)
user_data = {}
bot_last_message={}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start — проверка роли пользователя и/или регистрация."""
    chat_id = message.chat.id

    # Устанавливаем команды, которые будут видны в Telegram
    bot.set_my_commands([
        BotCommand("start", "Перезапуск бота"),
        BotCommand("menu", "Открыть меню"),
        BotCommand("help", "Помощь"),
        BotCommand("meow", "Сказать meow"),
        BotCommand("clear", "Очистить чат"),
    ])

    try:
        with SqlConnection() as (conn, cursor):
            # Проверяем, есть ли пользователь в таблице студентов или преподавателей
            cursor.execute(GET_USER_ROLE, (chat_id, chat_id))
            result = cursor.fetchone()

            if result:
                # Пользователь уже есть в БД
                role = result[0]
                if role == 'student':
                    markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.row(KeyboardButton("🏠 Главное меню"))

                    bot.send_message(chat_id, "Вы уже зарегистрированы как студент! ✅\nИспользуйте /menu для открытия меню.", reply_markup=markup)
                else:
                    bot.send_message(chat_id, "Вы уже зарегистрированы как преподаватель! ✅")
            else:
                # Пользователь не найден в БД — предлагаем выбрать роль
                markup = InlineKeyboardMarkup()
                markup.add(
                    InlineKeyboardButton("Преподаватель", callback_data="teacher_button"),
                    InlineKeyboardButton("Студент", callback_data="student_button")
                )
                bot.send_message(chat_id, "Добро пожаловать! Выберите вашу роль:", reply_markup=markup)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при проверке данных.")


@bot.callback_query_handler(func=lambda call: call.data == "teacher_button")
def handle_teacher(call):
    """Обработчик кнопки 'Преподаватель'."""
    chat_id = call.message.chat.id

    try:
        with SqlConnection() as (conn, cursor):
            # Проверяем, не записан ли уже пользователь как преподаватель
            cursor.execute(SELECT_TEACHER_BY_CHAT_ID, (chat_id,))
            existing_teacher = cursor.fetchone()

            if existing_teacher:
                bot.send_message(chat_id, "Вы уже зарегистрированы как преподаватель! ✅")
            else:
                # Регистрируем нового преподавателя (данные пока примерные)
                cursor.execute(INSERT_TEACHER, (chat_id, "Фамилия", "Имя", "Отчество", 0))
                conn.commit()
                bot.send_message(chat_id, "✅ Вы успешно зарегистрированы как преподаватель!")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Произошла ошибка. Попробуйте позднее")


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
                # Передаём bot как аргумент в функцию
                bot.register_next_step_handler(msg, lambda m: request_student_number(m, bot))
    except Exception as e:
        bot.send_message(chat_id, f"❌ Произошла ошибка. Попробуйте позднее")

@bot.message_handler(func=lambda message: message.text == "🏠 Главное меню")
def handle_main_menu(message):
    chat_id = message.chat.id
    user_message_id = message.message_id  # ID сообщения пользователя

    # Удаляем сообщение пользователя ("🏠 Главное меню")
    delete_previous_message(chat_id, user_message_id)

    # Удаляем предыдущее меню, если оно было
    if chat_id in bot_last_message:
        try:
            delete_previous_message(chat_id, bot_last_message[chat_id])
        except Exception as e:
            print(f"Ошибка удаления последнего сообщения бота: {e}")
    try:
        with SqlConnection() as (conn, cursor):
            # Проверяем роль из БД
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
                        print("❌ Ошибка: send_menu() не вернул сообщение!")
                elif role == "teacher":
                    bot.send_message(chat_id, "Меню для преподавателя в разработке...")
            else:
                delete_previous_message(chat_id,bot_last_message[chat_id])
                bot.send_message(chat_id, "Сначала пройдите регистрацию командой /start.")
    except Exception as e:
        bot.send_message(chat_id, "Сначала пройдите регистрацию командой /start.")

def delete_previous_message(chat_id, message_id):
    """Функция удаления сообщения."""
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения {message_id}: {e}")

@bot.message_handler(commands=['menu'])
def open_menu(message):
    """Открывает меню в зависимости от роли пользователя (по данным БД)."""
    chat_id = message.chat.id
    user_message_id = message.message_id  # ID сообщения пользователя

    # Удаляем сообщение пользователя ("🏠 Главное меню")
    delete_previous_message(chat_id, user_message_id)

    if chat_id in bot_last_message:
        try:
            delete_previous_message(chat_id, bot_last_message[chat_id])
        except Exception as e:
            print(f"Ошибка удаления последнего сообщения бота: {e}")
    try:
        with SqlConnection() as (conn, cursor):
            # Проверяем роль из БД
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
                        print("❌ Ошибка: send_menu() не вернул сообщение!")
                elif role == "teacher":
                    bot.send_message(chat_id, "Меню для преподавателя в разработке...")
            else:
                delete_previous_message(chat_id,bot_last_message[chat_id])

                bot.send_message(chat_id, "Сначала пройдите регистрацию командой /start.")
    except Exception as e:
        bot.send_message(chat_id, "Сначала пройдите регистрацию командой /start.")


@bot.message_handler(commands=['help'])
def send_help(message):
    """Простейшая команда помощи."""
    bot.send_message(message.chat.id, "Вам никто не поможет")


@bot.message_handler(commands=['meow'])
def send_meow(message):
    """Пример дополнительной команды."""
    bot.send_message(message.chat.id, "Ты еблан? Тг боты не мяукают.")


@bot.message_handler(commands=['clear'])
def clear_chat(message):
    """Удаляет последние ~200 сообщений, отправленные ботом, и выводит статус."""
    chat_id = message.chat.id
    message_id = message.message_id

    for i in range(200):
        try:
            bot.delete_message(chat_id, message_id - i)
        except telebot.apihelper.ApiException as e:
            # Если сообщение не найдено, пропускаем
            if "message to delete not found" in str(e):
                continue

    bot.send_message(chat_id, "Чат очищен!", disable_notification=True)

# Запуск бота
bot.infinity_polling()
