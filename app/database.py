import sqlite3

# Назва файлу бази даних — він автоматично створиться у папці проєкту
DB_NAME = 'practice_system.db'


def get_db_connection():
    """
    Створює та повертає підключення до бази даних.
    Викликай цю функцію кожного разу, коли потрібно щось прочитати або записати.
    """
    conn = sqlite3.connect(DB_NAME)

    # Вмикаємо перевірку зв'язків між таблицями (Foreign Keys)
    conn.execute('PRAGMA foreign_keys = ON')

    # Дозволяє звертатися до колонок за назвою: user['login'] замість user[1]
    conn.row_factory = sqlite3.Row

    return conn


def init_db():
    """
    Створює всі таблиці в базі даних (якщо вони ще не існують).
    Запускай цю функцію ОДИН РАЗ на початку розробки.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Користувачі — для входу всіх ролей у систему
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            login            TEXT UNIQUE NOT NULL,
            password_hash    TEXT NOT NULL,
            role             TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Студенти — профіль студента, прив'язаний до користувача
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name   TEXT NOT NULL,
            group_name  TEXT NOT NULL,
            user_id     INTEGER UNIQUE NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # 3. Викладачі (керівники практики)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name   TEXT NOT NULL,
            user_id     INTEGER UNIQUE NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # 4. Бази практики (підприємства / заклади)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            address         TEXT NOT NULL,
            phone           TEXT,
            contact_person  TEXT
        )
    ''')

    # 5. Практики — зв'язує студента, керівника та базу практики
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS practices (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL,
            company_id  INTEGER NOT NULL,
            teacher_id  INTEGER NOT NULL,
            start_date  DATE NOT NULL,
            end_date    DATE NOT NULL,
            topic       TEXT NOT NULL,
            status      TEXT DEFAULT 'assigned'
                        CHECK(status IN ('assigned', 'in_progress', 'submitted', 'graded')),
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
            FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id) ON DELETE CASCADE
        )
    ''')

    # 6. Щоденник практики — щоденні записи студента
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diary_entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            practice_id INTEGER NOT NULL,
            entry_date  DATE NOT NULL,
            content     TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (practice_id) REFERENCES practices (id) ON DELETE CASCADE
        )
    ''')

    # 7. Звіти — фінальний звіт студента з оцінкою керівника
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            practice_id      INTEGER UNIQUE NOT NULL,
            content_text     TEXT,
            file_path        TEXT,
            submitted_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            grade            INTEGER,
            teacher_comment  TEXT,
            graded_at        TIMESTAMP,
            FOREIGN KEY (practice_id) REFERENCES practices (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Базу даних успішно ініціалізовано!")


# ============================================================
# КОРИСТУВАЧІ (USERS)
# ============================================================

def create_user(login, password_hash, role):
    """Створює нового користувача. Повертає його id або None якщо логін зайнятий."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO users (login, password_hash, role) VALUES (?, ?, ?)',
            (login, password_hash, role)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Логін вже існує (UNIQUE constraint)
        return None
    finally:
        conn.close()


def get_user_by_login(login):
    """Знаходить користувача за логіном. Повертає рядок або None."""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE login = ?', (login,)
    ).fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    """Знаходить користувача за його id."""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE id = ?', (user_id,)
    ).fetchone()
    conn.close()
    return user


def delete_user(user_id):
    """
    Видаляє користувача. Завдяки ON DELETE CASCADE автоматично видаляється
    і пов'язаний профіль (студент або викладач).
    """
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()


# ============================================================
# СТУДЕНТИ (STUDENTS)
# ============================================================

def create_student(full_name, group_name, user_id):
    """Створює профіль студента, прив'язаний до існуючого користувача."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO students (full_name, group_name, user_id) VALUES (?, ?, ?)',
            (full_name, group_name, user_id)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_all_students():
    """Повертає список усіх студентів разом з їхніми логінами."""
    conn = get_db_connection()
    students = conn.execute('''
        SELECT students.*, users.login
        FROM students
        JOIN users ON students.user_id = users.id
        ORDER BY students.full_name
    ''').fetchall()
    conn.close()
    return students


def get_student_by_user_id(user_id):
    """Знаходить профіль студента за user_id (потрібно після логіну)."""
    conn = get_db_connection()
    student = conn.execute(
        'SELECT * FROM students WHERE user_id = ?', (user_id,)
    ).fetchone()
    conn.close()
    return student


def get_student_by_id(student_id):
    """Знаходить студента за його id."""
    conn = get_db_connection()
    student = conn.execute(
        'SELECT * FROM students WHERE id = ?', (student_id,)
    ).fetchone()
    conn.close()
    return student


def update_student(student_id, full_name, group_name):
    """Оновлює ім'я та групу студента."""
    conn = get_db_connection()
    conn.execute(
        'UPDATE students SET full_name = ?, group_name = ? WHERE id = ?',
        (full_name, group_name, student_id)
    )
    conn.commit()
    conn.close()


# ============================================================
# ВИКЛАДАЧІ (TEACHERS)
# ============================================================

def create_teacher(full_name, user_id):
    """Створює профіль викладача."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO teachers (full_name, user_id) VALUES (?, ?)',
            (full_name, user_id)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_all_teachers():
    """Повертає список усіх викладачів."""
    conn = get_db_connection()
    teachers = conn.execute(
        'SELECT * FROM teachers ORDER BY full_name'
    ).fetchall()
    conn.close()
    return teachers


def get_teacher_by_user_id(user_id):
    """Знаходить профіль викладача за user_id."""
    conn = get_db_connection()
    teacher = conn.execute(
        'SELECT * FROM teachers WHERE user_id = ?', (user_id,)
    ).fetchone()
    conn.close()
    return teacher


# ============================================================
# БАЗИ ПРАКТИКИ (COMPANIES)
# ============================================================

def create_company(name, address, phone, contact_person):
    """Додає нову базу практики."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO companies (name, address, phone, contact_person) VALUES (?, ?, ?, ?)',
        (name, address, phone, contact_person)
    )
    conn.commit()
    company_id = cursor.lastrowid
    conn.close()
    return company_id


def get_all_companies():
    """Повертає список усіх баз практики."""
    conn = get_db_connection()
    companies = conn.execute(
        'SELECT * FROM companies ORDER BY name'
    ).fetchall()
    conn.close()
    return companies


def get_company_by_id(company_id):
    """Знаходить базу практики за id."""
    conn = get_db_connection()
    company = conn.execute(
        'SELECT * FROM companies WHERE id = ?', (company_id,)
    ).fetchone()
    conn.close()
    return company


def update_company(company_id, name, address, phone, contact_person):
    """Оновлює дані бази практики."""
    conn = get_db_connection()
    conn.execute(
        '''UPDATE companies
           SET name = ?, address = ?, phone = ?, contact_person = ?
           WHERE id = ?''',
        (name, address, phone, contact_person, company_id)
    )
    conn.commit()
    conn.close()


def delete_company(company_id):
    """Видаляє базу практики."""
    conn = get_db_connection()
    conn.execute('DELETE FROM companies WHERE id = ?', (company_id,))
    conn.commit()
    conn.close()


# ============================================================
# ПРАКТИКИ (PRACTICES)
# ============================================================

def create_practice(student_id, company_id, teacher_id, start_date, end_date, topic):
    """Призначає студента на практику."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO practices
               (student_id, company_id, teacher_id, start_date, end_date, topic)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (student_id, company_id, teacher_id, start_date, end_date, topic)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_practice_by_student_id(student_id):
    """
    Повертає практику студента разом з назвою закладу та ім'ям керівника.
    Використовуй після логіну студента.
    """
    conn = get_db_connection()
    practice = conn.execute('''
        SELECT practices.*,
               companies.name        AS company_name,
               companies.address     AS company_address,
               teachers.full_name    AS teacher_name
        FROM practices
        JOIN companies ON practices.company_id = companies.id
        JOIN teachers  ON practices.teacher_id  = teachers.id
        WHERE practices.student_id = ?
    ''', (student_id,)).fetchone()
    conn.close()
    return practice


def get_practices_by_teacher_id(teacher_id):
    """Повертає всі практики, які веде цей керівник."""
    conn = get_db_connection()
    practices = conn.execute('''
        SELECT practices.*,
               students.full_name    AS student_name,
               students.group_name   AS student_group,
               companies.name        AS company_name,
               teachers.full_name    AS teacher_name
        FROM practices
        JOIN students  ON practices.student_id  = students.id
        JOIN companies ON practices.company_id  = companies.id
        JOIN teachers  ON practices.teacher_id  = teachers.id
        WHERE practices.teacher_id = ?
        ORDER BY students.full_name
    ''', (teacher_id,)).fetchall()
    conn.close()
    return practices


def get_all_practices():
    """Повертає всі практики з повною інформацією (для адміна)."""
    conn = get_db_connection()
    practices = conn.execute('''
        SELECT practices.*,
               students.full_name    AS student_name,
               students.group_name   AS student_group,
               companies.name        AS company_name,
               teachers.full_name    AS teacher_name
        FROM practices
        JOIN students  ON practices.student_id  = students.id
        JOIN companies ON practices.company_id  = companies.id
        JOIN teachers  ON practices.teacher_id  = teachers.id
        ORDER BY students.full_name
    ''').fetchall()
    conn.close()
    return practices


def get_practice_by_id(practice_id):
    """Знаходить одну практику за id."""
    conn = get_db_connection()
    practice = conn.execute(
        'SELECT * FROM practices WHERE id = ?', (practice_id,)
    ).fetchone()
    conn.close()
    return practice


def update_practice_status(practice_id, new_status):
    """Змінює статус практики (assigned → in_progress → submitted → graded)."""
    conn = get_db_connection()
    conn.execute(
        'UPDATE practices SET status = ? WHERE id = ?',
        (new_status, practice_id)
    )
    conn.commit()
    conn.close()


def delete_practice(practice_id):
    """Видаляє практику (щоденник і звіт видаляться автоматично через CASCADE)."""
    conn = get_db_connection()
    conn.execute('DELETE FROM practices WHERE id = ?', (practice_id,))
    conn.commit()
    conn.close()


# ============================================================
# ЩОДЕННИК ПРАКТИКИ (DIARY ENTRIES)
# ============================================================

def add_diary_entry(practice_id, entry_date, content):
    """Додає новий запис у щоденник практики."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO diary_entries (practice_id, entry_date, content) VALUES (?, ?, ?)',
        (practice_id, entry_date, content)
    )
    conn.commit()
    entry_id = cursor.lastrowid
    conn.close()
    return entry_id


def get_diary_entries(practice_id):
    """Повертає всі записи щоденника для конкретної практики, від найновіших."""
    conn = get_db_connection()
    entries = conn.execute(
        'SELECT * FROM diary_entries WHERE practice_id = ? ORDER BY entry_date DESC',
        (practice_id,)
    ).fetchall()
    conn.close()
    return entries


def update_diary_entry(entry_id, content):
    """Редагує запис щоденника."""
    conn = get_db_connection()
    conn.execute(
        'UPDATE diary_entries SET content = ? WHERE id = ?',
        (content, entry_id)
    )
    conn.commit()
    conn.close()


def delete_diary_entry(entry_id):
    """Видаляє запис щоденника."""
    conn = get_db_connection()
    conn.execute('DELETE FROM diary_entries WHERE id = ?', (entry_id,))
    conn.commit()
    conn.close()


# ============================================================
# ЗВІТИ (REPORTS)
# ============================================================

def submit_report(practice_id, content_text, file_path=None):
    """
    Студент здає звіт. Якщо звіт вже існує — оновлює його.
    Також автоматично змінює статус практики на 'submitted'.
    """
    conn = get_db_connection()
    try:
        conn.execute(
            '''INSERT INTO reports (practice_id, content_text, file_path)
               VALUES (?, ?, ?)''',
            (practice_id, content_text, file_path)
        )
    except sqlite3.IntegrityError:
        # Звіт вже є — оновлюємо його
        conn.execute(
            '''UPDATE reports
               SET content_text = ?, file_path = ?, submitted_at = CURRENT_TIMESTAMP
               WHERE practice_id = ?''',
            (content_text, file_path, practice_id)
        )
    # Змінюємо статус практики на "здано"
    conn.execute(
        'UPDATE practices SET status = ? WHERE id = ?',
        ('submitted', practice_id)
    )
    conn.commit()
    conn.close()


def get_report_by_practice_id(practice_id):
    """Повертає звіт для конкретної практики."""
    conn = get_db_connection()
    report = conn.execute(
        'SELECT * FROM reports WHERE practice_id = ?', (practice_id,)
    ).fetchone()
    conn.close()
    return report


def grade_report(practice_id, grade, teacher_comment):
    """
    Керівник виставляє оцінку та залишає коментар до звіту.
    Також змінює статус практики на 'graded'.
    """
    conn = get_db_connection()
    conn.execute(
        '''UPDATE reports
           SET grade = ?, teacher_comment = ?, graded_at = CURRENT_TIMESTAMP
           WHERE practice_id = ?''',
        (grade, teacher_comment, practice_id)
    )
    conn.execute(
        'UPDATE practices SET status = ? WHERE id = ?',
        ('graded', practice_id)
    )
    conn.commit()
    conn.close()


def get_all_reports():
    """Повертає всі звіти з іменем студента та назвою закладу (для адміна)."""
    conn = get_db_connection()
    reports = conn.execute('''
        SELECT reports.*,
               students.full_name   AS student_name,
               students.group_name  AS student_group,
               companies.name       AS company_name,
               practices.status     AS practice_status
        FROM reports
        JOIN practices ON reports.practice_id = practices.id
        JOIN students  ON practices.student_id = students.id
        JOIN companies ON practices.company_id = companies.id
        ORDER BY reports.submitted_at DESC
    ''').fetchall()
    conn.close()
    return reports


# ============================================================
# ЗАПУСК ПРИ ПРЯМОМУ ВИКОНАННІ ФАЙЛУ
# ============================================================

if __name__ == '__main__':
    init_db()


# ============================================================
# НОВІ ФУНКЦІЇ — ТИЖДЕНЬ 1
# ============================================================

def get_students_without_practice():
    """
    Повертає список студентів у яких ще НЕ призначено практику.
    Використовується у формі призначення — щоб адмін не міг
    випадково призначити двічі одному студенту.
    """
    conn = get_db_connection()
    students = conn.execute('''
        SELECT students.*, users.login
        FROM students
        JOIN users ON students.user_id = users.id
        WHERE students.id NOT IN (
            SELECT student_id FROM practices
        )
        ORDER BY students.full_name
    ''').fetchall()
    conn.close()
    return students


def search_students(query):
    """
    Пошук студентів за іменем або групою.
    query — рядок пошуку (наприклад 'Іванен' або '121-22')
    """
    conn = get_db_connection()
    pattern = f'%{query}%'
    students = conn.execute('''
        SELECT students.*, users.login
        FROM students
        JOIN users ON students.user_id = users.id
        WHERE students.full_name LIKE ?
           OR students.group_name LIKE ?
        ORDER BY students.full_name
    ''', (pattern, pattern)).fetchall()
    conn.close()
    return students


def get_practices_filtered(status=None, teacher_id=None, search=None):
    """
    Повертає практики з фільтрацією на рівні БД.
    status     — 'assigned' | 'in_progress' | 'submitted' | 'graded' | None (всі)
    teacher_id — id керівника або None (всі)
    search     — рядок пошуку по імені студента або назві закладу
    """
    conn = get_db_connection()

    query = '''
        SELECT practices.*,
               students.full_name  AS student_name,
               students.group_name AS student_group,
               companies.name      AS company_name,
               teachers.full_name  AS teacher_name
        FROM practices
        JOIN students  ON practices.student_id  = students.id
        JOIN companies ON practices.company_id  = companies.id
        JOIN teachers  ON practices.teacher_id  = teachers.id
        WHERE 1=1
    '''
    params = []

    if status:
        query += ' AND practices.status = ?'
        params.append(status)

    if teacher_id:
        query += ' AND practices.teacher_id = ?'
        params.append(teacher_id)

    if search:
        query += ' AND (students.full_name LIKE ? OR companies.name LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])

    query += ' ORDER BY students.full_name'

    practices = conn.execute(query, params).fetchall()
    conn.close()
    return practices


# ============================================================
# НОВІ ФУНКЦІЇ — КЕРУВАННЯ ОБЛІКОВИМИ ЗАПИСАМИ
# ============================================================

def get_all_teachers_with_login():
    """Повертає всіх викладачів разом з логіном."""
    conn = get_db_connection()
    teachers = conn.execute('''
        SELECT teachers.*, users.login, users.id AS user_id
        FROM teachers
        JOIN users ON teachers.user_id = users.id
        ORDER BY teachers.full_name
    ''').fetchall()
    conn.close()
    return teachers


def update_user_login(user_id, new_login):
    """
    Змінює логін користувача.
    Повертає True якщо успішно, False якщо логін вже зайнятий.
    """
    conn = get_db_connection()
    try:
        conn.execute(
            'UPDATE users SET login = ? WHERE id = ?',
            (new_login, user_id)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Логін вже існує
        return False
    finally:
        conn.close()


def update_user_password(user_id, new_password_hash):
    """Змінює пароль користувача (приймає вже захешований пароль)."""
    conn = get_db_connection()
    conn.execute(
        'UPDATE users SET password_hash = ? WHERE id = ?',
        (new_password_hash, user_id)
    )
    conn.commit()
    conn.close()


def delete_teacher(user_id):
    """Видаляє викладача (і його обліковий запис через CASCADE)."""
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()


def update_teacher(teacher_id, full_name):
    """Оновлює ім'я викладача."""
    conn = get_db_connection()
    conn.execute(
        'UPDATE teachers SET full_name = ? WHERE id = ?',
        (full_name, teacher_id)
    )
    conn.commit()
    conn.close()


def get_teacher_by_id(teacher_id):
    """Знаходить викладача за id."""
    conn = get_db_connection()
    teacher = conn.execute('''
        SELECT teachers.*, users.login, users.id AS user_id
        FROM teachers
        JOIN users ON teachers.user_id = users.id
        WHERE teachers.id = ?
    ''', (teacher_id,)).fetchone()
    conn.close()
    return teacher


# ============================================================
# НОВІ ФУНКЦІЇ — УПРАВЛІННЯ ОБЛІКОВИМИ ЗАПИСАМИ
# ============================================================

def get_all_teachers_with_logins():
    """Повертає всіх викладачів разом з їхніми логінами."""
    conn = get_db_connection()
    teachers = conn.execute('''
        SELECT teachers.*, users.login, users.id AS user_id
        FROM teachers
        JOIN users ON teachers.user_id = users.id
        ORDER BY teachers.full_name
    ''').fetchall()
    conn.close()
    return teachers


def update_user_login(user_id, new_login):
    """
    Змінює логін користувача.
    Повертає True якщо успішно, False якщо логін вже зайнятий.
    """
    conn = get_db_connection()
    try:
        conn.execute(
            'UPDATE users SET login = ? WHERE id = ?',
            (new_login, user_id)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Логін вже існує (UNIQUE constraint)
        return False
    finally:
        conn.close()


def update_user_password(user_id, new_password_hash):
    """Змінює пароль користувача (приймає вже захешований пароль)."""
    conn = get_db_connection()
    conn.execute(
        'UPDATE users SET password_hash = ? WHERE id = ?',
        (new_password_hash, user_id)
    )
    conn.commit()
    conn.close()


def delete_teacher(user_id):
    """Видаляє викладача (і його обліковий запис через CASCADE)."""
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()


def get_teacher_by_id(teacher_id):
    """Знаходить викладача за його id."""
    conn = get_db_connection()
    teacher = conn.execute(
        'SELECT teachers.*, users.login, users.id AS user_id FROM teachers JOIN users ON teachers.user_id = users.id WHERE teachers.id = ?',
        (teacher_id,)
    ).fetchone()
    conn.close()
    return teacher


# ============================================================
# АВАТАРКИ КОРИСТУВАЧІВ
# ============================================================

def add_avatar_column():
    """
    Додає колонку avatar до таблиці users якщо її ще немає.
    Викликається при запуску — безпечно якщо колонка вже існує.
    """
    conn = get_db_connection()
    try:
        conn.execute("ALTER TABLE users ADD COLUMN avatar TEXT")
        conn.commit()
        print("✅ Колонку avatar додано до таблиці users")
    except sqlite3.OperationalError:
        pass  # Колонка вже існує — все ок
    finally:
        conn.close()


def update_user_avatar(user_id, filename):
    """Зберігає назву файлу аватарки для користувача."""
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET avatar = ? WHERE id = ?",
        (filename, user_id)
    )
    conn.commit()
    conn.close()