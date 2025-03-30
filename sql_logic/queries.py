# queries.py

# Запрос для получения роли пользователя (студент или преподаватель)
GET_USER_ROLE = """
    SELECT 'student' AS role FROM students WHERE chat_id = %s
    UNION
    SELECT 'teacher' AS role FROM teachers WHERE chat_id = %s
"""

# Запрос для проверки существования преподавателя
SELECT_TEACHER_BY_CHAT_ID = "SELECT * FROM teachers WHERE chat_id = %s"
INSERT_STUDENT = """
INSERT INTO students (chat_id, Surname, Name, Patronymic, GroupName, IsLeader)
VALUES (%s, %s, %s, %s, %s, 0)
"""
# Запрос для регистрации нового преподавателя
INSERT_TEACHER = """
    INSERT INTO teachers (chat_id, surname, name, patronymic, is_verified)
    VALUES (%s, %s, %s, %s, %s)
"""
# Запрос для проверки существования студента
SELECT_STUDENT_BY_CHAT_ID = "SELECT * FROM students WHERE chat_id = %s"

# Запрос для регистрации нового студента
INSERT_STUDENT = """
INSERT INTO students (chat_id, Surname, Name, Patronymic, GroupName, IsLeader)
VALUES (%s, %s, %s, %s, %s, 0)
"""

INSERT_APPLICATION = """
INSERT INTO applications (chat_id, Surname, Name, Patronymic, Position)
VALUES (%s, %s, %s, %s, %s)
"""
