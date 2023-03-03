import sqlite3

users_db = sqlite3.connect('db/users.db')
cur = users_db.cursor()

# Создание необходимых таблиц
cur.execute("""CREATE TABLE IF NOT EXISTS main
(
    user_id BIGINT,
    first_name TEXT,
    sex TEXT,
    city TEXT,
    preferred_sex TEXT,
    preferred_age_from INTEGER,
    preferred_age_to INTEGER,
    search_offset BIGINT,
    registration_stage TEXT

)""")
cur.execute("""CREATE TABLE IF NOT EXISTS viewed_profiles
(
    user_id BIGINT,
    viewed_profile_id BIGINT
)""")


def is_user_exists(user_id: int) -> bool:
    """
    Проверка на существование айди пользователя в БД
    :param user_id: Айди пользователя, которого надо проверить
    """
    result = cur.execute(
        f"SELECT user_id FROM main WHERE user_id={user_id}"
    ).fetchone()
    if result is not None:
        return True
    return False


def register_user(user_id: int, username: str, sex: str, city):
    """
    Регистрация пользователя в БД
    :param user_id: Айди пользователя, которого надо зарегестрировать
    :param username: Имя пользователя
    :param sex: Пол пользователя
    :param city: Город пользователя
    """
    cur.execute(
        "INSERT INTO main(user_id, first_name, sex, city, preferred_sex,"
        " preferred_age_from, preferred_age_to, search_offset, registration_stage)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, username, sex, city, "NULL", "NULL", "NULL", 0, "choice_sex"),
    )


def get_registration_stage(user_id: int) -> str:
    """
    Возвращает текущий этап регистрации пользователя
    :param user_id: Айди пользователя, у которого надо узнать текущий этап
    """
    result = cur.execute(
        f"SELECT registration_stage FROM main WHERE user_id={user_id}"
    ).fetchone()
    if result is not None:
        return result[0]
    return result


def set_registration_stage(user_id: int, stage: str):
    """
    Устанавливает этап регистрации пользователя
    :param user_id: Айди пользователя, у которого надо установить этап
    """
    cur.execute(
        f"UPDATE main SET registration_stage = '{stage}' "
        f"WHERE user_id = {user_id}"
    )


def get_user(user_id: int, column: str) -> str:
    """
    Возвращает определенный столбец пользователя из БД
    :param user_id: Айди пользователя из БД
    :param column: Название столбца
    """
    result = cur.execute(
        f"SELECT {column} FROM main WHERE user_id = {user_id}"
    ).fetchone()[0]
    return result


def update_user(user_id: int, column: str, value: str):
    """
    Устанавливает значение для определененого столбца у пользователя из БД
    :param user_id: Айди пользователя из БД
    :param column: Название столбца
    :param value: Новое значение для этого столбца
    """
    cur.execute(
        f"UPDATE main SET {column} = ? WHERE user_id = ?",
        (value, user_id)
    )


def commit_db():
    """
    Сохраняет базу данных
    """
    users_db.commit()
