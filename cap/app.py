from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS
from flask_mail import Mail, Message
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import os
from datetime import datetime
import requests

app = Flask(__name__, static_folder='static')
CORS(app)  # Add CORS support
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# reset password
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')

mail = Mail(app)

class Medicine(db.Model):
    __tablename__ = 'med_name'
    mid = db.Column(db.Integer, primary_key=True)
    g_name = db.Column(db.String)
    b_name = db.Column(db.String)
    batch = db.Column(db.String)
    exp = db.Column(db.String)
    strength = db.Column(db.String)
    net = db.Column(db.Integer)

    def to_dict(self):
        return {
            'g_name': self.g_name,
            'b_name': self.b_name,
            'batch': self.batch,
            'exp': self.exp,
            'strength': self.strength,
            'net': self.net
        }

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    balance = db.Column(db.Float, default=10.0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    #Add methods to generate and verify tokens in the User model:
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    search_term = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SearchHistory {self.search_term}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'search_term': self.search_term,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

db.create_all()

def save_search_history(user_id, search_term):
    history = SearchHistory(user_id=user_id, search_term=search_term)
    db.session.add(history)
    db.session.commit()


def get_search_history(user_id):
    history = SearchHistory.query.filter_by(user_id=user_id).order_by(SearchHistory.timestamp.desc()).all()
    return history

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first name')
        last_name = request.form.get('last name')
        phone = request.form.get('phone')
        email = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('register'))

        user = User.query.filter_by(email=email).first()
        if user is not None:
            flash('Email already registered.')
            return redirect(url_for('register'))

        new_user = User(first_name=first_name, last_name=last_name, phone=phone, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Successfully registered.')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(email=username).first()

        if user and user.check_password(password):
            login_user(user)
            session['user_id'] = user.id
            flash('login successful', 'success')
            return redirect(url_for('index'))
        else:
            flash('Incorrect username or password, please try again', 'danger')
    return render_template('login.html')

@app.route('/search', methods=['GET'])
def search():
    return render_template('search.html')


@app.route('/dashboard')
@login_required
def dashboard():
    user_id = current_user.id  # Get the current user's ID
    return render_template('dashboard.html', user_id=user_id)



@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            send_reset_email(user)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('login'))

        else:
            flash('Email does not exist.', 'warning')

    return render_template('forgot_password.html')

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html', user=current_user)
    else:
        return render_template('index.html')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/about')
def about():
    return render_template('about.html')

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender=app.config['MAIL_USERNAME'], recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
    {url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('forgot_password.html', token=token)



        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))

    return render_template('forgot_password.html', token=token)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/update_password', methods=['POST'])
def update_password():
    # get form data
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # Check if the old password is correct
    if not check_password_hash(current_user.password_hash, old_password):
        flash('Old password is incorrect.')
        return redirect(url_for('dashboard'))

    # Check if the new password and confirm password are the same
    if new_password != confirm_password:
        flash('New password and confirm password do not match.')
        return redirect(url_for('dashboard'))

    # update password
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    flash('Password updated successfully.')
    return redirect(url_for('dashboard'))

@app.route('/deduct_balance', methods=['POST'])
@login_required
def deduct_balance():
    current_user.balance -= 0.05
    db.session.commit()
    return jsonify(success=True)

@app.route('/api/balance')
@login_required
def api_balance():
    return jsonify(balance=current_user.balance)

@app.route('/api/current_user/balance', methods=['GET'])
@login_required
def current_user_balance():
    balance = current_user.balance
    return jsonify({'balance': balance})

@app.route('/update', methods=['POST'])
def update():
    # get form data
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    phone = request.form.get('phone')

    # Check if the data is empty
    if not first_name or not last_name or not email or not phone:
        return "Error: All fields must be filled."

    # Update the current user's data
    current_user.first_name = first_name
    current_user.last_name = last_name
    current_user.email = email
    current_user.phone = phone

    # Submit the database session
    db.session.commit()

    # Notify the user that the update was successful
    flash('Your profile has been updated!')


    return redirect(url_for('dashboard'))


@app.route('/save_search', methods=['POST'])
def save_search():
    data = request.get_json()
    user_id = current_user.id

    search_term = data.get('search_term')
    timestamp = datetime.utcnow()

    # Create a new search history entry
    search_history = SearchHistory(user_id=user_id, search_term=search_term, timestamp=timestamp)
    db.session.add(search_history)
    db.session.commit()

    return jsonify({'status': 'success'})


@app.route('/search_history/<int:user_id>')
def search_history(user_id):
    history = get_search_history(user_id)  # Call the function
    return jsonify(history=[h.to_dict() for h in history])



if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)


