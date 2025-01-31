import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from functional_student_code.student_menu import TelegramBot  # Импорт студенческого меню
from connect_to_sql import SqlConnection
from telebot.types import ForceReply
import shutil

TOKEN = "8056279378:AAGX8tILI43XHYhJrQC3JF3xUFUoyPCr9vY"

bot = telebot.TeleBot(TOKEN)
user_data = {}
user_roles = {}  # Словарь для хранения ролей пользователей
#SqlConnection.get_connection()
conn, cursor = SqlConnection.get_connection()
if conn and cursor:
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    print("📂 Таблицы в базе данных:", [table[0] for table in tables])
    SqlConnection.close_connection(conn, cursor)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start"""
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Преподаватель", callback_data="teacher_button"),
        InlineKeyboardButton("Студент", callback_data="student_button")
    )
    
    bot.set_my_commands([
        BotCommand("start", "Перезапуск"),
        BotCommand("menu", "Открыть меню"),
        BotCommand("help", "Помощь"),
        BotCommand("meow", "Сказать meow"),
        BotCommand("test_zapros", "теСТ"),
        BotCommand("clear", "Очистить чат")
        
    ])
    
    bot.send_message(
        message.chat.id,
        "Привет! Давайте вас зарегистрируем:",
        reply_markup=markup
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "Вам никто не поможет.")

@bot.message_handler(commands=['test_zapros'])
def request_student_number(message):
    """Запрос номера зачётки у пользователя"""
    msg = bot.send_message(message.chat.id, "Введите ваш номер зачётки:", reply_markup=ForceReply(selective=True))
    bot.register_next_step_handler(msg, insert_student_number)

def insert_student_number(message):
    """Получает номер зачётки от пользователя и выполняет SQL-запрос"""
    student_number = message.text.strip()  # Получаем введённое пользователем значение
    user_data[message.chat.id] = student_number  # Сохраняем его в словаре

    conn, cursor = SqlConnection.get_connection()

    if conn and cursor:
        try:
            cursor.execute("""
                INSERT INTO students (chat_id, student_number, surname, name, patronymic, `group`, is_headman) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (message.chat.id, student_number, 'Ятманов', 'Николай', 'Александрович', 'СИС-32', 0))

            conn.commit()  # Фиксируем изменения
            bot.send_message(message.chat.id, f"✅ Данные добавлены! Номер зачётки: {student_number}")

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка при добавлении данных: {e}")

        finally:
            SqlConnection.close_connection(conn, cursor)
    else:
        bot.send_message(message.chat.id, "❌ Ошибка подключения к базе данных.")

@bot.message_handler(commands=['meow'])
def send_meow(message):
    bot.send_message(message.chat.id, "meow")

@bot.callback_query_handler(func=lambda call: call.data == "teacher_button")
def handle_teacher(call):
    """Обработчик кнопки 'Преподаватель'"""
    delete_previous_message(call.message.chat.id, call.message.message_id)
    user_roles[call.message.chat.id] = "teacher"
    # bot.send_message(call.message.chat.id, "Вы зарегистрированы как преподаватель. Используйте /menu, чтобы открыть меню.")

@bot.callback_query_handler(func=lambda call: call.data == "student_button")
def handle_student(call):
    """Обработчик кнопки 'Студент'"""
    delete_previous_message(call.message.chat.id, call.message.message_id)
    user_roles[call.message.chat.id] = "student"
  #  bot.send_message(call.message.chat.id, "Вы зарегистрированы как студент. Используйте /menu, чтобы открыть меню.")
    bot_instance = TelegramBot(bot)

    bot_instance.send_menu(call.message.chat.id)

@bot.message_handler(commands=['clear'])
def clear_chat(message):
    """Удаляет все сообщения, отправленные ботом"""
    chat_id = message.chat.id
    message_id = message.message_id

    for i in range(200):  # Попытка удалить последние 200 сообщений
        try:
            bot.delete_message(chat_id, message_id - i)
        except telebot.apihelper.ApiException as e:
            if "message to delete not found" in str(e):
                continue  # Если сообщение не найдено, пропускаем
            print(f"Ошибка при удалении сообщения {message_id - i}: {e}")

    bot.send_message(chat_id, "Чат очищен!", disable_notification=True)


@bot.message_handler(commands=['menu'])
def open_menu(message):
    """Открывает меню в зависимости от роли пользователя"""
    role = user_roles.get(message.chat.id, None)
    
    if role == "teacher":
        bot.send_message(message.chat.id, "Coming soon...")
    elif role == "student":
        bot_instance = TelegramBot(bot)
        bot_instance.send_menu(message.chat.id)
    else:
        bot.send_message(message.chat.id, "Сначала пройдите регистрацию с помощью /start!")

def delete_previous_message(chat_id, message_id):
    """Удаление предыдущего сообщения"""
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

bot.infinity_polling()
