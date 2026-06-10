import pytest
from app import app
from auth import hash_password, check_password

@pytest.fixture
def client():
    """Налаштування тестового клієнта Flask"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_page_loads(client):
    """Перевірка доступності сторінки авторизації (HTTP 200)"""
    rv = client.get('/login')
    assert rv.status_code == 200

def test_unauthorized_access_protection(client):
    """Перевірка захисту приватних маршрутів (редирект на логін)"""
    rv = client.get('/dashboard')
    assert rv.status_code == 302  # 302 - це код редиректу
    assert '/login' in rv.headers['Location']

def test_password_hashing():
    """Перевірка криптографічного алгоритму хешування паролів"""
    password = "secure_password_123"
    hashed = hash_password(password)
    
    # Хеш не повинен дорівнювати паролю
    assert hashed != password
    # Правильний пароль має проходити перевірку
    assert check_password(password, hashed) == True
    # Неправильний пароль має відхилятися
    assert check_password("wrong_password", hashed) == False