# student_registration.py

from sql_logic.connect_to_sql import SqlConnection
from sql_logic.queries import INSERT_STUDENT
import telebot

# Если переменная user_data используется и нужна в модуле,
# можно либо объявить её здесь, либо передавать как аргумент в функции.
user_data = {}

def request_student_number(message, bot):
    """Запрашиваем номер зачётки и переходим к вводу ФИО."""
    chat_id = message.chat.id
    student_number = message.text.strip()

    if not student_number.isdigit():
        msg = bot.send_message(chat_id, "❌ Номер зачётки должен содержать только цифры. Попробуйте ещё раз:")
        bot.register_next_step_handler(msg, lambda m: request_student_number(m, bot))
        return

    user_data[chat_id] = {"student_number": student_number}
    
    msg = bot.send_message(chat_id, "Введите ваше ФИО одной строкой (например: Иванов Иван Иванович):")
    bot.register_next_step_handler(msg, lambda m: request_full_name(m, bot))

def request_full_name(message, bot):
    """Запрашиваем ФИО, парсим его и переходим к вводу группы."""
    chat_id = message.chat.id
    full_name = message.text.strip()

    if not full_name:
        msg = bot.send_message(chat_id, "❌ ФИО не может быть пустым. Введите ещё раз:")
        bot.register_next_step_handler(msg, lambda m: request_full_name(m, bot))
        return

    try:
        last_name, first_name, middle_name = parse_full_name(full_name)
        user_data[chat_id]["last_name"] = last_name
        user_data[chat_id]["first_name"] = first_name
        user_data[chat_id]["middle_name"] = middle_name
    except ValueError as e:
        msg = bot.send_message(chat_id, str(e))
        bot.register_next_step_handler(msg, lambda m: request_full_name(m, bot))
        return

    msg = bot.send_message(chat_id, "Введите вашу группу:")
    bot.register_next_step_handler(msg, lambda m: request_group(m, bot))

def request_group(message, bot):
    """Запрашиваем группу и записываем данные в БД."""
    chat_id = message.chat.id
    group = message.text.strip()

    if not group:
        msg = bot.send_message(chat_id, "❌ Группа не может быть пустой. Введите ещё раз:")
        bot.register_next_step_handler(msg, lambda m: request_group(m, bot))
        return

    user_data[chat_id]["group"] = group

    try:
        with SqlConnection() as (conn, cursor):
            cursor.execute(
                INSERT_STUDENT,
                (
                    chat_id,
                    user_data[chat_id]["student_number"],
                    user_data[chat_id]["last_name"],
                    user_data[chat_id]["first_name"],
                    user_data[chat_id]["middle_name"],
                    user_data[chat_id]["group"],
                    0  # или другой статус
                )
            )
            conn.commit()
            bot.send_message(
                chat_id, 
                f"✅ Данные сохранены! Ваши данные:\n"
                f"📌 Номер зачётки: {user_data[chat_id]['student_number']}\n"
                f"👤 Фамилия: {user_data[chat_id]['last_name']}\n"
                f"👤 Имя: {user_data[chat_id]['first_name']}\n"
                f"👤 Отчество: {user_data[chat_id]['middle_name']}\n"
                f"🎓 Группа: {user_data[chat_id]['group']}\n\n"
                f"Теперь вы можете открыть меню командой /menu."
            )
            del user_data[chat_id]
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при добавлении студента: {e}")

def parse_full_name(full_name):
    """Парсит строку ФИО в фамилию, имя и отчество."""
    words = full_name.split()

    if len(words) == 2:
        last_name, first_name = words
        middle_name = ""
    elif len(words) == 3:
        last_name, first_name, middle_name = words
    else:
        raise ValueError("❌ Некорректный формат ФИО. Введите Фамилию, Имя и (по желанию) Отчество.")

    return last_name, first_name, middle_name
