from flask.testing import FlaskClient
import pytest

from page_analyzer.app import app

import psycopg2
import os
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
app.secret_key = os.getenv('SECRET_KEY')


@pytest.fixture
def client():
    return app.test_client()


def truncate_table_urls() -> bool:
    response = True

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        cur.execute("TRUNCATE TABLE urls RESTART IDENTITY CASCADE;")
        conn.commit()
    except psycopg2.Error:
        response = False

    cur.close()
    conn.close()

    return response


def test_index(client: FlaskClient):
    response = client.get('/')

    assert response.status_code == 200
    assert bytes('Анализатор страниц', encoding='utf-8') in response.data


def test_empty_add_url(client: FlaskClient):
    response = client.post('/urls', data={
        "url": ""
    })

    assert response.status_code == 422
    assert bytes('URL обязателен', encoding='utf-8') in response.data


def test_fail_add_url(client: FlaskClient):
    response = client.post('/urls', data={
        "url": "aghfhnbsdfb"
    })

    assert response.status_code == 422
    assert bytes('Некорректный URL', encoding='utf-8') in response.data


def test_succes_add_url(client: FlaskClient):
    response = client.post('/urls', data={
        "url": "https://hexlet.io"
    })
    assert response.status_code == 302

    response = client.get('/urls/1')
    assert bytes('Страница успешно добавлена',
                 encoding='utf-8') in response.data

    truncate_table_urls()


def test_info_add_url(client: FlaskClient):
    client.post('/urls', data={
        "url": "https://hexlet.io"
    })
    response = client.post('/urls', data={
        "url": "https://hexlet.io"
    })
    assert response.status_code == 302

    response = client.get('/urls/1')
    assert bytes('Страница уже существует', encoding='utf-8') in response.data

    truncate_table_urls()


def test_url_check(client: FlaskClient):
    client.post('/urls', data={
        "url": "https://hexlet.io"
    })

    response = client.post('/urls/1/checks', follow_redirects=True)

    assert bytes('Страница успешно проверена',
                 encoding='utf-8') in response.data
    assert bytes('Online programming school', encoding='utf-8') in response.data
    assert bytes('Programming education: online',
                 encoding='utf-8') in response.data
    assert bytes('Author training programs', encoding='utf-8') in response.data

    truncate_table_urls()


def test_order_urls(client: FlaskClient):
    client.post('/urls', data={
        "url": "https://hexlet.io"
    })
    client.post('/urls', data={
        "url": "https://mail.ru"
    })

    client.post('/urls/1/checks')

    response = client.get('/urls')

    url2 = response.data.find(b'https://mail.ru')
    url1 = response.data.find(b'https://hexlet.io')
    assert url2 < url1
    assert bytes('200', encoding='utf-8') in response.data

    truncate_table_urls()


def test_url_check_fail(client: FlaskClient):
    client.post('/urls', data={
        "url": "https://dfgh.ru"
    })

    response = client.post('/urls/1/checks', follow_redirects=True)

    assert bytes('Произошла ошибка при проверке',
                 encoding='utf-8') in response.data

    truncate_table_urls()
