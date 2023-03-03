# Импортирование модулей:
import requests

import VKLong.VKLong.object
from config import ACCEPTED_SEX, BOT_TOKEN
from db.database import *
from utils.keyboards import kbd_choice_sex, kbd_search
from VKLong.VKLong import Bot

# Авторизация:
user_token = input("Введите user-token, который будет использоваться для поиска людей: ")

bot = Bot(token=BOT_TOKEN)


def get_city_by_name(city_name: str) -> tuple:
    """
    Возвращает название и айди города по его названию в кортеже
    :param city_name: Название города
    """
    response = requests.get(
        "https://api.vk.com/method/database.getCities",
        params={
            "q": city_name,
            "count": 1,
            "access_token": user_token,
            "v": 5.131,
        },
    ).json()['response']

    if response['count'] > 0:
        return (response['items'][0]['title'], response['items'][0]['id'])


def get_city_by_id(city_id: int) -> tuple:
    """
    Возвращает название и айди города по его айди в кортеже
    :param city_id: Айди города
    """
    response = requests.get(
        "https://api.vk.com/method/database.getCitiesById",
        params={
            "city_ids": city_id,
            "access_token": user_token,
            "v": 5.131,
        },
    ).json()['response']

    return (response[0]['title'], response[0]['id'])


def search_user(user_id: int) -> dict:
    """
    Ищет пользователя, учитывая его настройки
    :param user_id: Айди пользователя, который ищет другого человека
    """
    preferred_sex = get_user(user_id, "preferred_sex")
    if preferred_sex == "female":
        preferred_sex = 1
    elif preferred_sex == "male":
        preferred_sex = 2

    age_from = int(get_user(user_id, 'preferred_age_from'))
    age_to = int(get_user(user_id, 'preferred_age_to'))
    offset = int(get_user(user_id, 'search_offset'))
    city = int(get_user(user_id, 'city'))

    response = requests.get(
        "https://api.vk.com/method/users.search",
        params={
            "offset": offset,
            "city": city,
            "sex": preferred_sex,
            "status": (1, 6),
            "age_from": age_from,
            "age_to": age_to,
            "access_token": user_token,
            "v": 5.131,
        },
    ).json()["response"]["items"][0]

    cur.execute(
        f"UPDATE main SET search_offset = search_offset + 1 WHERE user_id = {user_id}"
    )

    return response


def get_all_user_photos(user_id: int) -> dict:
    """
    Возвращает все фотографии указанного пользователя
    :param user_id: Пользователь, у которого надо найти все фотографии
    """
    response = requests.get(
        "https://api.vk.com/method/photos.getAll",
        params={
            "owner_id": user_id,
            "extended": 1,
            "count": 100,
            "skip_hidden": 1,
            "access_token": user_token,
            "v": 5.131,
        },
    ).json()["response"]

    return response


# Получение обновлений:
@bot.get_updates
def on_update(event):
    # Если новое событие НЕ является сообщением:
    if event.type != "message_new":
        return

    message = VKLong.VKLong.object.message_new(event.response)
    user_id: int = message.from_id
    # Если сообщение НЕ из личных сообщений:
    if message.from_id > 2000000000:
        return

    text: str = message.text.lower()

    is_exists = is_user_exists(user_id)
    registration_stage = get_registration_stage(user_id)

    # Если пользователь не зарегистрирован и не указал нужные данные:
    if not is_exists:
        user_info: dict = bot.execute_api("users.get", {"user_id": user_id, "fields": "sex,city"})[0]
        username = user_info["first_name"]
        sex = user_info["sex"]
        city = user_info.get("city")
        if city is not None:
            city = city["id"]
        else:
            city = "NULL"

        # 0 - не указан, 1 - женский, 2 - мужской
        if sex == 0:
            sex = "NULL"
        elif sex == 1:
            sex = "female"
        elif sex == 2:
            sex = "male"

        register_user(user_id, username, sex, city)

        if sex != "NULL":
            # Бот определил пол, потому что он есть в профиле
            set_registration_stage(user_id, "choice_preferred_sex")
            bot.answer(
                "👋 Привет! Добро пожаловать в VKinder!\n"
                "\n"
                "👉 Выбери предпочитаемый пол, с которым хочешь познакомиться:",
                kbd_choice_sex,
            )
        else:
            # Бот не определил пол, потому что он скрыт в профиле
            set_registration_stage(user_id, "choice_sex")
            bot.answer(
                "👋 Привет! Добро пожаловать в VKinder!\n"
                "\n"
                "👉 Выбери свой пол на клавиатуре:",
                kbd_choice_sex,
            )
        commit_db()

    # Регистрация пользователя:
    elif is_exists and registration_stage != 'finished':
        # Выбор своего пола пользователем:
        if registration_stage == "choice_sex":
            if text in ACCEPTED_SEX:
                if text == "мужской":
                    update_user(user_id, "sex", "male")
                elif text == "женский":
                    update_user(user_id, "sex", "female")

                set_registration_stage(user_id, "choice_preferred_sex")
                bot.answer(
                    "👍 Отлично! С твоим полом определились.\n"
                    "\n"
                    "👉 Выбери предпочитаемый пол, с которым хочешь познакомиться: ",
                    kbd_choice_sex,
                )
                commit_db()
            else:
                bot.answer(
                    "🤚 Упс! Вы выбрали недопустимый пол!\n"
                    "\n"
                    "👉 Выбери доступный пол на клавиатуре:",
                    kbd_choice_sex,
                )

        # Выбор предпочитаемого пола:
        elif registration_stage == "choice_preferred_sex":
            if text in ACCEPTED_SEX:
                set_registration_stage(user_id, 'choice_preferred_age')
                if text == "мужской":
                    update_user(user_id, 'preferred_sex', 'male')
                elif text == "женский":
                    update_user(user_id, 'preferred_sex', 'female')
                bot.answer(
                    "👍 Отлично! С преподчитаемым полом определились!\n"
                    "\n"
                    "👉 Теперь укажи диапазон возраста собеседника:\n"
                    "(например, отправь сообщение: 20-25)"
                )
                commit_db()
            else:
                bot.answer(
                    "🤚 Упс! Вы выбрали недопустимый предпочитаемый пол!\n"
                    "\n"
                    "👉 Выбери доступный пол на клавиатуре:",
                    kbd_choice_sex,
                )

        # Указание диапазона поиска по возрасту:
        elif registration_stage == "choice_preferred_age":
            try:
                minimal_age = int(text.split("-")[0])
                maximum_age = int(text.split("-")[1])
            except IndexError:
                bot.answer(
                    "🤚 Упс! Ты неправильно указал(а) диапазон возраста!\n"
                    "\n"
                    "👉 Отправь сообщение вида 20-25, чтобы указать возраст поиска:"
                )
                return

            if minimal_age > maximum_age:
                minimal_age, maximum_age = maximum_age, minimal_age

            if minimal_age < 18 or minimal_age > 99:
                bot.answer(
                    "🤚 Упс! Диапазон поиска должен быть не менее 18-ти и не более 99-ти лет!\n"
                    "\n"
                    "👉 Отправь сообщение вида 20-25, чтобы указать возраст поиска:"
                )
                return

            try:
                update_user(user_id, "preferred_age_from", minimal_age)
                update_user(user_id, "preferred_age_to", maximum_age)
            except ValueError:
                bot.answer(
                    "🤚 Упс! Диапазон поиска должен являться целым числом!\n"
                    "\n"
                    "👉 Отправь сообщение вида 20-25, чтобы указать возраст поиска:"
                )
                return

            city = get_user(user_id, "city")
            if city == "NULL":
                set_registration_stage(user_id, "choice_preferred_city")
                bot.answer(
                    "👍 Отлично, вы выбрали возраст собеседника!\n"
                    "\n"
                    "👉 Теперь укажи свой город:"
                )
            else:
                set_registration_stage(user_id, "finished")
                bot.answer(
                    "🥳 Отлично! Теперь ты можешь воспользоваться VKinder!\n"
                    "\n"
                    '👉 Используй команду - "поиск", чтобы найти подходящего человека!',
                    kbd_search,
                )

            commit_db()

        elif registration_stage == "choice_preferred_city":
            if len(text) > 30:
                bot.answer(
                    "🤚 Упс! Название города слишком длинное!\n"
                    "\n"
                    "👉 Название города должно быть меньше 30 символов, попробуйте ещё раз:"
                )
                return

            city = get_city_by_name(text)

            update_user(user_id, "city", city[1])
            commit_db()
            bot.answer(
                f"🥳 Отлично, вы выбрали город {city[1]}! Теперь ты "
                "можешь воспользоваться VKinder!\n"
                "\n"
                '👉 Используй команду - "поиск", чтобы найти подходящего человека!',
                kbd_search,
            )

    # Если пользователь зарегистрирован:
    elif is_exists and registration_stage == "finished":
        if text != "поиск" and text != "🔎 поиск":
            return

        while True:
            # Поиск нового пользователя
            finded_user_object = search_user(user_id)
            commit_db()

            is_profile_closed = finded_user_object["is_closed"]
            if is_profile_closed:
                return

            photos_object = get_all_user_photos(finded_user_object["id"])

            if photos_object["count"] < 3:
                pass

            # Отправка фотографий и ссылки на пользователей:
            else:
                photo_dict = {}
                if photos_object["count"] > 100:
                    photos_object["count"] = 100
                for i in range(photos_object["count"]):
                    try:
                        photo_likes = photos_object["items"][i]["likes"]["count"]
                        photo_dict[
                            photo_likes
                        ] = f"photo{finded_user_object['id']}_{photos_object['items'][i]['id']}"
                    except:
                        break

                if photo_dict != {}:
                    attachment_list = ""

                    for _ in range(3):
                        attachment_list += f"{photo_dict[max(photo_dict)]},"
                        photo_dict.pop(max(photo_dict))

                    finded_user_id = finded_user_object['id']
                    first_name = finded_user_object['first_name']
                    last_name = finded_user_object['last_name']
                    finded_link = f"vk.com/id{finded_user_id}"

                    bot.answer(
                        "👍 Найден подходящий профиль!\n"
                        "\n"
                        f"🏵 [id{finded_user_id}|{first_name} {last_name}]\n"
                        f"Ссылка: {finded_link}",
                        attachment=str(attachment_list),
                    )
                    break
