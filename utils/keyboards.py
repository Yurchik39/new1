from VKLong.VKLong import KeyboardGenerator, KeyboardColor

# Выбор пола:
kbd_choice_sex = KeyboardGenerator(one_time=True)
kbd_choice_sex.add_text_button("Мужской", color=KeyboardColor.BLUE)
kbd_choice_sex.add_text_button("Женский", color=KeyboardColor.BLUE)
kbd_choice_sex = kbd_choice_sex.get_keyboard_json()

# Кнопка поиска:
kbd_search = KeyboardGenerator(one_time=False)
kbd_search.add_text_button("🔎 Поиск", color=KeyboardColor.GREEN)
kbd_search = kbd_search.get_keyboard_json()
