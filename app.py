from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, os

app = Flask(__name__)
app.secret_key = "mysecretkey"
DATABASE = "database.db"

# -------------------------
# Database Setup
# -------------------------
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                year INTEGER NOT NULL,
                image TEXT NOT NULL,
                added_by INTEGER NOT NULL,
                FOREIGN KEY (added_by) REFERENCES users (id)
            )
            """
        )
        conn.commit()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------
# Routes
# -------------------------
@app.route("/")
def index():
    conn = get_db_connection()
    books = conn.execute(
        """
        SELECT books.*, users.username AS added_by_name
        FROM books JOIN users ON books.added_by = users.id
        ORDER BY books.id DESC
        """
    ).fetchall()
    conn.close()
    return render_template("index.html", books=books)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists!", "danger")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/add-book", methods=["GET", "POST"])
def add_book():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        year = request.form["year"]
        image = request.form["image"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO books (title, author, year, image, added_by) VALUES (?, ?, ?, ?, ?)",
            (title, author, year, image, session["user_id"])
        )
        conn.commit()
        conn.close()
        flash("Book added successfully!", "success")
        return redirect(url_for("index"))

    return render_template("add_book.html")

@app.route("/book/<int:book_id>")
def book_detail(book_id):
    conn = get_db_connection()
    book = conn.execute(
        """
        SELECT books.*, users.username AS added_by_name
        FROM books JOIN users ON books.added_by = users.id
        WHERE books.id = ?
        """,
        (book_id,)
    ).fetchone()
    conn.close()
    if not book:
        return render_template("404.html"), 404
    return render_template("book_detail.html", book=book)

@app.route("/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    if "user_id" not in session:
        flash("Please login to delete books.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()

    if not book:
        conn.close()
        flash("Book not found.", "danger")
        return redirect(url_for("index"))

    if book["added_by"] != session["user_id"]:
        conn.close()
        flash("You are not authorized to delete this book.", "danger")
        return redirect(url_for("index"))

    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()

    flash("Book deleted successfully!", "success")
    return redirect(url_for("index"))

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
