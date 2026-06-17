"""
Модуль валідації даних на сервері.

Кожна функція повертає None якщо все добре,
або текст помилки (рядок) якщо дані некоректні.

Серверна валідація важлива тому, що перевірку у браузері
(HTML required, pattern) користувач може обійти — наприклад,
надіславши запит напряму. Сервер — останній і надійний рубіж захисту.
"""

import re


def validate_login(login):
    """
    Логін: 3-30 символів, тільки латинські літери, цифри та підкреслення.
    """
    if not login:
        return "Логін не може бути порожнім."
    if len(login) < 3:
        return "Логін має містити щонайменше 3 символи."
    if len(login) > 30:
        return "Логін занадто довгий (максимум 30 символів)."
    if not re.fullmatch(r'[A-Za-z0-9_]+', login):
        return "Логін може містити тільки латинські літери, цифри та підкреслення."
    return None


def validate_password(password):
    """
    Пароль: щонайменше 6 символів.
    """
    if not password:
        return "Пароль не може бути порожнім."
    if len(password) < 6:
        return "Пароль має містити щонайменше 6 символів."
    if len(password) > 100:
        return "Пароль занадто довгий."
    return None


def validate_full_name(name):
    """
    Повне ім'я: 3-100 символів, літери (укр/лат), пробіли, апострофи, дефіси.
    """
    if not name:
        return "Ім'я не може бути порожнім."
    if len(name) < 3:
        return "Ім'я занадто коротке."
    if len(name) > 100:
        return "Ім'я занадто довге."
    # Дозволяємо українські та латинські літери, пробіл, апостроф, дефіс
    if not re.fullmatch(r"[А-Яа-яЇїІіЄєҐґA-Za-z'\u2019\- ]+", name):
        return "Ім'я може містити тільки літери, пробіли, апострофи та дефіси."
    return None


def validate_group(group):
    """
    Група: 1-20 символів, літери, цифри, дефіси.
    """
    if not group:
        return "Назва групи не може бути порожньою."
    if len(group) > 20:
        return "Назва групи занадто довга."
    if not re.fullmatch(r"[А-Яа-яЇїІіЄєҐґA-Za-z0-9\- ]+", group):
        return "Назва групи містить недопустимі символи."
    return None


def validate_email(email):
    """
    Email необов'язковий, але якщо вказано — має бути коректним.
    """
    if not email:
        return None  # порожній — це ОК (поле необов'язкове)
    if len(email) > 100:
        return "Email занадто довгий."
    # Простий, але надійний шаблон email
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        return "Невірний формат email (приклад: name@example.com)."
    return None


def validate_phone(phone):
    """
    Телефон необов'язковий. Якщо вказано — цифри, пробіли, +, -, дужки.
    """
    if not phone:
        return None
    if len(phone) > 30:
        return "Номер телефону занадто довгий."
    if not re.fullmatch(r'[0-9+\-() ]+', phone):
        return "Телефон може містити тільки цифри та символи + - ( )."
    return None


def validate_text(text, field_name="Поле", min_len=1, max_len=5000):
    """
    Загальна перевірка текстового поля (тема, адреса, зміст щоденника тощо).
    """
    if not text or len(text) < min_len:
        return f"{field_name}: занадто короткий текст (мінімум {min_len})."
    if len(text) > max_len:
        return f"{field_name}: занадто довгий текст (максимум {max_len})."
    return None


def validate_grade(grade_str):
    """
    Оцінка: ціле число 0-100.
    """
    if not grade_str:
        return "Вкажіть оцінку."
    try:
        grade = int(grade_str)
    except (ValueError, TypeError):
        return "Оцінка має бути цілим числом."
    if grade < 0 or grade > 100:
        return "Оцінка має бути від 0 до 100."
    return None


def validate_date_range(start_date, end_date):
    """
    Перевірка діапазону дат: обидві вказані, кінець пізніше початку.
    Дати у форматі рядка YYYY-MM-DD (як приходять з HTML date input).
    """
    if not start_date or not end_date:
        return "Вкажіть обидві дати."
    if end_date < start_date:
        return "Дата завершення не може бути раніше дати початку."
    if end_date == start_date:
        return "Дата завершення має бути пізніше дати початку."
    return None