from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user
from datetime import timedelta


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        id = 1

        user = User.query.filter_by(id=id).first()
        print(user)
        custom_duration = timedelta(hours=12)
        if user:
            if check_password_hash(user.password, password):
                flash('Login Successful!', 'success')
                login_user(user, remember=True, duration=custom_duration)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect Token, try again.', 'error')
        else:
            flash('Server Error', 'error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successful!', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
@login_required
def sign_up():
    if request.method == 'POST':
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # Menggunakan current_user untuk mendapatkan pengguna yang sudah login
        user = current_user

        if not check_password_hash(user.password, password1):
            flash('Old token is wrong!', 'error')
            print('incorrect')
        elif len(password2) < 7:
            flash('New Token must be at least 7 characters.', 'error')
            print('token kurang')
        else:
            # Update password pada objek User yang sudah ada
            user.password = generate_password_hash(password2)
            db.session.commit()
            flash('Token updated!', 'success')
            print('Success')

    return render_template("sign_up.html", user=current_user)
