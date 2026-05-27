from flask import Flask, redirect, url_for, render_template, request, flash
import sqlite3
app = Flask(__name__)
app.secret_key = "mysecretkey"

@app.route('/')
def reroute():
    return redirect(url_for('sign_up'))

connect = sqlite3.connect('database.db')
connect.execute(
    'CREATE TABLE IF NOT EXISTS PARTICIPANTS (username TEXT, \
    email TEXT, password TEXT)')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('dashboard.html')

@app.route('/new-task', methods=['GET', 'POST'])
def new_task():
    return render_template('new_task.html')

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form['userEmail']
        username = request.form['userId']
        password = request.form['userPassword']
        confirm_password = request.form['ConfirmUserPassword']
        if not email:
            flash('Email is required', 'danger')
            return redirect(url_for('sign_up'))
        if not username:
            flash('Username is required', 'warning')
            return redirect(url_for('sign_up'))
        if not password:
            flash('Password field is required', 'danger')
            return redirect(url_for('sign_up'))
        if len(password) < 8:
            flash("Password must be at least 8 characters", "warning")
            return redirect(url_for('sign_up'))

        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for('sign_up'))
        with sqlite3.connect("database.db") as users:
            cursor = users.cursor()
            cursor.execute("INSERT INTO PARTICIPANTS \
            (username,email,password) VALUES (?,?,?)",
                           (username, email, password))
            users.commit()
        return redirect(url_for('dashboard'))

    return render_template('sign_up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/participants')
def participants():
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()
    cursor.execute('SELECT * FROM PARTICIPANTS')

    data = cursor.fetchall()
    return render_template("participants.html", data=data)


# @app.route('/all_tasks', methods=['POST'])
# def read_form():
#
#     # Get the form data as Python ImmutableDict datatype
#     data = request.form
#
#     ## Return the extracted information
#     return render_template('all_tasks.html', data=data)


if __name__ == "__main__":
    app.run(debug=True)