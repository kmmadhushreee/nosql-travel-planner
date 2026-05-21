
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from models import get_db
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        
        if db.users.find_one({'username': username}):
            flash('Username already exists')
            return redirect(url_for('auth.register'))
            
        hashed_password = generate_password_hash(password)
        db.users.insert_one({'username': username, 'email': email, 'password': hashed_password})
        flash('Registration successful. Please login.')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.users.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            return redirect(url_for('booking.dashboard'))
        else:
            flash('Invalid username or password')
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
