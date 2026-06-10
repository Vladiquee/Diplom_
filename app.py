from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import date
from database import (
    init_db,
    # Користувачі
    create_user, get_user_by_login,
    # Студенти
    create_student, get_all_students, get_student_by_user_id,
    get_student_by_id, update_student,
    # Викладачі
    create_teacher, get_all_teachers, get_teacher_by_user_id,
    # Компанії
    create_company, get_all_companies, get_company_by_id,
    update_company, delete_company,
    # Практики
    create_practice, get_all_practices, get_practice_by_id,
    get_practice_by_student_id, get_practices_by_teacher_id,
    update_practice_status, delete_practice,
    # Щоденник
    add_diary_entry, get_diary_entries,
    update_diary_entry, delete_diary_entry,
    # Звіти
    submit_report, get_report_by_practice_id,
    grade_report, get_all_reports,
    # Видалення
    delete_user,
    # Нові функції (тиждень 1)
    get_students_without_practice,
    search_students,
    get_practices_filtered,
    # Управління викладачами та обліковими записами
    get_all_teachers_with_logins,
    update_user_login,
    update_user_password,
    delete_teacher,
    get_teacher_by_id,
)
from auth import (
    hash_password, check_password,
    login_user, logout_user,
    login_required, admin_required,
    teacher_required, student_required,
    get_current_user_id, get_current_user_role,
)

# ============================================================
# НАЛАШТУВАННЯ ЗАСТОСУНКУ
# ============================================================

app = Flask(__name__)

# Секретний ключ для шифрування сесій.
# У реальному проєкті заміни на довгий випадковий рядок!
app.secret_key = 'praktyka-poltava-2026-secret-key'

# Максимальний розмір файлу для завантаження — 16 МБ
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


# ============================================================
# ГОЛОВНА СТОРІНКА — ПЕРЕНАПРАВЛЕННЯ
# ============================================================

@app.route('/')
def index():
    """Головна сторінка — перенаправляє залежно від ролі."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))


# ============================================================
# ВХІД / ВИХІД
# ============================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  — показує форму входу
    POST — перевіряє логін і пароль
    """
    # Якщо вже залогінений — одразу на дашборд
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        login_input = request.form.get('login', '').strip()
        password_input = request.form.get('password', '').strip()

        # Перевіряємо чи заповнені поля
        if not login_input or not password_input:
            flash('Заповніть усі поля.', 'warning')
            return render_template('login.html')

        # Шукаємо користувача в БД
        user = get_user_by_login(login_input)

        if user and check_password(password_input, user['password_hash']):
            # Пароль правильний — зберігаємо в сесію
            login_user(user)
            flash(f'Ласкаво просимо, {user["login"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Невірний логін або пароль.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Виходить з акаунту та перенаправляє на вхід."""
    logout_user()
    flash('Ви вийшли з системи.', 'info')
    return redirect(url_for('login'))


# ============================================================
# ДАШБОРД — ПЕРЕНАПРАВЛЕННЯ ЗА РОЛЛЮ
# ============================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Перенаправляє кожну роль на свою головну сторінку."""
    role = get_current_user_role()
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    elif role == 'student':
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))


# ============================================================
# АДМІНІСТРАТОР
# ============================================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Головна панель адміністратора зі статистикою."""
    students = get_all_students()
    practices = get_all_practices()
    companies = get_all_companies()
    teachers = get_all_teachers()
    reports = get_all_reports()

    # Підраховуємо статистику
    stats = {
        'total_students':  len(students),
        'total_practices': len(practices),
        'total_companies': len(companies),
        'total_teachers':  len(teachers),
        'graded':    sum(1 for p in practices if p['status'] == 'graded'),
        'submitted': sum(1 for p in practices if p['status'] == 'submitted'),
        'in_progress': sum(1 for p in practices if p['status'] == 'in_progress'),
        'assigned':  sum(1 for p in practices if p['status'] == 'assigned'),
    }

    return render_template('admin/dashboard.html', stats=stats)


# --- Студенти (адмін) ---

@app.route('/admin/students')
@admin_required
def admin_students():
    """Список усіх студентів з пошуком за іменем або групою."""
    query    = request.args.get('q', '').strip()
    students = search_students(query) if query else get_all_students()
    return render_template('admin/students.html', students=students, query=query)


@app.route('/admin/students/add', methods=['GET', 'POST'])
@admin_required
def admin_add_student():
    """Додавання нового студента."""
    if request.method == 'POST':
        full_name  = request.form.get('full_name', '').strip()
        group_name = request.form.get('group_name', '').strip()
        login      = request.form.get('login', '').strip()
        password   = request.form.get('password', '').strip()

        if not all([full_name, group_name, login, password]):
            flash('Заповніть усі поля.', 'warning')
            return render_template('admin/add_student.html')

        # Спочатку створюємо користувача, потім профіль студента
        user_id = create_user(login, hash_password(password), 'student')
        if user_id is None:
            flash('Логін вже зайнятий. Оберіть інший.', 'danger')
            return render_template('admin/add_student.html')

        create_student(full_name, group_name, user_id)
        flash(f'Студента {full_name} успішно додано!', 'success')
        return redirect(url_for('admin_students'))

    return render_template('admin/add_student.html')


@app.route('/admin/students/edit/<int:student_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_student(student_id):
    """Редагування даних студента."""
    student = get_student_by_id(student_id)
    if not student:
        flash('Студента не знайдено.', 'danger')
        return redirect(url_for('admin_students'))

    if request.method == 'POST':
        full_name  = request.form.get('full_name', '').strip()
        group_name = request.form.get('group_name', '').strip()

        if not full_name or not group_name:
            flash('Заповніть усі поля.', 'warning')
            return render_template('admin/edit_student.html', student=student)

        update_student(student_id, full_name, group_name)
        flash('Дані студента оновлено!', 'success')
        return redirect(url_for('admin_students'))

    return render_template('admin/edit_student.html', student=student)


@app.route('/admin/students/delete/<int:user_id>')
@admin_required
def admin_delete_student(user_id):
    """Видалення студента (і його облікового запису)."""
    delete_user(user_id)
    flash('Студента видалено.', 'info')
    return redirect(url_for('admin_students'))


# --- Бази практики (адмін) ---

@app.route('/admin/companies')
@admin_required
def admin_companies():
    """Список баз практики."""
    companies = get_all_companies()
    return render_template('admin/companies.html', companies=companies)


@app.route('/admin/companies/add', methods=['GET', 'POST'])
@admin_required
def admin_add_company():
    """Додавання нової бази практики."""
    if request.method == 'POST':
        name           = request.form.get('name', '').strip()
        address        = request.form.get('address', '').strip()
        phone          = request.form.get('phone', '').strip()
        contact_person = request.form.get('contact_person', '').strip()

        if not name or not address:
            flash('Назва та адреса обов\'язкові.', 'warning')
            return render_template('admin/add_company.html')

        create_company(name, address, phone, contact_person)
        flash(f'Базу практики "{name}" додано!', 'success')
        return redirect(url_for('admin_companies'))

    return render_template('admin/add_company.html')


@app.route('/admin/companies/edit/<int:company_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_company(company_id):
    """Редагування бази практики."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Базу практики не знайдено.', 'danger')
        return redirect(url_for('admin_companies'))

    if request.method == 'POST':
        name           = request.form.get('name', '').strip()
        address        = request.form.get('address', '').strip()
        phone          = request.form.get('phone', '').strip()
        contact_person = request.form.get('contact_person', '').strip()

        update_company(company_id, name, address, phone, contact_person)
        flash('Дані оновлено!', 'success')
        return redirect(url_for('admin_companies'))

    return render_template('admin/edit_company.html', company=company)


@app.route('/admin/companies/delete/<int:company_id>')
@admin_required
def admin_delete_company(company_id):
    """Видалення бази практики."""
    delete_company(company_id)
    flash('Базу практики видалено.', 'info')
    return redirect(url_for('admin_companies'))


# --- Практики (адмін) ---

@app.route('/admin/practices')
@admin_required
def admin_practices():
    """Список практик з фільтрацією за статусом і пошуком."""
    status  = request.args.get('status', '').strip() or None
    search  = request.args.get('q', '').strip()      or None
    practices = get_practices_filtered(status=status, search=search)
    teachers  = get_all_teachers()
    return render_template('admin/practices.html',
                           practices=practices,
                           teachers=teachers,
                           current_status=status or 'all',
                           current_search=search or '')


@app.route('/admin/practices/add', methods=['GET', 'POST'])
@admin_required
def admin_add_practice():
    """Призначення студента на практику."""
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        company_id = request.form.get('company_id')
        teacher_id = request.form.get('teacher_id')
        start_date = request.form.get('start_date')
        end_date   = request.form.get('end_date')
        topic      = request.form.get('topic', '').strip()

        if not all([student_id, company_id, teacher_id, start_date, end_date, topic]):
            flash('Заповніть усі поля.', 'warning')
        else:
            # ✅ ЗАХИСТ ВІД ДУБЛЮВАННЯ
            existing = get_practice_by_student_id(int(student_id))
            if existing:
                flash('Цьому студенту вже призначено практику! Спочатку видаліть попередню.', 'danger')
            else:
                create_practice(student_id, company_id, teacher_id,
                                start_date, end_date, topic)
                flash('Практику призначено!', 'success')
                return redirect(url_for('admin_practices'))

    # ✅ Тільки студенти БЕЗ практики у списку вибору
    students  = get_students_without_practice()
    companies = get_all_companies()
    teachers  = get_all_teachers()
    return render_template('admin/add_practice.html',
                           students=students,
                           companies=companies,
                           teachers=teachers)


@app.route('/admin/practices/delete/<int:practice_id>')
@admin_required
def admin_delete_practice(practice_id):
    """Видалення практики."""
    delete_practice(practice_id)
    flash('Практику видалено.', 'info')
    return redirect(url_for('admin_practices'))


# --- Керівники (адмін) ---

@app.route('/admin/teachers/add', methods=['GET', 'POST'])
@admin_required
def admin_add_teacher():
    """Додавання нового керівника практики."""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        login     = request.form.get('login', '').strip()
        password  = request.form.get('password', '').strip()

        if not all([full_name, login, password]):
            flash('Заповніть усі поля.', 'warning')
            return render_template('admin/add_teacher.html')

        user_id = create_user(login, hash_password(password), 'teacher')
        if user_id is None:
            flash('Логін вже зайнятий.', 'danger')
            return render_template('admin/add_teacher.html')

        create_teacher(full_name, user_id)
        flash(f'Керівника {full_name} додано!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/add_teacher.html')



# --- Список викладачів (адмін) ---

@app.route('/admin/teachers')
@admin_required
def admin_teachers():
    """Список усіх керівників практики."""
    teachers = get_all_teachers_with_logins()
    return render_template('admin/teachers.html', teachers=teachers)


@app.route('/admin/teachers/delete/<int:user_id>')
@admin_required
def admin_delete_teacher(user_id):
    """Видалення керівника практики."""
    delete_teacher(user_id)
    flash('Керівника видалено.', 'info')
    return redirect(url_for('admin_teachers'))


# --- Редагування облікових записів (логін / пароль) ---

@app.route('/admin/credentials/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_credentials(user_id):
    """Зміна логіну та пароля будь-якого користувача."""
    from database import get_user_by_id
    user = get_user_by_id(user_id)
    if not user:
        flash('Користувача не знайдено.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        new_login    = request.form.get('login', '').strip()
        new_password = request.form.get('password', '').strip()
        changed = []

        # Змінюємо логін якщо заповнений
        if new_login and new_login != user['login']:
            ok = update_user_login(user_id, new_login)
            if ok:
                changed.append('логін')
            else:
                flash(f'Логін «{new_login}» вже зайнятий. Оберіть інший.', 'danger')
                return render_template('admin/edit_credentials.html', user=user)

        # Змінюємо пароль якщо заповнений
        if new_password:
            update_user_password(user_id, hash_password(new_password))
            changed.append('пароль')

        if changed:
            flash(f'Успішно змінено: {", ".join(changed)}.', 'success')
        else:
            flash('Нічого не змінено.', 'info')

        # Повертаємо на відповідний список
        if user['role'] == 'student':
            return redirect(url_for('admin_students'))
        elif user['role'] == 'teacher':
            return redirect(url_for('admin_teachers'))
        else:
            return redirect(url_for('admin_dashboard'))

    return render_template('admin/edit_credentials.html', user=user)



# --- Налаштування акаунту адміна ---

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    """Адмін змінює свій власний логін та пароль."""
    user_id = get_current_user_id()
    from database import get_user_by_id
    user = get_user_by_id(user_id)

    if request.method == 'POST':
        new_login    = request.form.get('login', '').strip()
        old_password = request.form.get('old_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        changed = []

        # Перевіряємо старий пароль
        if old_password and not check_password(old_password, user['password_hash']):
            flash('Старий пароль введено невірно.', 'danger')
            return render_template('admin/settings.html', user=user)

        # Змінюємо логін
        if new_login and new_login != user['login']:
            ok = update_user_login(user_id, new_login)
            if ok:
                session['user_login'] = new_login
                changed.append('логін')
            else:
                flash(f'Логін «{new_login}» вже зайнятий.', 'danger')
                return render_template('admin/settings.html', user=user)

        # Змінюємо пароль
        if new_password:
            if not old_password:
                flash('Щоб змінити пароль — введіть спочатку старий.', 'warning')
                return render_template('admin/settings.html', user=user)
            update_user_password(user_id, hash_password(new_password))
            changed.append('пароль')

        if changed:
            flash(f'Успішно змінено: {", ".join(changed)}!', 'success')
        else:
            flash('Нічого не змінено.', 'info')

        return redirect(url_for('admin_settings'))

    return render_template('admin/settings.html', user=user)


# ============================================================
# КЕРІВНИК ПРАКТИКИ (TEACHER)
# ============================================================

@app.route('/teacher')
@teacher_required
def teacher_dashboard():
    """Головна панель керівника — список його студентів."""
    user_id = get_current_user_id()
    teacher = get_teacher_by_user_id(user_id)

    if not teacher:
        flash('Профіль керівника не знайдено.', 'danger')
        return redirect(url_for('logout'))

    practices = get_practices_by_teacher_id(teacher['id'])
    return render_template('teacher/dashboard.html',
                           teacher=teacher,
                           practices=practices)


@app.route('/teacher/report/<int:practice_id>', methods=['GET', 'POST'])
@teacher_required
def teacher_view_report(practice_id):
    """Перегляд звіту студента та виставлення оцінки."""
    practice = get_practice_by_id(practice_id)
    report   = get_report_by_practice_id(practice_id)
    diary    = get_diary_entries(practice_id)

    if not practice:
        flash('Практику не знайдено.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    if request.method == 'POST':
        grade   = request.form.get('grade')
        comment = request.form.get('comment', '').strip()

        if not grade:
            flash('Вкажіть оцінку.', 'warning')
        else:
            grade_report(practice_id, int(grade), comment)
            flash('Оцінку виставлено!', 'success')
            return redirect(url_for('teacher_dashboard'))

    return render_template('teacher/report.html',
                           practice=practice,
                           report=report,
                           diary=diary)


# ============================================================
# СТУДЕНТ
# ============================================================

@app.route('/student')
@student_required
def student_dashboard():
    """Головна панель студента — інформація про практику."""
    user_id = get_current_user_id()
    student  = get_student_by_user_id(user_id)

    if not student:
        flash('Профіль студента не знайдено.', 'danger')
        return redirect(url_for('logout'))

    practice = get_practice_by_student_id(student['id'])
    report   = get_report_by_practice_id(practice['id']) if practice else None

    return render_template('student/dashboard.html',
                           student=student,
                           practice=practice,
                           report=report)


@app.route('/student/diary', methods=['GET', 'POST'])
@student_required
def student_diary():
    """Щоденник практики — перегляд і додавання записів."""
    user_id  = get_current_user_id()
    student  = get_student_by_user_id(user_id)
    practice = get_practice_by_student_id(student['id'])

    if not practice:
        flash('Вам ще не призначено практику.', 'warning')
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        entry_date = request.form.get('entry_date')
        content    = request.form.get('content', '').strip()

        if not entry_date or not content:
            flash('Заповніть дату та зміст запису.', 'warning')
        else:
            add_diary_entry(practice['id'], entry_date, content)
            # ✅ АВТОСТАТУС — якщо практика ще 'assigned', змінюємо на 'in_progress'
            if practice['status'] == 'assigned':
                update_practice_status(practice['id'], 'in_progress')
            flash('Запис додано!', 'success')
            return redirect(url_for('student_diary'))

    entries = get_diary_entries(practice['id'])
    return render_template('student/diary.html',
                           practice=practice,
                           entries=entries)


@app.route('/student/diary/delete/<int:entry_id>')
@student_required
def student_delete_diary_entry(entry_id):
    """Видалення запису щоденника."""
    delete_diary_entry(entry_id)
    flash('Запис видалено.', 'info')
    return redirect(url_for('student_diary'))


@app.route('/student/report', methods=['GET', 'POST'])
@student_required
def student_report():
    """Здача фінального звіту."""
    user_id  = get_current_user_id()
    student  = get_student_by_user_id(user_id)
    practice = get_practice_by_student_id(student['id'])

    if not practice:
        flash('Вам ще не призначено практику.', 'warning')
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        content_text = request.form.get('content_text', '').strip()

        if not content_text:
            flash('Напишіть текст звіту.', 'warning')
        else:
            submit_report(practice['id'], content_text)
            flash('Звіт успішно здано! Очікуйте перевірки.', 'success')
            return redirect(url_for('student_dashboard'))

    report = get_report_by_practice_id(practice['id'])
    return render_template('student/report.html',
                           practice=practice,
                           report=report)




# ============================================================
# МІЙ АКАУНТ — для всіх ролей
# ============================================================

@app.route('/account', methods=['GET', 'POST'])
@login_required
def my_account():
    """Зміна логіну та пароля для будь-якої ролі."""
    user_id = get_current_user_id()
    from database import get_user_by_id
    user = get_user_by_id(user_id)

    if request.method == 'POST':
        new_login    = request.form.get('login', '').strip()
        old_password = request.form.get('old_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        changed = []

        # Перевіряємо старий пароль якщо хочуть змінити пароль
        if new_password and not old_password:
            flash('Щоб змінити пароль — введіть спочатку старий.', 'warning')
            return render_template('account.html', user=user)

        if old_password and not check_password(old_password, user['password_hash']):
            flash('Старий пароль введено невірно.', 'danger')
            return render_template('account.html', user=user)

        # Змінюємо логін
        if new_login and new_login != user['login']:
            ok = update_user_login(user_id, new_login)
            if ok:
                session['user_login'] = new_login
                changed.append('логін')
            else:
                flash(f'Логін «{new_login}» вже зайнятий.', 'danger')
                return render_template('account.html', user=user)

        # Змінюємо пароль
        if new_password:
            update_user_password(user_id, hash_password(new_password))
            changed.append('пароль')

        if changed:
            flash(f'Успішно змінено: {", ".join(changed)}!', 'success')
        else:
            flash('Нічого не змінено.', 'info')

        return redirect(url_for('my_account'))

    return render_template('account.html', user=user)


# ============================================================
# ЗАПУСК СЕРВЕРА
# ============================================================

if __name__ == '__main__':
    # Створюємо таблиці при першому запуску
    init_db()

    # Створюємо адміністратора за замовчуванням (якщо потрібно)
    from database import get_user_by_login, create_user
    if get_user_by_login('admin') is None:
        create_user('admin', hash_password('admin123'), 'admin')
        print("✅ Створено адміністратора: login=admin, password=admin123")
        print("⚠️  Змініть пароль після першого входу!")

    print("🚀 Сервер запущено: http://localhost:5000")

    # debug=True — автоматично перезапускає сервер при змінах у коді
    app.run(debug=True)