from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SECRET_KEY'] = 'eureka'

db = SQLAlchemy(app)

login_manager = LoginManager(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    password = db.Column(db.String(16), nullable=False)

    def __repr__(self):
        return self.name

    def is_authenticated(self):
        return True


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    date = db.Column(db.String, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))

    if request.method == 'POST':
        user = db.session.query(User).filter_by(name=request.form['login']).first()
        if user and request.form['password'] == user.password:
            login_user(user)
            return redirect('/admin')
        else:
            return 'error'

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')


@app.errorhandler(401)
def custom_401(error):
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
