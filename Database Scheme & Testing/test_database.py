import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

def test_users():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    assert len(users) > 0
    print("Users test passed")



def test_courses():
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    assert len(courses) > 0
    print("Courses test passed")

def test_students():
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    assert len(students) > 0
    print("Students test passed")



def test_enrollments():
    cursor.execute("SELECT * FROM enrollments")
    enrollments = cursor.fetchall()
    assert len(enrollments) > 0
    print("Enrollments test passed")



test_users()
test_courses()
test_students()
test_enrollments()



conn.close()