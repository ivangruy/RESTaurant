
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, TextAreaField, SelectField, DateField, SubmitField, EmailField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from datetime import datetime
import sqlite3
import threading
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'IMVAATNTGRRAUSYS'
app.config['DATABASE'] = 'restaurant.db'

db_local = threading.local()


def get_db():
    if not hasattr(db_local, 'db'):
        db_local.db = sqlite3.connect(app.config['DATABASE'])
    return db_local.db


@app.teardown_appcontext
def close_db(error):
    if hasattr(db_local, 'db'):
        db_local.db.close()


def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        with app.open_resource('schema.sql', mode='r') as f:
            cursor.executescript(f.read())

        menu_data = get_all_menu_items_from_data()
        for category, items in menu_data.items():
            for item in items:
                cursor.execute(
                    "INSERT OR IGNORE INTO menu_items (id, name, category, price, image) VALUES (?, ?, ?, ?, ?)",
                    (item['id'], item['name'], category, item['price'], item['image'])
                )

        db.commit()


menu_data = {
    "Закуски": [
        {"id": 1, "name": "Брускетта с томатами", "price": 8, "image": "https://via.placeholder.com/150"},
        {"id": 2, "name": "Карпаччо из говядины", "price": 12, "image": "https://via.placeholder.com/150"},
        {"id": 3, "name": "Сырная тарелка", "price": 15, "image": "https://via.placeholder.com/150"},
    ],
    "Салаты": [
        {"id": 4, "name": "Цезарь с курицей", "price": 10, "image": "https://via.placeholder.com/150"},
        {"id": 5, "name": "Греческий салат", "price": 9, "image": "https://via.placeholder.com/150"},
        {"id": 6, "name": "Салат с авокадо и креветками", "price": 14, "image": "https://via.placeholder.com/150"},
    ],
    "Основные блюда": [
        {"id": 7, "name": "Стейк Рибай", "price": 25, "image": "https://via.placeholder.com/150"},
        {"id": 8, "name": "Лосось на гриле", "price": 20, "image": "https://via.placeholder.com/150"},
        {"id": 9, "name": "Паста Карбонара", "price": 16, "image": "https://via.placeholder.com/150"},
    ],
    "Десерты": [
        {"id": 10, "name": "Тирамису", "price": 7, "image": "https://via.placeholder.com/150"},
        {"id": 11, "name": "Чизкейк", "price": 6, "image": "https://via.placeholder.com/150"},
        {"id": 12, "name": "Мороженое", "price": 5, "image": "https://via.placeholder.com/150"},
    ]
}

# --- Формы ---

class RegistrationForm(FlaskForm):
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    city = StringField('Город', validators=[DataRequired()])
    phone = StringField('Телефон', validators=[DataRequired()])
    email = EmailField('Почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class BookingForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])  # Added Name field
    date = DateField('Дата', validators=[DataRequired()], default=datetime.now)
    time = SelectField('Время', choices=[(f"{hour:02d}:{minute:02d}", f"{hour:02d}:{minute:02d}")
                                           for hour in range(12, 24) for minute in (0, 30)], validators=[DataRequired()])
    guests = IntegerField('Количество человек', validators=[DataRequired()])
    comment = TextAreaField('Комментарий')
    submit = SubmitField('Забронировать')


class AddMenuItemForm(FlaskForm):
    name = StringField('Название блюда', validators=[DataRequired()])
    category = StringField('Категория', validators=[DataRequired()])
    price = FloatField('Цена', validators=[DataRequired()])
    image = StringField('Ссылка на изображение', validators=[DataRequired()])
    submit = SubmitField('Добавить блюдо')

# --- Функции API ---

def get_menu_item_by_id(item_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, category, price, image FROM menu_items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    if item:
        return {
            'id': item[0],
            'name': item[1],
            'category': item[2],
            'price': item[3],
            'image': item[4]
        }
    return None


def get_all_menu_items():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, category, price, image FROM menu_items")
    items = cursor.fetchall()

    menu_data = {}
    for item in items:
        item_dict = {
            'id': item[0],
            'name': item[1],
            'price': item[3],
            'image': item[4]
        }
        category = item[2]
        if category not in menu_data:
            menu_data[category] = []
        menu_data[category].append(item_dict)
    return menu_data


def get_all_menu_items_from_data():
    return menu_data


def get_available_times(date):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT time FROM bookings WHERE date = ?", (date,))
    booked_times = [row[0] for row in cursor.fetchall()]

    all_times = [f"{hour:02d}:{minute:02d}" for hour in range(12, 24) for minute in (0, 30)]
    available_times = []
    for time in all_times:
        if booked_times.count(time) < 5:
            available_times.append((time, time))

    return available_times


# --- Вкладки ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/menu')
def menu():
    menu_data = get_all_menu_items()
    return render_template('menu.html', menu=menu_data)


@app.route('/add_to_cart/<int:item_id>')
def add_to_cart(item_id):
    item = get_menu_item_by_id(item_id)
    if item:
        if 'cart' not in session:
            session['cart'] = {}
        cart = session['cart']
        if str(item_id) in cart:
            cart[str(item_id)] += 1
        else:
            cart[str(item_id)] = 1
        session['cart'] = cart  # Update the session
        flash(f"Товар '{item['name']}' добавлен в корзину!", 'success')
    else:
        flash("Товар не найден.", 'error')
    return redirect(url_for('menu'))


@app.route('/remove_from_cart/<int:item_id>')
def remove_from_cart(item_id):
    cart = session.get('cart', {})
    item_id_str = str(item_id)
    if item_id_str in cart:
        del cart[item_id_str]
        session['cart'] = cart  # Update the session
        flash("Товар удален из корзины.", 'success')
    return redirect(url_for('view_cart'))


@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    total_price = 0
    for item_id, quantity in cart.items():
        item = get_menu_item_by_id(int(item_id))
        if item:
            item['quantity'] = quantity
            cart_items.append(item)
            total_price += item['price'] * quantity

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)


@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        flash("Пожалуйста, войдите, чтобы оформить заказ.", 'error')
        return redirect(url_for('login'))

    cart = session.get('cart', {})
    if not cart:
        flash("Ваша корзина пуста.", 'warning')
        return redirect(url_for('cart'))

    user_id = session['user_id']
    order_total = 0

    try:
        db = get_db()
        cursor = db.cursor()
        order_details = []
        for item_id, quantity in cart.items():
            item = get_menu_item_by_id(int(item_id))
            if item:
                order_total += item['price'] * quantity
                order_details.append((int(item_id), quantity))

        cursor.execute("INSERT INTO orders (user_id, order_date, total_amount) VALUES (?, ?, ?)",
                       (user_id, datetime.now(), order_total))
        order_id = cursor.lastrowid

        for item_id, quantity in order_details:
            cursor.execute("INSERT INTO order_items (order_id, item_id, quantity) VALUES (?, ?, ?)",
                           (order_id, item_id, quantity))

        db.commit()

        session['cart'] = {}
        flash("Заказ успешно оформлен!", 'success')
        return redirect(url_for('index'))

    except Exception as e:
        db.rollback()  # Rollback in case of error
        flash(f"Ошибка при оформлении заказа: {e}", 'error')
        return redirect(url_for('cart'))


@app.route('/book', methods=['GET', 'POST'])
def book():
    form = BookingForm()
    today = datetime.now().date()
    form.date.default = today
    form.date.data = today

    if request.method == 'POST':
        date = form.date.data
        time = form.time.data
        datetime_str = f"{date} {time}"
        booking_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')

        if form.validate_on_submit():
            name = form.name.data
            guests = form.guests.data
            comment = form.comment.data

            if 'user_id' in session:
                user_id = session['user_id']
            else:
                user_id = None

            try:
                db = get_db()
                cursor = db.cursor()
                cursor.execute(
                    "INSERT INTO bookings (booking_datetime, guests, comment, user_id, name, date, time) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (booking_datetime, guests, comment, user_id, name, date, time))  # Include user_id and name

                db.commit()
                flash("Столик успешно забронирован!", 'success')
                return redirect(url_for('index'))
            except Exception as e:
                flash(f"Ошибка при бронировании столика: {e}", 'error')
                return render_template('book.html', form=form)
        else:
            flash("Пожалуйста, заполните все обязательные поля.", 'error')


    if form.date.data:
        available_times = get_available_times(form.date.data)
        form.time.choices = available_times
    else:
        form.time.choices = get_available_times(today)


    return render_template('book.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        hashed_password = generate_password_hash(password)

        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO users (first_name, last_name, city, phone, email, password) VALUES (?, ?, ?, ?, ?, ?)",
                (form.first_name.data, form.last_name.data, form.city.data, form.phone.data, email, hashed_password))
            db.commit()
            flash("Регистрация прошла успешно! Теперь вы можете войти.", 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Этот адрес электронной почты уже зарегистрирован.", 'error')
        except Exception as e:
            flash(f"Произошла ошибка при регистрации: {e}", 'error')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT id, password, first_name, last_name, city, phone FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user[1], password):
                session['user_id'] = user[0]
                session['email'] = email
                session['first_name'] = user[2]
                flash("Вы успешно вошли!", 'success')
                return redirect(url_for('profile'))
            else:
                flash("Неверная почта или пароль.", 'error')
        except Exception as e:
            flash(f"Произошла ошибка при входе: {e}", 'error')

    return render_template('login.html', form=form)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT first_name, last_name, city, phone, email FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()

        if not user_data:
            flash("Пользователь не найден.", 'error')
            return redirect(url_for('logout'))

        # Create a dictionary from the fetched data
        user_dict = {
            'first_name': user_data[0],
            'last_name': user_data[1],
            'city': user_data[2],
            'phone': user_data[3],
            'email': user_data[4]
        }

        form = RegistrationForm(data=user_dict)

        if form.validate_on_submit():
            # Update user data
            first_name = form.first_name.data
            last_name = form.last_name.data
            city = form.city.data
            phone = form.phone.data
            email = form.email.data

            cursor.execute("""
                UPDATE users
                SET first_name = ?, last_name = ?, city = ?, phone = ?, email = ?
                WHERE id = ?
            """, (first_name, last_name, city, phone, email, user_id))
            db.commit()
            session['email'] = email

            flash("Профиль успешно обновлен!", 'success')
            return redirect(url_for('profile'))

        return render_template('profile.html', form=form)

    except Exception as e:
        flash(f"Произошла ошибка при загрузке/обновлении профиля: {e}", 'error')
        return render_template('profile.html', form=form)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('email', None)
    session.pop('first_name', None)
    return redirect(url_for('index'))


@app.route('/add_menu_item', methods=['GET', 'POST'])
def add_menu_item():
    form = AddMenuItemForm()
    if form.validate_on_submit():
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO menu_items (name, category, price, image) VALUES (?, ?, ?, ?)",
                (form.name.data, form.category.data, form.price.data, form.image.data))
            db.commit()
            flash("Блюдо успешно добавлено в меню!", 'success')
            return redirect(url_for('menu'))
        except Exception as e:
            flash(f"Ошибка при добавлении блюда: {e}", 'error')
    return render_template('add_menu_item.html', form=form)


# --- Error Handling ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# --- Main ---
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
