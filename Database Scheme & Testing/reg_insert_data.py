import sqlite3
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# 2 users admin and student
cursor.execute("""
INSERT INTO users (username, email, password, role)
VALUES ('admin', 'admin1@gmail.com', '1111', 'admin')
""")
cursor.execute("""
INSERT INTO users (username, email, password, role)
VALUES ('student1', 'student1@gmail.com', '2222', 'student')
""")

# student insertion
cursor.execute("""
INSERT INTO students (user_id, full_name, department)
VALUES (001, 'Ahmad Ahmadi', 'Computer Science')
""")
# course insertion
cursor.execute("""
INSERT INTO courses (course_name,  instructor, credits, schedule, department, capacity)
VALUES ('Intro to Python',   'Dr. Yousof', 3, 'Sunday 6:30 PM', 'Computer Science', 25)
""")
# enrollment insertion
cursor.execute("""
INSERT INTO enrollments (student_id, course_id, status)
VALUES (001, 0101, 'enrolled')
""")
conn.commit()
conn.close()
print("Sample first data for all tables inserted successfullt!")
