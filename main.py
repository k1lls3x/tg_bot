import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from functional_student_code.student_menu import TelegramBot  # Импорт студенческого меню
import shutil

TOKEN = "8056279378:AAGX8tILI43XHYhJrQC3JF3xUFUoyPCr9vY"

bot = telebot.TeleBot(TOKEN)

user_roles = {}  # Словарь для хранения ролей пользователей

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
        BotCommand("meow", "Сказать meow")
    ])
    
    bot.send_message(
        message.chat.id,
        "Привет! Давайте вас зарегистрируем:",
        reply_markup=markup
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "Вам никто не поможет.")

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
