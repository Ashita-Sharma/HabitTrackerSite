from flask import Flask, redirect, url_for, render_template, request

app = Flask(__name__)
@app.route('/')
def reroute():
    return redirect(url_for('sign_up'))

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

        print(email, username, password)

        return redirect(url_for('dashboard'))
    return render_template('sign_up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')



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