from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3

app = Flask(__name__)
app.secret_key = "lmskey"

# DATABASE
conn = sqlite3.connect("lms.db", check_same_thread=False)
cursor = conn.cursor()

# USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
email TEXT,
password TEXT
)
""")

# COURSES TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS courses(
id INTEGER PRIMARY KEY AUTOINCREMENT,
course TEXT,
description TEXT
)
""")

# LESSONS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS lessons(
id INTEGER PRIMARY KEY AUTOINCREMENT,
course_id INTEGER,
title TEXT,
content TEXT
)
""")

# QUIZ TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS quiz(
id INTEGER PRIMARY KEY AUTOINCREMENT,
lesson_id INTEGER,
question TEXT,
option1 TEXT,
option2 TEXT,
option3 TEXT,
option4 TEXT,
answer TEXT
)
""")

conn.commit()


# HOME
@app.route("/")
def home():
    return render_template("home.html")


# LOGIN PAGE
@app.route("/login")
def login():
    return render_template("login.html")


# REGISTER
@app.route("/register", methods=["POST"])
def register():

    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    cursor.execute(
        "INSERT INTO users(name,email,password) VALUES(?,?,?)",
        (name,email,password)
    )

    conn.commit()

    return redirect("/login")


# LOGIN CHECK
@app.route("/logincheck", methods=["POST"])
def logincheck():

    email = request.form['email']
    password = request.form['password']

    # ADMIN LOGIN
    if email == "admin@gmail.com" and password == "admin123":
        return redirect("/admin")

    cursor.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email,password)
    )

    user = cursor.fetchone()

    if user:
        session["user"] = user[1]
        return redirect("/courses")
    else:
        return "Invalid Login"


# STUDENT COURSES
@app.route("/courses")
def courses():

    if "user" not in session:
        return redirect("/login")

    view = request.args.get("view")

    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()

    return render_template("courses.html", courses=courses, view=view)


# LESSON PAGE
@app.route("/lesson/<course_id>")
def lesson(course_id):

    cursor.execute("SELECT * FROM lessons WHERE course_id=?", (course_id,))
    lessons = cursor.fetchall()

    return render_template("lesson.html", lessons=lessons)


# QUIZ PAGE
@app.route("/quiz/<lesson_id>")
def quiz(lesson_id):

    cursor.execute("SELECT * FROM quiz WHERE lesson_id=?", (lesson_id,))
    quiz = cursor.fetchone()

    return render_template("quiz.html", quiz=quiz)


# ADMIN PANEL
@app.route("/admin")
def admin():

    view = request.args.get("view")

    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    cursor.execute("SELECT * FROM lessons")
    lessons = cursor.fetchall()

    return render_template(
        "admin.html",
        courses=courses,
        users=users,
        lessons=lessons,
        view=view
    )


# ADD COURSE
@app.route("/addcourse", methods=["POST"])
def addcourse():

    name = request.form['course']
    desc = request.form['description']

    cursor.execute(
        "INSERT INTO courses(course,description) VALUES(?,?)",
        (name,desc)
    )

    conn.commit()

    return redirect("/admin")


# DELETE COURSE
@app.route("/delete/<id>")
def delete(id):

    cursor.execute("DELETE FROM courses WHERE id=?", (id,))
    conn.commit()

    return redirect("/admin")


# UPDATE COURSE
@app.route("/update/<id>", methods=["POST"])
def update(id):

    name = request.form['course']
    desc = request.form['description']

    cursor.execute(
        "UPDATE courses SET course=?, description=? WHERE id=?",
        (name,desc,id)
    )

    conn.commit()

    return redirect("/admin")


# ADD LESSON
@app.route("/addlesson", methods=["POST"])
def addlesson():

    course_id = request.form['course_id']
    title = request.form['title']
    content = request.form['content']

    cursor.execute(
        "INSERT INTO lessons(course_id,title,content) VALUES(?,?,?)",
        (course_id,title,content)
    )

    conn.commit()

    return redirect("/admin?view=lessons")


# DELETE LESSON
@app.route("/deletelesson/<id>")
def deletelesson(id):

    cursor.execute("DELETE FROM lessons WHERE id=?", (id,))
    conn.commit()

    return redirect("/admin?view=lessons")


# ADD QUIZ
@app.route("/addquiz", methods=["POST"])
def addquiz():

    lesson_id = request.form['lesson_id']
    question = request.form['question']
    o1 = request.form['option1']
    o2 = request.form['option2']
    o3 = request.form['option3']
    o4 = request.form['option4']
    ans = request.form['answer']

    cursor.execute("""
    INSERT INTO quiz(lesson_id,question,option1,option2,option3,option4,answer)
    VALUES(?,?,?,?,?,?,?)
    """,(lesson_id,question,o1,o2,o3,o4,ans))

    conn.commit()

    return redirect("/admin")


# CERTIFICATE DOWNLOAD
@app.route("/certificate")
def certificate():

    name = session["user"]

    file = open("certificate.txt","w")
    file.write("JovilRapidLearn Certificate\n\n")
    file.write("This certificate is awarded to\n")
    file.write(name + "\n\n")
    file.write("For completing the course.")
    file.close()

    return send_file("certificate.txt", as_attachment=True)


# LOGOUT
@app.route("/logout")
def logout():

    session.pop("user", None)
    return redirect("/")


app.run(debug=True)
