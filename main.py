import sqlalchemy
from flask import Flask
from data import db_session
from data.users import User
from data.news import News
from data.arts import Arts
from PIL import Image

import os

from forms import LoginForm, RegisterForm, ContentForm

from datetime import datetime

from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import redirect, request, abort

from flask import render_template

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init("db/sputnik.db")


def verifyext(filename):
    ext = filename.rsplit('.', 1)[1]
    if ext == "png" or ext == "PNG" or ext == "jpg" or ext == "JPG":
        return True
    return False


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    news = db_sess.query(News).all()
    articles = db_sess.query(Arts).all()
    return render_template("index.html", news=news, articles=articles, title='Главная страница - Sputnic')


@app.route("/profile")
def profile():
    return render_template("profile.html", title='Профиль - Sputnic')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация - Sputnik', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = User()
        if user and form.age.data and int(form.age.data) >= 14:
            user.name = form.name.data
            user.surname = form.surname.data
            user.age = form.age.data
            user.email = form.email.data
            user.password = form.password.data
            db_sess.add(user)
            db_sess.commit()
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('register.html',
                               message="Возраст не может быть меньше 14-ти",
                               form=form)
    return render_template('register.html', title='Регистрация - Sputnik', form=form)


@app.route('/news_item/<int:id>')
def news(id):
    db_sess = db_session.create_session()
    news_item = db_sess.query(News).filter(News.id == id).first()
    return render_template('news_item.html', title=f'{news_item.title} - Sputnik', news_item=news_item)


@app.route('/add_news_item', methods=['GET', 'POST'])
@login_required
def add_news():
    form = ContentForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        all_news = db_sess.query(News).all()
        le = len(all_news)
        news_item = News()
        news_item.title = form.title.data
        news_item.content = form.content.data
        news_item.created_date = datetime.now().date()
        news_item.picture = ''
        current_user.news.append(news_item)

        img = Image.open(form.picture.data)
        img.save(f'static/img/news/back_news_item{le}.jpg')
        news_item.picture = f'back_news_item{le}.jpg'

        db_sess.merge(current_user)
        db_sess.commit()
        db_sess.close()

        return redirect('/')
    return render_template('content.html', title='Новая новость  - Sputnik', form=form)


@app.route('/edit_news_item/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = ContentForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news_item = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
        if news_item:
            form.title.data = news_item.title
            form.content.data = news_item.content
            form.picture.data = news_item.picture
        else:
            abort(404)
        db_sess.close()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news_item = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
        if news_item:
            news_item.title = form.title.data
            news_item.content = form.content.data
            news_item.created_date = datetime.now().date()
            if form.picture.data == str:
                db_sess.commit()
            else:
                img = Image.open(form.picture.data)
                os.remove(f'static/img/news/{news_item.picture}')
                img.save(f'static/img/news/{news_item.picture}')
                news_item.picture = f'{news_item.picture}'
                db_sess.commit()
            return redirect('/')
        else:
            abort(404)
        db_sess.close()
    return render_template('content.html', title='Редактирование новости - Sputnik', form=form)


@app.route('/delete_news_item/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_news(id):
    db_sess = db_session.create_session()
    news_item = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
    if news_item:
        cur_id = news_item.id
        os.remove(f'static/img/news/{news_item.picture}')
        db_sess.delete(news_item)
        db_sess.commit()

        news_for = db_sess.query(News).filter(News.id > cur_id)
        for cur in news_for:
            os.rename(f'static/img/news/{cur.picture}', f'static/img/news/back_news_item{cur.id - 2}.jpg')
            cur.picture = f'back_news_item{cur.id - 2}.jpg'
            cur.id = cur.id - 1
            db_sess.commit()
    else:
        abort(404)
    db_sess.close()
    return redirect('/')


@app.route('/art/<int:id>')
@login_required
def art(id):
    db_sess = db_session.create_session()
    art = db_sess.query(Arts).filter(Arts.id == id).first()
    return render_template('art.html', title=f'{art.title} - Sputnik', art=art)


@app.route('/add_art', methods=['GET', 'POST'])
@login_required
def add_art():
    form = ContentForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        all_art = db_sess.query(Arts).all()
        le = len(all_art)
        art = Arts()
        art.title = form.title.data
        art.content = form.content.data
        art.picture = ''
        art.created_date = datetime.now().date()
        current_user.arts.append(art)

        img = Image.open(form.picture.data)
        img.save(f'static/img/articles/back_art{le}.jpg')
        art.picture = f'back_art{le}.jpg'

        db_sess.merge(current_user)
        db_sess.commit()
        db_sess.close()

        return redirect('/')
    return render_template('content.html', title='Новая статья - Sputnik', form=form)


@app.route('/edit_art/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_art(id):
    form = ContentForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        art = db_sess.query(Arts).filter(Arts.id == id, Arts.user == current_user).first()
        if art:
            form.title.data = art.title
            form.content.data = art.content
            form.picture.data = art.picture
        else:
            abort(404)
        db_sess.close()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        art = db_sess.query(Arts).filter(Arts.id == id, Arts.user == current_user).first()
        if art:
            art.title = form.title.data
            art.content = form.content.data
            art.created_date = datetime.now().date()
            if form.picture.data == str:
                db_sess.commit()
            else:
                img = Image.open(form.picture.data)
                os.remove(f'static/img/articles/{art.picture}')
                img.save(f'static/img/articles/{art.picture}')
                art.picture = f'{art.picture}'
                db_sess.commit()
            return redirect('/')
        else:
            abort(404)
        db_sess.close()
    return render_template('content.html', title='Редактирование статьи - Sputnik', form=form)


@app.route('/delete_art/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_art(id):
    db_sess = db_session.create_session()
    art = db_sess.query(Arts).filter(Arts.id == id, Arts.user == current_user).first()
    if art:
        cur_id = art.id
        os.remove(f'static/img/articles/{art.picture}')
        db_sess.delete(art)
        db_sess.commit()

        arts_for = db_sess.query(Arts).filter(Arts.id > cur_id)
        for cur in arts_for:
            os.rename(f'static/img/articles/{cur.picture}', f'static/img/articles/back_art{cur.id - 2}.jpg')
            cur.picture = f'back_art{cur.id - 2}.jpg'
            cur.id = cur.id - 1
            db_sess.commit()

    else:
        abort(404)
    db_sess.close()
    return redirect('/')


@app.route("/none")
def none():
    return render_template("none.html",title='Ошибка 404 - Sputnic')


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')