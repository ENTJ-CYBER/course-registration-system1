import sqlite3
import os
from datetime import datetime
from types import SimpleNamespace

from flask import (
    Flask,
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from markupsafe import Markup, escape

app = Flask(__name__)
app.secret_key = "auaf_secret_key"


# =========================
# DATABASE HELPERS
# =========================

def get_db_connection():
    import os
    db_path = os.path.join(os.path.dirname(__file__), "database.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def table_exists(table_name):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    conn.close()
    return row is not None


def get_columns(table_name):
    if not table_exists(table_name):
        return []
    conn = get_db_connection()
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    conn.close()
    return [row["name"] for row in rows]


def first_existing(row, names, default=None):
    if row is None:
        return default
    for name in names:
        if name in row.keys():
            return row[name]
    return default


def parse_date(value):
    if not value:
        return datetime.now()

    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass

    return datetime.now()


# =========================
# FAKE current_user
# =========================
class CurrentUser:
    @property
    def is_authenticated(self):
        return "username" in session

    @property
    def is_admin(self):
        return session.get("role") == "admin"

    @property
    def full_name(self):
        return session.get("full_name") or session.get("username") or "User"


@app.context_processor
def inject_globals():
    return {
        "current_user": CurrentUser(),
    }


# =========================
# FAKE FORM HELPERS
# =========================
class FakeLabel:
    def __init__(self, text):
        self.text = text

    def __call__(self, **attrs):
        attrs_html = "".join(
            f' {k}="{escape(v)}"' for k, v in attrs.items() if v is not None
        )
        return Markup(f"<label{attrs_html}>{escape(self.text)}</label>")


class FakeInputField:
    def __init__(self, name, label_text, input_type="text", value="", errors=None):
        self.name = name
        self.label = FakeLabel(label_text)
        self.input_type = input_type
        self.value = value
        self.errors = errors or []

    def __call__(self, **attrs):
        attrs = dict(attrs)
        if "name" not in attrs:
            attrs["name"] = self.name
        if "id" not in attrs:
            attrs["id"] = self.name
        if self.input_type != "password" and "value" not in attrs:
            attrs["value"] = self.value if self.value is not None else ""
        attrs_html = "".join(
            f' {k}="{escape(v)}"' for k, v in attrs.items() if v is not None
        )
        return Markup(f'<input type="{self.input_type}"{attrs_html}>')


class FakeCheckboxField:
    def __init__(self, name, label_text, checked=False, errors=None):
        self.name = name
        self.label = FakeLabel(label_text)
        self.checked = checked
        self.errors = errors or []

    def __call__(self, **attrs):
        attrs = dict(attrs)
        if "name" not in attrs:
            attrs["name"] = self.name
        if "id" not in attrs:
            attrs["id"] = self.name
        if "value" not in attrs:
            attrs["value"] = "1"
        checked_html = " checked" if self.checked else ""
        attrs_html = "".join(
            f' {k}="{escape(v)}"' for k, v in attrs.items() if v is not None
        )
        return Markup(f'<input type="checkbox"{checked_html}{attrs_html}>')


class FakeSubmitField:
    def __init__(self, text):
        self.text = text

    def __call__(self, **attrs):
        attrs = dict(attrs)
        if "type" not in attrs:
            attrs["type"] = "submit"
        attrs_html = "".join(
            f' {k}="{escape(v)}"' for k, v in attrs.items() if v is not None
        )
        return Markup(f"<button{attrs_html}>{escape(self.text)}</button>")


class LoginForm:
    def __init__(self):
        self.username = FakeInputField("email", "Email", input_type="email")
        self.password = FakeInputField("password", "Password", input_type="password")
        self.remember_me = FakeCheckboxField("remember_me", "Remember Me")

    def hidden_tag(self):
        return Markup("")


class RegisterForm:
    def __init__(self):
        self.full_name = FakeInputField("full_name", "Full Name")
        self.username = FakeInputField("username", "Username")
        self.email = FakeInputField("email", "Email", input_type="email")
        self.student_id = FakeInputField("student_id", "Student ID")
        self.department = FakeInputField("department", "Department")
        self.password = FakeInputField("password", "Password", input_type="password")
        self.password2 = FakeInputField("password2", "Confirm Password", input_type="password")

    def hidden_tag(self):
        return Markup("")


class StudentEditForm:
    def __init__(self, student=None):
        self.full_name = FakeInputField(
            "full_name",
            "Full Name",
            value=getattr(student, "full_name", "")
        )
        self.email = FakeInputField(
            "email",
            "Email",
            input_type="email",
            value=getattr(student, "email", "")
        )
        self.student_id = FakeInputField(
            "student_id",
            "Student ID",
            value=getattr(student, "student_id", "")
        )
        self.department = FakeInputField(
            "department",
            "Department",
            value=getattr(student, "department", "")
        )
        self.is_active = FakeCheckboxField(
            "is_active",
            "Active Account",
            checked=bool(getattr(student, "is_active", 1))
        )
        self.submit = FakeSubmitField("Save Changes")

    def hidden_tag(self):
        return Markup("")


# =========================
# HELPERS
# =========================
def get_user_full_name(user_row):
    username = first_existing(user_row, ["username"], "User")
    email = first_existing(user_row, ["email"], "")

    if table_exists("students") and email:
        student_cols = get_columns("students")
        if "email" in student_cols:
            conn = get_db_connection()
            student = conn.execute(
                "SELECT * FROM students WHERE email = ?",
                (email,),
            ).fetchone()
            conn.close()
            if student:
                return first_existing(student, ["full_name", "name"], username)

    return username


def get_course_name_column():
    cols = get_columns("courses")
    if "course_name" in cols:
        return "course_name"
    if "name" in cols:
        return "name"
    return None


def get_course_code_column():
    cols = get_columns("courses")
    if "course_code" in cols:
        return "course_code"
    if "code" in cols:
        return "code"
    return None


def get_student_name_column():
    cols = get_columns("students")
    if "full_name" in cols:
        return "full_name"
    if "name" in cols:
        return "name"
    return None


def get_enrollment_date_column():
    cols = get_columns("enrollments")
    for col in ["enrolled_at", "created_at", "date"]:
        if col in cols:
            return col
    return None


def get_student_active_value(row):
    if row is None:
        return 1

    keys = row.keys()
    if "is_active" in keys:
        return row["is_active"]
    if "active" in keys:
        return row["active"]
    if "status" in keys:
        status = str(row["status"]).lower()
        return 0 if status in ["inactive", "disabled"] else 1

    return 1


def get_enrolled_count(course_id):
    if not table_exists("enrollments"):
        return 0

    conn = get_db_connection()
    enroll_cols = get_columns("enrollments")

    if "status" in enroll_cols:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM enrollments WHERE course_id = ? AND (status IS NULL OR status != 'dropped')",
            (course_id,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM enrollments WHERE course_id = ?",
            (course_id,),
        ).fetchone()

    conn.close()
    return row["total"] if row else 0


def make_course_object(row):
    course_name = first_existing(row, ["course_name", "name"], "")
    course_code = first_existing(row, ["course_code", "code"], "")
    capacity = first_existing(row, ["capacity"], 0)

    try:
        capacity = int(capacity) if capacity is not None else 0
    except Exception:
        capacity = 0

    enrolled_count = get_enrolled_count(row["id"])
    available_seats = max(capacity - enrolled_count, 0)

    return SimpleNamespace(
        id=row["id"],
        course_name=course_name,
        name=course_name,
        course_code=course_code,
        instructor=first_existing(row, ["instructor"], ""),
        department=first_existing(row, ["department"], ""),
        schedule=first_existing(row, ["schedule"], ""),
        credits=first_existing(row, ["credits"], ""),
        capacity=capacity,
        description=first_existing(row, ["description"], ""),
        enrolled_count=enrolled_count,
        available_seats=available_seats,
        is_full=available_seats <= 0,
        is_available=True,
    )


def get_course_by_id(course_id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return make_course_object(row)


class EnrollmentList:
    def __init__(self, items):
        self.items = items

    def order_by(self, field_name):
        reverse = False
        key_name = field_name

        if field_name.startswith("-"):
            reverse = True
            key_name = field_name[1:]

        sorted_items = sorted(
            self.items,
            key=lambda x: getattr(x, key_name, datetime.min) or datetime.min,
            reverse=reverse
        )
        return EnrollmentList(sorted_items)

    def all(self):
        return self.items


def get_student_by_id(student_id):
    if not table_exists("students"):
        return None

    conn = get_db_connection()

    student_row = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,),
    ).fetchone()

    if not student_row:
        conn.close()
        return None

    user_row = None
    if table_exists("users") and "user_id" in student_row.keys():
        user_row = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (student_row["user_id"],),
        ).fetchone()

    enrollments = []
    active_enrollments = []

    rows = conn.execute("""
        SELECT e.id AS enrollment_id, e.status, e.course_id,
               c.id AS real_course_id,
               c.course_code, c.course_name, c.credits, c.schedule
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.student_id = ?
        ORDER BY e.id DESC
    """, (student_id,)).fetchall()

    for row in rows:
        status = row["status"] or "enrolled"

        course_obj = SimpleNamespace(
            id=row["real_course_id"],
            course_code=row["course_code"],
            name=row["course_name"],
            credits=row["credits"],
            schedule=row["schedule"],
        )

        enrollment_obj = SimpleNamespace(
            id=row["enrollment_id"],
            status=status,
            grade=None,
            enrolled_at=datetime.now(),
            course=course_obj,
        )

        enrollments.append(enrollment_obj)

        if status.lower() != "dropped":
            active_enrollments.append(enrollment_obj)

    conn.close()

    return SimpleNamespace(
        id=student_row["id"],
        full_name=student_row["full_name"],
        student_id=f"S{student_row['id']:04d}",
        department=student_row["department"] or "Not Assigned",
        username=user_row["username"] if user_row else "N/A",
        email=user_row["email"] if user_row and "email" in user_row.keys() else "N/A",
        created_at=datetime.now(),
        is_active=True,
        active_enrollments=active_enrollments,
        enrollments=EnrollmentList(enrollments),
    )

# =========================
# BLUEPRINTS
# =========================
auth_bp = Blueprint("auth", __name__)
main_bp = Blueprint("main", __name__)
courses_bp = Blueprint("courses", __name__, url_prefix="/courses")
students_bp = Blueprint("students", __name__, url_prefix="/students")
enrollment_bp = Blueprint("enrollment", __name__, url_prefix="/enrollment")


# =========================
# ROOT
# =========================
@app.route("/")
def root():
    return redirect(url_for("auth.login"))

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()

        conn.close()

        if user:
            role = first_existing(user, ["role"], "student")

            session["user_id"] = user["id"]
            session["username"] = first_existing(user, ["username"], "")
            session["role"] = role
            session["full_name"] = get_user_full_name(user)
            session["email"] = first_existing(user, ["email"], "")

            if role == "admin":
                return redirect(url_for("main.dashboard"))
            else:
                return redirect(url_for("main.student_dashboard"))

        flash("Invalid email or password", "danger")
        return redirect(url_for("auth.login"))

    return render_template("auth/login.html", form=form)



@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    form = RegisterForm()

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        department = request.form.get("department", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()

        try:
            conn.execute("""
                INSERT INTO users (username, password, role, email)
                VALUES (?, ?, 'student', ?)
            """, (username, password, email))

            user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            conn.execute("""
                INSERT INTO students (user_id, full_name, department)
                VALUES (?, ?, ?)
            """, (user_id, full_name, department))

            conn.commit()

        finally:
            conn.close()

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)

# =========================
# DASHBOARD
# =========================
@main_bp.route("/dashboard")
def dashboard():

    
    if session.get("role") != "admin":
        return redirect(url_for("main.student_dashboard"))

    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    total_students = 0
    total_courses = 0
    total_enrollments = 0

    if table_exists("students"):
        total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]

    if table_exists("courses"):
        total_courses = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]

    if table_exists("enrollments"):
        total_enrollments = conn.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0]

    stats = {
        "total_students": total_students,
        "total_courses": total_courses,
        "active_courses": total_courses,
        "total_enrollments": total_enrollments,
    }

    recent_enrollments = []

    if table_exists("students") and table_exists("courses") and table_exists("enrollments"):
        course_name_col = get_course_name_column()
        course_code_col = get_course_code_column()
        student_name_col = get_student_name_column()
        date_col = get_enrollment_date_column()
        enroll_cols = get_columns("enrollments")

        status_select = "enrollments.status AS status" if "status" in enroll_cols else "'enrolled' AS status"
        grade_select = "enrollments.grade AS grade" if "grade" in enroll_cols else "NULL AS grade"
        date_select = f"enrollments.{date_col} AS enrolled_at" if date_col else "NULL AS enrolled_at"
        student_name_select = f"students.{student_name_col} AS student_name" if student_name_col else "'Unknown Student' AS student_name"
        course_name_select = f"courses.{course_name_col} AS course_name" if course_name_col else "'Unnamed Course' AS course_name"
        course_code_select = f"courses.{course_code_col} AS course_code" if course_code_col else "'' AS course_code"

        query = f"""
            SELECT
                enrollments.id AS enrollment_id,
                {status_select},
                {grade_select},
                {date_select},
                students.id AS student_id,
                {student_name_select},
                courses.id AS course_id,
                {course_code_select},
                {course_name_select}
            FROM enrollments
            JOIN students ON enrollments.student_id = students.id
            JOIN courses ON enrollments.course_id = courses.id
            ORDER BY enrollments.id DESC
            LIMIT 5
        """

        rows = conn.execute(query).fetchall()

        for row in rows:
            recent_enrollments.append(
                SimpleNamespace(
                    id=row["enrollment_id"],
                    status=row["status"] or "enrolled",
                    grade=row["grade"],
                    enrolled_at=parse_date(row["enrolled_at"]),
                    student=SimpleNamespace(
                        id=row["student_id"],
                        full_name=row["student_name"],
                    ),
                    course=SimpleNamespace(
                        id=row["course_id"],
                        course_code=row["course_code"],
                        name=row["course_name"],
                    ),
                )
            )

    conn.close()

    return render_template(
        "main/admin_dashboard.html",
        stats=stats,
        recent_enrollments=recent_enrollments,
    )
# =========================
# STUDENT DASHBOARD
# =========================
@main_bp.route("/student-dashboard")
def student_dashboard():

    if "username" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "student":
        return redirect(url_for("main.dashboard"))

    conn = get_db_connection()
    print("SESSION USER ID:", session.get("user_id"))
    
    student = conn.execute("""
        SELECT * FROM students
        WHERE user_id = ?
    """, (session.get("user_id"),)).fetchone()
    print("STUDENT ROW:", student)

    if not student:
        conn.close()
        return "Student profile not found"

    # enrolled courses
    enrolled_courses = conn.execute("""
    SELECT c.id,
       c.course_name,
       c.course_code,
       c.instructor,
       c.credits,
       c.schedule
FROM courses c
JOIN enrollments e ON c.id = e.course_id
    WHERE e.student_id = ?
    AND e.status = 'enrolled'
""", (student["id"],)).fetchall()
    print("ENROLLED COURSES:", enrolled_courses)

    # all courses
    all_courses = conn.execute("""
        SELECT * FROM courses
    """).fetchall()

    conn.close()

    active_tab = request.args.get("tab", "enrolled")

    return render_template(
        "main/student_dashboard.html",
        student=student,
        enrolled_courses=enrolled_courses,
        all_courses=all_courses,
        active_tab=active_tab
    )
# =========================
# COURSES
# =========================
@courses_bp.route("/")
@courses_bp.route("/")
def list_courses():
    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    rows = conn.execute("SELECT * FROM courses ORDER BY id DESC").fetchall()
    courses = [make_course_object(row) for row in rows]

    enrolled_rows = conn.execute("""
        SELECT course_id 
        FROM enrollments 
        WHERE student_id = (
            SELECT id FROM students WHERE user_id = ?
        )
        AND status = 'enrolled'
    """, (session["user_id"],)).fetchall()

    enrolled_ids = [row["course_id"] for row in enrolled_rows]

    conn.close()

    query = request.args.get("query", "").strip().lower()
    department = request.args.get("department", "").strip().lower()
    instructor = request.args.get("instructor", "").strip().lower()

    filtered = []

    for course in courses:
        if query and query not in (course.course_name or "").lower() and query not in (course.course_code or "").lower():
            continue
        if department and department not in (course.department or "").lower():
            continue
        if instructor and instructor not in (course.instructor or "").lower():
            continue

        filtered.append(course)

    return render_template(
        "courses/list.html",
        courses=filtered,
        enrolled_ids=enrolled_ids
    )


@courses_bp.route("/add", methods=["GET", "POST"])
def add_course():
    if "username" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        flash("Only admin can add courses.", "danger")
        return redirect(url_for("courses.list_courses"))

    if request.method == "POST":
        course_code = request.form.get("course_code", "").strip()
        course_name = request.form.get("course_name", "").strip()
        instructor = request.form.get("instructor", "").strip()
        department = request.form.get("department", "").strip()
        schedule = request.form.get("schedule", "").strip()
        credits = request.form.get("credits", "").strip()
        capacity = request.form.get("capacity", "").strip()
        description = request.form.get("description", "").strip()

        conn = get_db_connection()
        cols = get_columns("courses")

        if "course_code" in cols:
            existing = conn.execute(
                "SELECT * FROM courses WHERE course_code = ?",
                (course_code,),
            ).fetchone()
            if existing:
                conn.close()
                flash("Course code already exists.", "danger")
                return redirect(url_for("courses.add_course"))

        insert_data = {}

        if "course_code" in cols:
            insert_data["course_code"] = course_code
        elif "code" in cols:
            insert_data["code"] = course_code

        if "course_name" in cols:
            insert_data["course_name"] = course_name
        elif "name" in cols:
            insert_data["name"] = course_name

        if "instructor" in cols:
            insert_data["instructor"] = instructor
        if "department" in cols:
            insert_data["department"] = department
        if "schedule" in cols:
            insert_data["schedule"] = schedule
        if "credits" in cols:
            insert_data["credits"] = credits
        if "capacity" in cols:
            insert_data["capacity"] = capacity
        if "description" in cols:
            insert_data["description"] = description

        columns_sql = ", ".join(insert_data.keys())
        placeholders = ", ".join(["?"] * len(insert_data))
        values = tuple(insert_data.values())

        conn.execute(
            f"INSERT INTO courses ({columns_sql}) VALUES ({placeholders})",
            values,
        )
        conn.commit()
        conn.close()

        flash("Course added successfully.", "success")
        return redirect(url_for("courses.list_courses"))

    return render_template("courses/form.html", course=None)


@courses_bp.route("/<int:course_id>")
def view_course(course_id):
    if "username" not in session:
        return redirect(url_for("auth.login"))

    course = get_course_by_id(course_id)
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("courses.list_courses"))

    return render_template("courses/detail.html", course=course)


@courses_bp.route("/<int:course_id>/edit", methods=["GET", "POST"])
def edit_course(course_id):
    if "username" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        flash("Only admin can edit courses.", "danger")
        return redirect(url_for("courses.list_courses"))

    course = get_course_by_id(course_id)
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("courses.list_courses"))

    if request.method == "POST":
        course_code = request.form.get("course_code", "").strip()
        course_name = request.form.get("course_name", "").strip()
        instructor = request.form.get("instructor", "").strip()
        department = request.form.get("department", "").strip()
        schedule = request.form.get("schedule", "").strip()
        credits = request.form.get("credits", "").strip()
        capacity = request.form.get("capacity", "").strip()
        description = request.form.get("description", "").strip()

        conn = get_db_connection()
        cols = get_columns("courses")

        code_col = "course_code" if "course_code" in cols else ("code" if "code" in cols else None)
        if code_col:
            existing = conn.execute(
                f"SELECT * FROM courses WHERE {code_col} = ? AND id != ?",
                (course_code, course_id),
            ).fetchone()

            if existing:
                conn.close()
                flash("Another course already uses this course code.", "danger")
                return redirect(url_for("courses.edit_course", course_id=course_id))

        update_data = []

        if "course_code" in cols:
            update_data.append(("course_code", course_code))
        elif "code" in cols:
            update_data.append(("code", course_code))

        if "course_name" in cols:
            update_data.append(("course_name", course_name))
        elif "name" in cols:
            update_data.append(("name", course_name))

        if "instructor" in cols:
            update_data.append(("instructor", instructor))
        if "department" in cols:
            update_data.append(("department", department))
        if "schedule" in cols:
            update_data.append(("schedule", schedule))
        if "credits" in cols:
            update_data.append(("credits", credits))
        if "capacity" in cols:
            update_data.append(("capacity", capacity))
        if "description" in cols:
            update_data.append(("description", description))

        set_clause = ", ".join([f"{col} = ?" for col, _ in update_data])
        values = [value for _, value in update_data]
        values.append(course_id)

        conn.execute(
            f"UPDATE courses SET {set_clause} WHERE id = ?",
            values,
        )
        conn.commit()
        conn.close()

        flash("Course updated successfully.", "success")
        return redirect(url_for("courses.view_course", course_id=course_id))

    return render_template("courses/form.html", course=course)


@courses_bp.route("/<int:course_id>/delete", methods=["POST"])
def delete_course(course_id):
    if "username" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        flash("Only admin can delete courses.", "danger")
        return redirect(url_for("courses.list_courses"))

    conn = get_db_connection()
    conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()

    flash("Course deleted successfully.", "success")
    return redirect(url_for("courses.list_courses"))


# =========================
# STUDENTS
# =========================
@students_bp.route("/")
def list_students():
    if "username" not in session:
        return redirect(url_for("auth.login"))

    if not table_exists("students"):
        return render_template("students/list.html", students=[], search="")

    search = request.args.get("search", "").strip()
    search_lower = search.lower()

    conn = get_db_connection()
    student_rows = conn.execute("SELECT * FROM students ORDER BY id DESC").fetchall()

    enrolled_counts = {}
    if table_exists("enrollments"):
        enroll_cols = get_columns("enrollments")
        if "status" in enroll_cols:
            count_rows = conn.execute(
                """
                SELECT student_id, COUNT(*) AS total
                FROM enrollments
                WHERE status IS NULL OR status != 'dropped'
                GROUP BY student_id
                """
            ).fetchall()
        else:
            count_rows = conn.execute(
                """
                SELECT student_id, COUNT(*) AS total
                FROM enrollments
                GROUP BY student_id
                """
            ).fetchall()

        enrolled_counts = {row["student_id"]: row["total"] for row in count_rows}

    students = []

    for row in student_rows:
        full_name = first_existing(row, ["full_name", "name"], "")
        email = first_existing(row, ["email"], "")
        student_code = first_existing(row, ["student_id"], "")
        department = first_existing(row, ["department"], "")

        haystack = f"{full_name} {email} {student_code}".lower()
        if search_lower and search_lower not in haystack:
            continue

        students.append(
            SimpleNamespace(
                id=row["id"],
                full_name=full_name,
                email=email,
                student_id=student_code or f"S{row['id']:04d}",
                department=department or "Not Assigned",
                is_active=bool(get_student_active_value(row)),
                enrolled_count=enrolled_counts.get(row["id"], 0),
            )
        )

    conn.close()

    return render_template("students/list.html", students=students, search=search)


@students_bp.route("/<int:student_id>")
def view_student(student_id):
    if "username" not in session:
        return redirect(url_for("auth.login"))

    student = get_student_by_id(student_id)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("students.list_students"))

    return render_template("students/detail.html", student=student)


@students_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
def edit_student(student_id):
    if "username" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        flash("Only admin can edit student records.", "danger")
        return redirect(url_for("students.list_students"))

    student = get_student_by_id(student_id)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("students.list_students"))

    form = StudentEditForm(student)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        student_code = request.form.get("student_id", "").strip()
        department = request.form.get("department", "").strip()
        is_active = 1 if request.form.get("is_active") else 0

        old_email = student.email

        conn = get_db_connection()
        student_cols = get_columns("students")

        update_parts = []
        update_values = []

        if "full_name" in student_cols:
            update_parts.append("full_name = ?")
            update_values.append(full_name)
        elif "name" in student_cols:
            update_parts.append("name = ?")
            update_values.append(full_name)

        if "email" in student_cols:
            update_parts.append("email = ?")
            update_values.append(email)

        if "student_id" in student_cols:
            update_parts.append("student_id = ?")
            update_values.append(student_code)

        if "department" in student_cols:
            update_parts.append("department = ?")
            update_values.append(department)

        if "is_active" in student_cols:
            update_parts.append("is_active = ?")
            update_values.append(is_active)

        if update_parts:
            update_values.append(student_id)
            conn.execute(
                f"UPDATE students SET {', '.join(update_parts)} WHERE id = ?",
                tuple(update_values),
            )

        if table_exists("users") and old_email:
            user_cols = get_columns("users")
            if "email" in user_cols:
                conn.execute(
                    "UPDATE users SET email = ? WHERE email = ?",
                    (email, old_email),
                )

        conn.commit()
        conn.close()

        flash("Student updated successfully.", "success")
        return redirect(url_for("students.view_student", student_id=student_id))

    return render_template("students/edit.html", student=student, form=form)


# =========================
# ENROLLMENT
# =========================
enrollment_bp = Blueprint("enrollment", __name__, url_prefix="/enrollment")

def get_student_id():
    user_id = session.get("user_id")

    conn = get_db_connection()
    student = conn.execute(
        "SELECT id FROM students WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()

    return student["id"] if student else None

@enrollment_bp.route("/courses")
def student_courses():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()

    return render_template("students/courses.html", courses=rows)


@enrollment_bp.route("/search")
def search_courses():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    q = request.args.get("q", "").strip().lower()

    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()

    results = []

    for c in rows:
        if (
            q in str(c["course_name"]).lower()
            or q in str(c["course_code"]).lower()
            or q in str(c["instructor"]).lower()
            or q in str(c["department"]).lower()
        ):
            results.append(c)

    return render_template("course/list.html", courses=results)


@enrollment_bp.route("/enroll/<int:course_id>", methods=["POST"])
def enroll(course_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    student_id = get_student_id()

    if not student_id:
        flash("Student profile not found.", "danger")
        return redirect(url_for("enrollment.student_courses"))

    conn = get_db_connection()

    existing = conn.execute(
        """
        SELECT 1 FROM enrollments
        WHERE student_id = ? AND course_id = ? AND status = 'enrolled'
        """,
        (student_id, course_id)
    ).fetchone()

    if existing:
        conn.close()
        flash("You are already enrolled in this course.", "warning")
        return redirect(request.referrer)

    conn.execute(
        """
        INSERT INTO enrollments (student_id, course_id, status)
        VALUES (?, ?, 'enrolled')
        """,
        (student_id, course_id)
    )

    conn.commit()
    conn.close()

    flash("Enrolled successfully!", "success")
    return redirect(url_for("enrollment.history"))


@enrollment_bp.route("/drop/<int:course_id>", methods=["POST"])
def drop(course_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    student_id = get_student_id()

    if not student_id:
        flash("Student profile not found.", "danger")
        return redirect(url_for("enrollment.student_courses"))

    conn = get_db_connection()

    conn.execute(
        """
        UPDATE enrollments
        SET status = 'dropped'
        WHERE student_id = ? AND course_id = ? AND status = 'enrolled'
        """,
        (student_id, course_id)
    )

    conn.commit()
    conn.close()

    flash("Course dropped successfully.", "info")
    return redirect(url_for("main.student_dashboard"))


@enrollment_bp.route("/history")
def history():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    student_id = get_student_id()

    if not student_id:
        flash("Student profile not found.", "danger")
        return redirect(url_for("enrollment.student_courses"))

    conn = get_db_connection()

    rows = conn.execute("""
        SELECT e.id, e.status, c.course_name, c.course_code
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.student_id = ?
        ORDER BY e.id DESC
    """, (student_id,)).fetchall()

    conn.close()

    return render_template("students/history.html", enrollments=rows)


# =========================
# REGISTER BLUEPRINTS
# =========================
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(main_bp, url_prefix="")
app.register_blueprint(courses_bp)
app.register_blueprint(students_bp)
app.register_blueprint(enrollment_bp)


if __name__ == "__main__":
    app.run(debug=True)