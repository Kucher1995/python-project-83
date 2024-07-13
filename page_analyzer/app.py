import os
from dotenv import load_dotenv
from flask import Flask, render_template, \
    redirect, request, url_for, \
    flash, get_flashed_messages, abort
from page_analyzer import dbase as db
from page_analyzer import valid
from page_analyzer import html


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


@app.route('/urls/<id>', methods=['post', 'get'])
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


@app.route('/urls/<id>/checks', methods=['post'])
def checks(id):
    conn = db.create_connection()
    url = db.get_url(conn, id)

    response = html.get_response(url.name)
    if not response:
        app.logger.info(
            f"""{url.name} An error occurred
            while requesting the response URL.""")

        flash('Произошла ошибка при проверке', 'error')

        db.close(conn)

        return redirect(url_for('show_url', id=id), 302)

    status_code = response.status_code

    check_data = html.get_check_result(response)
    check_data.update({
        'url_id': id,
        'status_code': status_code,
    })

    app.logger.info(f'{url.name} The response was successfully received.')
    flash('Страница успешно проверена', 'success')

    try:
        db.add_url_check(conn, check_data)
    except Exception:
        abort(500)
    finally:
        db.close(conn)

    return redirect(url_for('show_url', id=id), 302)


@app.errorhandler(500)
def page_500(errors):
    app.logger.info('An error 500 occurred.')
    return render_template(
        'errors/500.html',
        errors=errors
    ), 500
