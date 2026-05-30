from flask import Flask, redirect, url_for, render_template, request, flash
from flask import session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "mysecretkey"

@app.route('/')
def reroute():
    if 'user_id' not in session:
        return redirect(url_for('sign_up'))
    return redirect(url_for('dashboard'))


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

    filter_by = request.args.get('filter', 'all')
    sort_by = request.args.get('sort', 'deadline')
    search_query = request.args.get('search', '')

    query = "SELECT * FROM TASKS WHERE user_id = ?"
    params = [session['user_id']]

    if search_query:
        query += " AND (task_name LIKE ? OR description LIKE ?)"
        params.append(f"%{search_query}%")
        params.append(f"%{search_query}%")

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

    return render_template('dashboard.html', tasks=tasks, filter_by=filter_by, sort_by=sort_by, search_query=search_query)

@app.route('/new-task', methods=['GET', 'POST'])
def new_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('new_task.html')

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if 'user_id' in session:
        flash('Already logged in!', 'warning')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['userEmail']
        username = request.form['userId']
        password = request.form['userPassword']
        confirm_password = request.form['ConfirmUserPassword']
        if not email:
            flash('Email is required!', 'danger')
            return redirect(url_for('sign_up'))
        if not username:
            flash('Username is required!', 'warning')
            return redirect(url_for('sign_up'))
        if not password:
            flash('Password field is required!', 'danger')
            return redirect(url_for('sign_up'))
        if len(password) < 8:
            flash("Password must be at least 8 characters!", "warning")
            return redirect(url_for('sign_up'))
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM PARTICIPANTS WHERE email = ?", (email,))
            user = cursor.fetchone()
            if user:
                flash("E-Mail already in use!", "danger")
                return redirect(url_for('sign_up'))

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('sign_up'))

        hashed_password = generate_password_hash(password)
        with sqlite3.connect("database.db") as users:
            cursor = users.cursor()
            cursor.execute("INSERT INTO PARTICIPANTS \
            (username,email,password) VALUES (?,?,?)",
                           (username, email, hashed_password))
            users.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('sign_up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        flash('Already logged in!', 'warning')
        return redirect(url_for('dashboard'))
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

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash("Please log in!", 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']

        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE PARTICIPANTS SET email = ?, username = ? WHERE id = ?",
                (email, username, session['user_id']))
            conn.commit()

        session['username'] = username
        flash("Profile updated!", "success")
        return redirect(url_for('dashboard'))


    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email, username FROM PARTICIPANTS WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()

    return render_template('profile.html', user=user)

@app.route('/delete-task/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM TASKS WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
        conn.commit()

    flash("Task deleted", "info")
    return redirect(url_for('dashboard'))

@app.route('/complete-task/<int:task_id>')
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE TASKS SET completed = 1 WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
        conn.commit()

    flash("Task marked as complete!", "success")
    return redirect(url_for('dashboard'))

@app.route('/edit-task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
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
                "UPDATE TASKS SET task_name = ?, description = ?, deadline = ?, priority = ? WHERE id = ? AND user_id = ?",
                (task_name, description, deadline, priority, task_id, session['user_id'])
            )
            conn.commit()

        flash("Task updated!", "success")
        return redirect(url_for('dashboard'))

    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM TASKS WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
        task = cursor.fetchone()

    return render_template('edit_task.html', task=task)

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