from flask import Flask, flash, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import sqlite3
import random
from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Create tables
conn = sqlite3.connect("database.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT,
    email TEXT,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    username TEXT,
    review TEXT,
    rating INTEGER,
    result TEXT
)
""")

conn.commit()
conn.close()
app = Flask(__name__)
app.secret_key = "supersecret"

model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# Create Database

@app.route("/")
def home():
    return render_template("home.html")

# USER REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?,?,?)",
                  (username, email, password))
        conn.commit()
        conn.close()

        # 🔥 VERY IMPORTANT
        session["user"] = username

        return redirect("/dashboard")

    return render_template("register.html")


# USER LOGIN
from werkzeug.security import check_password_hash

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT username, password FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['username'] = username
            return redirect('/home')
        else:
            flash("Invalid credentials")
            return render_template("login.html")

    return render_template("login.html")

@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        username = request.form["username"]
        new_password = request.form["new_password"]

        hashed_password = generate_password_hash(new_password)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("UPDATE users SET password=? WHERE username=?",
                  (hashed_password, username))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("forgot.html")
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        review = request.form["review"]
        data = vectorizer.transform([review])
        prediction = model.predict(data)[0]

        result = "Fake ❌" if prediction == 1 else "Genuine ✅"

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        rating = int(request.form.get("rating", 0))
        c.execute("INSERT INTO reviews VALUES (?,?,?,?)", (session["user"], review, rating, result))
        conn.commit()
        conn.close()

        return render_template("dashboard.html",  username=session["user"])

    return render_template("dashboard.html")
@app.route("/send_otp", methods=["GET", "POST"])
def send_otp():
    if request.method == "POST":
        session["otp"] = random.randint(1000, 9999)
        print("Your OTP is:", session["otp"])  # For testing

        return render_template("verify_otp.html")

    return render_template("send_otp.html")

# ADMIN LOGIN
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/admin_panel")
        else:
            return render_template("admin.html", error="Wrong Admin Credentials ❌")

    return render_template("admin.html")

@app.route("/admin_panel")
def admin_panel():
    if "admin" not in session:
        return redirect("/admin")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Search
    search = request.args.get("search")

    if search:
        c.execute("SELECT * FROM reviews WHERE review LIKE ?", ('%'+search+'%',))
    else:
        c.execute("SELECT * FROM reviews")

    reviews = c.fetchall()

    # Total Reviews
    c.execute("SELECT COUNT(*) FROM reviews")
    total_reviews = c.fetchone()[0]

    # Fake Reviews Count
    c.execute("SELECT COUNT(*) FROM reviews WHERE result='Fake ❌'")
    fake_reviews = c.fetchone()[0]

    # Fake Percentage
    fake_percentage = 0
    if total_reviews > 0:
        fake_percentage = round((fake_reviews / total_reviews) * 100, 2)

    # Average Rating Per User
    c.execute("SELECT username, AVG(rating) FROM reviews GROUP BY username")
    avg_ratings = c.fetchall()

    conn.close()

    return render_template("admin_panel.html",
                           reviews=reviews,
                           total_reviews=total_reviews,
                           fake_reviews=fake_reviews,
                           fake_percentage=fake_percentage,
                           avg_ratings=avg_ratings)
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
@app.route("/delete/<int:id>")
def delete(id):
    if "admin" not in session:
        return redirect("/admin")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM reviews WHERE rowid = ?", (id+1,))
    conn.commit()
    conn.close()

    return redirect("/admin_panel")
@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # ✅ Only fetch reviews of logged-in user
    c.execute("SELECT * FROM reviews WHERE username=?", (username,))
    reviews = c.fetchall()

    conn.close()

    return render_template("profile.html",
                           username=username,
                           reviews=reviews)
if __name__ == "__main__":
    app.run(debug=True)