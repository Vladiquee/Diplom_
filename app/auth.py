from functools import wraps
from flask import session, redirect, url_for, flash
import hashlib

# ============================================================
# ХЕШУВАННЯ ПАРОЛІВ
# ============================================================

def hash_password(password):
    """
    Перетворює пароль у хеш (зашифрований рядок).
    Ніколи не зберігаємо пароль у відкритому вигляді!
    
    Приклад: hash_password("1234") → "03ac674216f3e15c..."
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def check_password(password, password_hash):
    """
    Перевіряє чи введений пароль відповідає збереженому хешу.
    Повертає True або False.
    """
    return hash_password(password) == password_hash


# ============================================================
# РОБОТА З СЕСІЄЮ (хто зараз залогінений)
# ============================================================

def login_user(user):
    """
    Зберігає дані користувача в сесію після успішного входу.
    Сесія — це як "пам'ять" Flask про те, хто зайшов на сайт.
    """
    session['user_id'] = user['id']
    session['user_login'] = user['login']
    session['user_role'] = user['role']


def logout_user():
    """Очищає сесію — виходить з акаунту."""
    session.clear()


def get_current_user_id():
    """Повертає id поточного користувача або None якщо не залогінений."""
    return session.get('user_id')


def get_current_user_role():
    """Повертає роль поточного користувача: 'admin', 'teacher' або 'student'."""
    return session.get('user_role')


def is_logged_in():
    """Перевіряє чи користувач залогінений."""
    return 'user_id' in session


# ============================================================
# ДЕКОРАТОРИ — ЗАХИСТ СТОРІНОК
# ============================================================
# Декоратор — це @функція яку ставиш над маршрутом.
# Вона виконується ПЕРЕД тим як відкрити сторінку.

def login_required(f):
    """
    Захищає сторінку від незалогінених користувачів.
    Якщо не залогінений — перекидає на сторінку входу.
    
    Використання:
        @app.route('/dashboard')
        @login_required
        def dashboard():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('Будь ласка, увійдіть у систему.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Захищає сторінку — дозволяє доступ тільки адміністратору.
    
    Використання:
        @app.route('/admin/students')
        @admin_required
        def admin_students():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('Будь ласка, увійдіть у систему.', 'warning')
            return redirect(url_for('login'))
        if get_current_user_role() != 'admin':
            flash('У вас немає доступу до цієї сторінки.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    """Дозволяє доступ тільки керівнику практики."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('Будь ласка, увійдіть у систему.', 'warning')
            return redirect(url_for('login'))
        if get_current_user_role() != 'teacher':
            flash('У вас немає доступу до цієї сторінки.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """Дозволяє доступ тільки студенту."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('Будь ласка, увійдіть у систему.', 'warning')
            return redirect(url_for('login'))
        if get_current_user_role() != 'student':
            flash('У вас немає доступу до цієї сторінки.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function
