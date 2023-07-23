from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_migrate import Migrate
from datetime import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SECRET_KEY'] = 'eureka'

db = SQLAlchemy(app)

login_manager = LoginManager(app)

migrate = Migrate(app, db)


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
    time = db.Column(db.String, nullable=False)


class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    lastname = db.Column(db.String, nullable=False)
    rank = db.Column(db.String)
    phone = db.Column(db.String, nullable=False)
    event_id = db.Column(db.Integer, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def get_valid_events(events):
    output = []
    for event in events:
        if datetime.strptime(event.date, '%d.%m.%Y').date() >= datetime.today().date():
            output.append(event)
    return output


@app.route('/')
def index():
    events = get_valid_events(db.session.query(Event).order_by(Event.date).all())
    return render_template('index.html', events=events)


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
    events = get_valid_events(db.session.query(Event).order_by(Event.date).all())
    registrations = []
    for event in events:
        registrations.append(len(db.session.query(Registration).filter_by(event_id=event.id).all()))

    return render_template('admin.html', events=events, registrations=registrations)


@app.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    if request.method == 'POST':
        data = request.form
        if data['title'] and data['date'] and data['time']:
            date = (datetime.strptime(data['date'], '%Y-%m-%d').date()).strftime('%d.%m.%Y')
            new_event = Event(title=data['title'], date=date, time=data['time'])
            db.session.add(new_event)
            db.session.commit()
            return redirect('/admin')
        else:
            redirect('/add_event')
    return render_template('add_event.html')


@app.route('/delete_event/<int:id>')
@login_required
def delete_event(id):
    event = db.session.query(Event).filter_by(id=id).first()
    db.session.delete(event)

    event_registrations = db.session.query(Registration).filter_by(event_id=id).all()
    for user in event_registrations:
        db.session.delete(user)
        
    db.session.commit()
    return redirect('/admin')


@app.route('/edit_event/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_event(id):
    if request.method == 'POST':
        event = db.session.query(Event).filter_by(id=id).first()
        event.title = request.form['title']
        event.date = (datetime.strptime(request.form['date'], '%Y-%m-%d').date()).strftime('%d.%m.%Y')
        event.time = request.form['time']

        db.session.add(event)
        db.session.commit()

        return redirect('/admin')

    event = db.session.query(Event).filter_by(id=id).first()
    date = (datetime.strptime(event.date, '%d.%m.%Y').date()).strftime('%Y-%m-%d')
    return render_template('edit_event.html', event=event, date=date)


@app.route('/registration/<int:id>', methods=['GET', 'POST'])
def registration(id):
    if request.method == 'POST':
        new_registration = Registration(name=request.form['name'], lastname=request.form['lastname'],
                                        rank=request.form['rank'], phone=request.form['phone'], event_id=id)
        db.session.add(new_registration)
        db.session.commit()
        return redirect('/')
    event = db.session.query(Event).filter_by(id=id).first()
    return render_template('registration.html', event=event)


@app.route('/registrations/<int:id>')
@login_required
def registrations(id):
    registrations_list = db.session.query(Registration).filter_by(event_id=id).all()
    event = db.session.query(Event).filter_by(id=id).first()

    return render_template('registrations.html', event=event, registrations=registrations_list)


@app.errorhandler(401)
def custom_401(error):
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
