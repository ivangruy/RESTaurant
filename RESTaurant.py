
from flask import Flask, render_template

app = Flask(__name__)
app.config['SECRET_KEY'] = 'IMVAATNTGRRAUSYS'

menu_data = {
    "Закуски": [
        {"name": "Брускетта с томатами", "price": 8},
        {"name": "Карпаччо из говядины", "price": 12},
        {"name": "Сырная тарелка", "price": 15},
    ],
    "Салаты": [
        {"name": "Цезарь с курицей", "price": 10},
        {"name": "Греческий салат", "price": 9},
        {"name": "Салат с авокадо и креветками", "price": 14},
    ],
    "Основные блюда": [
        {"name": "Стейк Рибай", "price": 25},
        {"name": "Лосось на гриле", "price": 20},
        {"name": "Паста Карбонара", "price": 16},
    ],
    "Десерты": [
        {"name": "Тирамису", "price": 7},
        {"name": "Чизкейк", "price": 6},
        {"name": "Мороженое", "price": 5},
    ]
}

users = {}




@app.route('/')
def index():
    return render_template('index.html')


@app.route('/menu')
def menu():
    return render_template('menu.html', menu=menu_data)


@app.route('/book', methods=['GET', 'POST'])
def book():
    return


@app.route('/register', methods=['GET', 'POST'])
def register():
   return


@app.route('/login', methods=['GET', 'POST'])
def login():
    return


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    return


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# --- Main ---
if __name__ == '__main__':
    app.run(debug=True)
