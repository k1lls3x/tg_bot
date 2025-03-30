from sql_logic.connect_to_sql import SqlConnection
from sql_logic.queries import INSERT_STUDENT, INSERT_APPLICATION
import telebot

# Словарь для хранения промежуточных данных пользователя
user_data = {}

def start_registration(message, bot):
    """
    Начало регистрации: запрашиваем ФИО.
    """
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "Введите ваше ФИО (например: Иванов Иван Иванович):")
    bot.register_next_step_handler(msg, lambda m: request_full_name(m, bot))

def request_full_name(message, bot):
    """
    Запрашиваем ФИО, парсим его и переходим к вводу группы.
    """
    chat_id = message.chat.id
    full_name = message.text.strip()

    if not full_name:
        msg = bot.send_message(chat_id, "❌ ФИО не может быть пустым. Введите ещё раз:")
        bot.register_next_step_handler(msg, lambda m: request_full_name(m, bot))
        return

    try:
        last_name, first_name, middle_name = parse_full_name(full_name)
    except ValueError as e:
        msg = bot.send_message(chat_id, str(e))
        bot.register_next_step_handler(msg, lambda m: request_full_name(m, bot))
        return

    user_data[chat_id] = {
        "last_name": last_name,
        "first_name": first_name,
        "middle_name": middle_name
    }

    msg = bot.send_message(chat_id, "Введите вашу группу(В формате СИС-32):")
    bot.register_next_step_handler(msg, lambda m: request_group(m, bot))

def request_group(message, bot):
    """
    Сохраняем группу и спрашиваем, является ли студент старостой.
    """
    chat_id = message.chat.id
    group = message.text.strip()

    if not group:
        msg = bot.send_message(chat_id, "❌ Группа не может быть пустой. Введите ещё раз:")
        bot.register_next_step_handler(msg, lambda m: request_group(m, bot))
        return

    user_data[chat_id]["group"] = group

    # Формируем клавиатуру с вариантами ответа
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("Да", "Нет")
    msg = bot.send_message(chat_id, "Являетесь ли вы старостой?", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: request_leader_status(m, bot))

def request_leader_status(message, bot):
    """
    Обрабатываем выбор: если студент выбирает «Да» — отправляем заявку
    и регистрируем его как старосту (запись добавляется в таблицу applications и students),
    если «Нет» — регистрируем его как обычного студента (только в students).
    """
    chat_id = message.chat.id
    answer = message.text.strip().lower()

    if answer not in ["да", "нет"]:
        msg = bot.send_message(chat_id, "❌ Пожалуйста, выберите «Да» или «Нет».")
        bot.register_next_step_handler(msg, lambda m: request_leader_status(m, bot))
        return

    try:
        with SqlConnection() as (conn, cursor):
            # Проверяем, существует ли указанная группа в таблице groups
            group = user_data[chat_id]["group"]
            cursor.execute("SELECT GroupName FROM groups WHERE GroupName = %s", (group,))
            existing_group = cursor.fetchone()
            if not existing_group:
                bot.send_message(chat_id, f"❌ Группа {group} не найдена. Проверьте корректность ввода.")
                return

            # Если пользователь выбрал регистрацию как староста, выполняем два запроса:
            if answer == "да":
                # Добавляем заявку на старосту в таблицу applications
                cursor.execute(
                    INSERT_APPLICATION,
                    (
                        chat_id,
                        user_data[chat_id]["last_name"],
                        user_data[chat_id]["first_name"],
                        user_data[chat_id]["middle_name"],
                        "Староста"
                    )
                )
                # Регистрируем старосту в таблице students
                cursor.execute(
                    INSERT_STUDENT,
                    (
                        chat_id,
                        user_data[chat_id]["last_name"],
                        user_data[chat_id]["first_name"],
                        user_data[chat_id]["middle_name"],
                        group
                    )
                )
                conn.commit()
                bot.send_message(chat_id, "✅ Вы зарегистрированы как староста. Ваша заявка отправлена на рассмотрение, а данные сохранены.")
            else:
                # Если студент регистрируется как обычный студент — просто вставляем данные в таблицу students
                cursor.execute(
                    INSERT_STUDENT,
                    (
                        chat_id,
                        user_data[chat_id]["last_name"],
                        user_data[chat_id]["first_name"],
                        user_data[chat_id]["middle_name"],
                        group
                    )
                )
                conn.commit()
                bot.send_message(
                    chat_id,
                    f"✅ Регистрация завершена!\n"
                    f"👤 ФИО: {user_data[chat_id]['last_name']} {user_data[chat_id]['first_name']} {user_data[chat_id]['middle_name']}\n"
                    f"🎓 Группа: {group}"
                )
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при регистрации: {e}")
    finally:
        if chat_id in user_data:
            del user_data[chat_id]



def parse_full_name(full_name):
    """
    Парсит строку ФИО в фамилию, имя и отчество.
    Если отчество не указано, возвращает пустую строку.
    """
    words = full_name.split()

    if len(words) == 2:
        last_name, first_name = words
        middle_name = ""
    elif len(words) == 3:
        last_name, first_name, middle_name = words
    else:
        raise ValueError("❌ Некорректный формат ФИО. Введите Фамилию, Имя и (при наличии) Отчество.")

    return last_name, first_name, middle_name
