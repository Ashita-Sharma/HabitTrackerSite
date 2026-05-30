from flask import Flask, redirect, url_for, render_template, request, flash
from flask import session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "mysecretkey"

@app.route('/')
def reroute():
    return redirect(url_for('sign_up'))

def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS PARTICIPANTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            password TEXT
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS TASKS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_name TEXT,
            description TEXT,
            deadline TEXT,
            priority TEXT DEFAULT 'medium',
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES PARTICIPANTS(id)
        )
        """)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        task_name = request.form['TaskName']
        description = request.form['TextDescription']
        deadline = request.form['Deadline']
        priority = request.form['Priority']

        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO TASKS (user_id, task_name, description, deadline, priority) VALUES (?, ?, ?, ?, ?)",
                (session['user_id'], task_name, description, deadline, priority)
            )
            conn.commit()

        flash("Task added!", "success")
        return redirect(url_for('dashboard'))

    # Get filter and sort from URL parameters
    filter_by = request.args.get('filter', 'all')
    sort_by = request.args.get('sort', 'deadline')

    query = "SELECT * FROM TASKS WHERE user_id = ?"
    params = [session['user_id']]

    if filter_by == 'pending':
        query += " AND completed = 0"
    elif filter_by == 'completed':
        query += " AND completed = 1"
    elif filter_by == 'overdue':
        query += " AND completed = 0 AND deadline < DATE('now')"

    if sort_by == 'deadline':
        query += " ORDER BY deadline ASC"
    elif sort_by == 'priority':
        query += " ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END"

    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        tasks = cursor.fetchall()

    return render_template('dashboard.html', tasks=tasks, filter_by=filter_by, sort_by=sort_by)

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

        hashed_password = generate_password_hash(password)
        with sqlite3.connect("database.db") as users:
            cursor = users.cursor()
            cursor.execute("INSERT INTO PARTICIPANTS \
            (username,email,password) VALUES (?,?,?)",
                           (username, email, hashed_password))
            users.commit()
        return redirect(url_for('dashboard'))

    return render_template('sign_up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['enteredEmail']
        password = request.form['enteredPassword']

        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, password FROM PARTICIPANTS WHERE email = ?", (email,))
            user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")

# @app.route('/participants')
# def participants():
#     with sqlite3.connect('database.db') as conn:
#         cursor = conn.cursor()
#         cursor.execute('SELECT * FROM PARTICIPANTS')
#         data = cursor.fetchall()
#
#     return render_template("participants.html", data=data)

# @app.route('/delete-user/<int:user_id>')
# def delete_user(user_id):
#     with sqlite3.connect("database.db") as conn:
#         cursor = conn.cursor()
#         cursor.execute("DELETE FROM PARTICIPANTS WHERE id = ?", (user_id,))
#         conn.commit()
#
#     return redirect(url_for('participants'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# @app.route('/all_tasks', methods=['POST'])
# def read_form():
#
#     # Get the form data as Python ImmutableDict datatype
#     data = request.form
#
#     ## Return the extracted information
#     return render_template('all_tasks.html', data=data)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)