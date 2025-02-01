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
        bot.send_message(chat_id, f"❌ Ошибка при проверке данных: {e}")


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
        bot.send_message(chat_id, f"❌ Ошибка при добавлении преподавателя: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "student_button")
def handle_student(call):
    """Обработчик кнопки 'Студент'."""
    chat_id = call.message.chat.id

    try:
        with SqlConnection() as (conn, cursor):
            # Проверяем, не записан ли уже пользователь как студент
            cursor.execute(SELECT_STUDENT_BY_CHAT_ID, (chat_id,))
            existing_student = cursor.fetchone()

            if existing_student:
                bot.send_message(chat_id, "Вы уже зарегистрированы как студент! ✅\nИспользуйте /menu для открытия меню.")
            else:
                # Если не зарегистрирован, просим ввести номер зачётки
                msg = bot.send_message(chat_id, "Введите ваш номер зачётки:")
                bot.register_next_step_handler(msg, request_student_number)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при проверке студента: {e}")

def request_student_number(message):
    """Запрашиваем у студента номер зачётки и сохраняем в БД."""
    chat_id = message.chat.id
    student_number = message.text.strip()

    # Проверяем, что введённый номер состоит только из цифр
    if not student_number.isdigit():
        msg = bot.send_message(chat_id, "❌ Номер зачётки должен содержать только цифры. Попробуйте еще раз:")
        bot.register_next_step_handler(msg, request_student_number)
        return

    user_data[chat_id] = student_number

    try:
        with SqlConnection() as (conn, cursor):
            # Заполняем базовыми данными (при необходимости спросите ФИО, группу и т.д.)
            cursor.execute(
                INSERT_STUDENT,
                (chat_id, student_number, 'Фамилия', 'Имя', 'Отчество', 'Группа', 0)
            )
            conn.commit()
            bot.send_message(chat_id, f"✅ Данные сохранены! Ваш номер зачётки: {student_number}\nТеперь вы можете открыть меню командой /menu.")

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при добавлении студента: {e}")

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
    bot.send_message(message.chat.id, "Это сообщение помощи. Здесь вы можете дать подсказки пользователям.")


@bot.message_handler(commands=['meow'])
def send_meow(message):
    """Пример дополнительной команды."""
    bot.send_message(message.chat.id, "meow")


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

    bot.send_message(chat_id, "Чат почищен!", disable_notification=True)

# Запуск бота
bot.infinity_polling()
