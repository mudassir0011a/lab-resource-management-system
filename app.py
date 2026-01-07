from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session




app = Flask(__name__)
app.secret_key = "simple_secret_key"


# DB connection
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Create tables (run once automatically)
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resource_name TEXT,
        resource_type TEXT,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS allocations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        resource_id INTEGER,
        assigned_date TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- DASHBOARD ----------------
@app.route("/")
@app.route("/")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
    available = conn.execute(
        "SELECT COUNT(*) FROM resources WHERE status='available'"
    ).fetchone()[0]
    allocated = conn.execute(
        "SELECT COUNT(*) FROM resources WHERE status='allocated'"
    ).fetchone()[0]
    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        available=available,
        allocated=allocated
    )

    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
    available = conn.execute(
        "SELECT COUNT(*) FROM resources WHERE status='available'"
    ).fetchone()[0]
    allocated = conn.execute(
        "SELECT COUNT(*) FROM resources WHERE status='allocated'"
    ).fetchone()[0]
    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        available=available,
        allocated=allocated
    )
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if (username == "admin" and password == "admin123") or \
           (username == "staff" and password == "staff123"):
            session["logged_in"] = True
            session["user_role"] = username   # admin or staff
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# ---------------- ADD RESOURCE ----------------
@app.route("/add-resource", methods=["GET", "POST"])
def add_resource():
    if session.get("user_role") != "admin":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form["name"]
        rtype = request.form["type"]

        conn = get_db()
        conn.execute(
            "INSERT INTO resources (resource_name, resource_type, status) VALUES (?, ?, ?)",
            (name, rtype, "available")
        )
        conn.commit()
        conn.close()

        return redirect(url_for("view_resources"))

    return render_template("add_resource.html")


# ---------------- VIEW RESOURCES ----------------
@app.route("/resources")
def view_resources():
    conn = get_db()
    resources = conn.execute("SELECT * FROM resources").fetchall()
    conn.close()
    return render_template("view_resources.html", resources=resources)

# ---------------- ASSIGN / RELEASE ----------------
@app.route("/assign", methods=["GET", "POST"])
def assign_resource():
    conn = get_db()

    if request.method == "POST":
        user_id = request.form["user"]
        resource_id = request.form["resource"]

        conn.execute(
            "INSERT INTO allocations (user_id, resource_id, assigned_date) VALUES (?, ?, ?)",
            (user_id, resource_id, str(date.today()))
        )
        conn.execute(
            "UPDATE resources SET status='allocated' WHERE id=?",
            (resource_id,)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("view_resources"))

    users = conn.execute("SELECT * FROM users").fetchall()
    resources = conn.execute(
        "SELECT * FROM resources WHERE status='available'"
    ).fetchall()
    conn.close()

    return render_template(
        "assign_resource.html",
        users=users,
        resources=resources
    )
    
@app.route("/delete-resource/<int:resource_id>")
def delete_resource(resource_id):
    # Sirf admin delete kar sakta hai
    if session.get("user_role") != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db()

    # Safety: allocated resource delete na ho
    resource = conn.execute(
        "SELECT status FROM resources WHERE id=?",
        (resource_id,)
    ).fetchone()

    if resource and resource["status"] == "allocated":
        conn.close()
        return redirect(url_for("view_resources"))

    conn.execute(
        "DELETE FROM resources WHERE id=?",
        (resource_id,)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("view_resources"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/release/<int:resource_id>")
def release_resource(resource_id):
    conn = get_db()
    conn.execute(
        "UPDATE resources SET status='available' WHERE id=?",
        (resource_id,)
    )
    conn.execute(
        "DELETE FROM allocations WHERE resource_id=?",
        (resource_id,)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("view_resources"))

if __name__ == "__main__":
    app.run(debug=True)
