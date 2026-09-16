from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

# ---------------- DATABASE ----------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "library.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    conn = get_db()

    # Books table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Available',
            issued_to INTEGER
        )
    """)

    # Members table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# IMPORTANT:
# Create database when Flask/Gunicorn starts
create_database()


# ---------------- HOME ----------------

@app.route("/")
def home():
    conn = get_db()

    total_books = conn.execute(
        "SELECT COUNT(*) FROM books"
    ).fetchone()[0]

    available_books = conn.execute(
        "SELECT COUNT(*) FROM books WHERE status='Available'"
    ).fetchone()[0]

    issued_books = conn.execute(
        "SELECT COUNT(*) FROM books WHERE status='Issued'"
    ).fetchone()[0]

    total_members = conn.execute(
        "SELECT COUNT(*) FROM members"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        total_books=total_books,
        available_books=available_books,
        issued_books=issued_books,
        total_members=total_members
    )


# ---------------- ADD BOOK ----------------

@app.route("/add-book", methods=["GET", "POST"])
def add_book():

    if request.method == "POST":

        title = request.form["title"]
        author = request.form["author"]

        conn = get_db()

        conn.execute(
            "INSERT INTO books (title, author) VALUES (?, ?)",
            (title, author)
        )

        conn.commit()
        conn.close()

        return redirect("/books")

    return render_template("add_book.html")


# ---------------- VIEW BOOKS ----------------

@app.route("/books")
def books():

    conn = get_db()

    books = conn.execute("""
        SELECT books.*, members.name AS member_name
        FROM books
        LEFT JOIN members
        ON books.issued_to = members.id
        ORDER BY books.id DESC
    """).fetchall()

    members = conn.execute(
        "SELECT * FROM members ORDER BY name"
    ).fetchall()

    conn.close()

    return render_template(
        "books.html",
        books=books,
        members=members
    )


# ---------------- DELETE BOOK ----------------

@app.route("/delete-book/<int:book_id>")
def delete_book(book_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM books WHERE id=?",
        (book_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/books")


# ---------------- ADD MEMBER ----------------

@app.route("/add-member", methods=["GET", "POST"])
def add_member():

    if request.method == "POST":

        name = request.form["name"]
        phone = request.form["phone"]

        conn = get_db()

        conn.execute(
            "INSERT INTO members (name, phone) VALUES (?, ?)",
            (name, phone)
        )

        conn.commit()
        conn.close()

        return redirect("/members")

    return render_template("add_member.html")


# ---------------- VIEW MEMBERS ----------------

@app.route("/members")
def members():

    conn = get_db()

    members = conn.execute("""
        SELECT * FROM members
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "members.html",
        members=members
    )


# ---------------- REMOVE MEMBER ----------------

@app.route("/remove-member/<int:member_id>")
def remove_member(member_id):

    conn = get_db()

    issued_book = conn.execute(
        "SELECT * FROM books WHERE issued_to=?",
        (member_id,)
    ).fetchone()

    if issued_book:

        conn.close()

        return """
        <script>
            alert("This member has an issued book. Return the book first.");
            window.location.href="/members";
        </script>
        """

    conn.execute(
        "DELETE FROM members WHERE id=?",
        (member_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/members")


# ---------------- ISSUE BOOK ----------------

@app.route("/issue-book/<int:book_id>", methods=["POST"])
def issue_book(book_id):

    member_id = request.form["member_id"]

    conn = get_db()

    book = conn.execute(
        "SELECT * FROM books WHERE id=?",
        (book_id,)
    ).fetchone()

    if book and book["status"] == "Available":

        conn.execute("""
            UPDATE books
            SET status='Issued',
                issued_to=?
            WHERE id=?
        """, (member_id, book_id))

        conn.commit()

    conn.close()

    return redirect("/books")


# ---------------- RETURN BOOK ----------------

@app.route("/return-book/<int:book_id>")
def return_book(book_id):

    conn = get_db()

    conn.execute("""
        UPDATE books
        SET status='Available',
            issued_to=NULL
        WHERE id=?
    """, (book_id,))

    conn.commit()
    conn.close()

    return redirect("/books")


# ---------------- START APPLICATION ----------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
