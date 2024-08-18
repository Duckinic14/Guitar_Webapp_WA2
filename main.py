from flask import Flask, render_template, url_for, request, session, redirect, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database Setup
def init_db():
  with sqlite3.connect('guitar_club.db') as conn:
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    instrument TEXT,
    section TEXT,
    skill_level TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
  equipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_name TEXT NOT NULL,
  quantity INTEGER NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    feedback TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    conn.commit()

    # cursor.execute('''
    # INSERT INTO users (username, password, role, instrument, section, skill_level) 
    # VALUES (seth, generate_password_hash('seth'), 'member', 'prime', 'prime 2', 'advanced'))

    # ''')

init_db() # create databases

def get_db_connection():
  conn = sqlite3.connect('guitar_club.db')
  conn.row_factory = sqlite3.Row # change accessing the database from a index to a key.
  return conn






@app.route("/")
def index():
  # send users to login
  if 'user_id' not in session:
      return redirect(url_for('login'))
  return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        instrument = request.form['instrument']
        section = request.form['section']
        skill_level = request.form['skill_level']

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO users (username, password, role, instrument, section, skill_level)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password, role, instrument, section, skill_level))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another one.')
            return redirect(url_for('register'))
        finally:
            conn.close()

        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')



@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    username = request.form["username"]
    password = request.form["password"]
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password): # valid credentials
      session["user_id"] = user["user_id"]
      session["username"] = user["username"]
      session["role"] = user["role"]
      flash("Login successful!")
      return redirect(url_for("index"))
    else:
      flash("Invalid credentials, try again please.")

  return render_template("login.html")

@app.route("/logout")
def logout():
  session.clear()
  return redirect(url_for("login"))

@app.route("/inventory")
def inventory():
  conn = get_db_connection()
  inventory_items = conn.execute("SELECT * FROM inventory").fetchall()
  conn.close()
  return render_template("inventory.html", inventory_items = inventory_items)

@app.route("/members")
def members():
  conn = get_db_connection()
  members = conn.execute("SELECT * FROM users").fetchall()
  conn.close()
  return render_template("members.html", members=members)

@app.route("/scores")
def scores():
  pdf_files = os.listdir(os.path.join(app.root_path, "static/pdf")) # list all files in static/pdf
  return render_template("scores.html", pdf_files=pdf_files)

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
  if request.method == "POST":
    feedback = request.form["feedback"]
    user_id = session.get("user_id")
    if user_id:
      conn = get_db_connection()
      conn.execute("INSERT INTO feedback (user_id, feedback) VALUES (?,?)", (user_id, feedback))
      conn.commit()
      conn.close()
      return "Feedback submitted!"
    else:
      return "You must be logged in to submit feedback."
  return render_template("feedback.html")


@app.route("/update_skill", methods=["POST"])
def update_skill():
  if session.get("role") == "SectionLeader":
    user_id = request.form["user_id"]
    new_skill_level = request.form["skill_level"]
    conn = get_db_connection()
    conn.execute("UPDATE users SET skill_level = ? WHERE user_id = ?", (new_skill_level, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for("members"))
  else:
    return "Access to modifying skill records exclusive to section leaders."


@app.route("/add_inventory", methods=["POST"])
def add_inventory():
    item_name = request.form["item_name"]
    quantity = request.form["quantity"]

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO inventory (item_name, quantity) VALUES (?, ?)",
        (item_name, quantity),
    )
    conn.commit()
    conn.close()
    flash("New inventory item added successfully!")
    return redirect(url_for("inventory"))


@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'static']
    if 'user_id' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)