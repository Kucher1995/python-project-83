import os
from dotenv import load_dotenv
from flask import Flask, render_template, \
    redirect, request, url_for, \
    flash, get_flashed_messages, abort
from page_analyzer import dbase as db
from page_analyzer import valid


app = Flask(__name__)

load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')


@app.route('/')
def analyzer():
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'analyzer.html',
        messages=messages)


@app.route('/urls', methods=['get'])
def show_urls():
    conn = db.create_connection()
    urls = db.get_url_check(conn)
    db.close(conn)

    return render_template(
        'urls.html',
        urls=urls
    ), 200


@app.route('/urls', methods=['post'])
def add_url():
    url = request.form.get('url')
    errors = valid.validate_url(url)
    if errors:
        for error in errors:
            flash(error, 'error')
        messages = get_flashed_messages(with_categories=True)
        app.logger.info(f'{url} URL validation error.')
        return render_template(
            'analyzer.html',
            input_url=url,
            messages=messages,
        ), 422

    normalize_url = [valid.normalize_url(url)]
    conn = db.create_connection()
    url = db.get_url_by_name(conn, normalize_url)
    if url:
        flash('Страница уже существует', 'info')
        id = url.id
    else:
        id = db.add_url(conn, normalize_url)
        if id:
            app.logger.info(
                f'{url} Writing data to the database was successful.'
            )
            flash('Страница успешно добавлена', 'success')
        else:
            db.close(conn)
            abort(500)
    db.close(conn)
    return redirect(url_for('show_url', id=id), 302)


@app.route('/urls/<id>', methods=['get'])
def show_url(id):
    conn = db.create_connection()
    url = db.get_url(conn, id)
    checks = db.get_checks_url(conn, id)
    db.close(conn)
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'url.html',
        url=url,
        messages=messages,
        checks=checks,
    )
