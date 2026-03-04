from flask import Flask, render_template, request, redirect, session, send_file
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.pdfgen import canvas
from datetime import date
import os

app = Flask(__name__)
app.secret_key = "jovil_secret_key"

# ---------------- MYSQL CONFIG ----------------
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""   # put password if exists
app.config["MYSQL_DB"] = "jovilrapidlearn"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

# ---------------- DATABASE SETUP ----------------
def setup_database():
    cur = mysql.connection.cursor()

    cur.execute("CREATE DATABASE IF NOT EXISTS jovilrapidlearn")
    cur.execute("USE jovilrapidlearn")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100) UNIQUE,
        password VARCHAR(255),
        role VARCHAR(20)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS modules(
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(200),
        description VARCHAR(300)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS progress(
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        module_id INT,
        completed INT
    )
    """)

    # ---------- DEFAULT ADMIN ----------
    cur.execute("SELECT * FROM users WHERE email=%s", ("admin@jovil.com",))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
            ("Admin", "admin@jovil.com",
             generate_password_hash("admin123"), "admin")
        )

    # ---------- DEFAULT STUDENT ----------
    cur.execute("SELECT * FROM users WHERE email=%s", ("student@jovil.com",))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
            ("Student", "student@jovil.com",
             generate_password_hash("student123"), "student")
        )

    mysql.connection.commit()
    cur.close()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- LOGIN & REGISTER ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        action = request.form["action"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        cur = mysql.connection.cursor()

        if action == "register":
            name = request.form["name"]
            cur.execute(
                "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
                (name, email, generate_password_hash(password), role)
            )
            mysql.connection.commit()

        if action == "login":
            cur.execute(
                "SELECT * FROM users WHERE email=%s AND role=%s",
                (email, role)
            )
            user = cur.fetchone()
            if user and check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                session["role"] = user["role"]
                return redirect("/courses")

        cur.close()
    return render_template("login.html")

# ---------------- COURSES ----------------
@app.route("/courses")
def courses():
    if "user_id" not in session:
        return redirect("/login")

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM modules")
    modules = cur.fetchall()
    cur.close()

    return render_template(
        "courses.html",
        modules=modules,
        role=session["role"]
    )

# ---------------- ADMIN CRUD ----------------
@app.route("/add_module", methods=["POST"])
def add_module():
    if session["role"] != "admin":
        return "Unauthorized"

    title = request.form["title"]
    description = request.form["description"]

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO modules (title,description) VALUES (%s,%s)",
        (title, description)
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/courses")

@app.route("/update_module/<int:id>", methods=["POST"])
def update_module(id):
    if session["role"] != "admin":
        return "Unauthorized"

    title = request.form["title"]
    description = request.form["description"]

    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE modules SET title=%s, description=%s WHERE id=%s",
        (title, description, id)
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/courses")

@app.route("/delete_module/<int:id>")
def delete_module(id):
    if session["role"] != "admin":
        return "Unauthorized"

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM modules WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect("/courses")

# ---------------- STUDENT PROGRESS ----------------
@app.route("/complete_module/<int:module_id>")
def complete_module(module_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT * FROM progress
        WHERE user_id=%s AND module_id=%s
    """, (session["user_id"], module_id))

    if not cur.fetchone():
        cur.execute(
            "INSERT INTO progress (user_id,module_id,completed) VALUES (%s,%s,1)",
            (session["user_id"], module_id)
        )
        mysql.connection.commit()

    cur.close()
    return redirect("/check_completion")

@app.route("/check_completion")
def check_completion():
    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM modules")
    total = cur.fetchone()["total"]

    cur.execute(
        "SELECT COUNT(*) AS done FROM progress WHERE user_id=%s",
        (session["user_id"],)
    )
    done = cur.fetchone()["done"]

    cur.close()
    return redirect("/certificate" if total > 0 and done == total else "/courses")

# ---------------- CERTIFICATE (PDF) ----------------
@app.route("/certificate")
def certificate():
    cur = mysql.connection.cursor()
    cur.execute("SELECT name FROM users WHERE id=%s", (session["user_id"],))
    name = cur.fetchone()["name"]
    cur.close()

    today = date.today().strftime("%d %B %Y")
    file_name = "certificate.pdf"

    c = canvas.Canvas(file_name)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(300, 750, "Certificate of Completion")
    c.setFont("Helvetica", 16)
    c.drawCentredString(300, 700, name)
    c.drawCentredString(300, 660, "has successfully completed")
    c.drawCentredString(300, 620, "Web Development Course")
    c.drawCentredString(300, 580, f"Date: {today}")
    c.drawCentredString(300, 540, "JovilRapidLearn")
    c.save()

    return send_file(file_name, as_attachment=True)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        setup_database()
    app.run(debug=True)
