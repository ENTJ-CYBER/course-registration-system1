Course; Intro to Python
Framework: Flask 3.1.3
Language: Python 3
Frontend: HTML, CSS, JavaScript
Database: SQLite (SQL)
Teammates: Ghazal Ahmadzai, Faiza Hussaini, Noorullah Ahmadi, Parwana Jafari, Sana Hashemi

1. Project Overview
This is a web-based Student Course Registration System built using Python Flask and SQLite. It supports two types of users: Admins and Students. Admins can manage courses and students, while students can browse, search, and enroll in courses. The system also tracks enrollment history for each student.

2. Project Structure
The project is organized into two main folders.
The flask_project folder contains the core application. Inside it, app.py is the main file that handles all the routes and application logic. The static folder holds the CSS and JavaScript files for styling and interactivity. The templates folder contains all the HTML pages, organized into subfolders for authentication, courses, the main dashboard, and student pages.
The Database Scheme & Testing folder contains the database setup scripts. registration.py creates all the database tables. reg_insert_data.py fills the database with sample data. test_database.py contains the tests for verifying the database is working correctly.

3. Setup & Installation
To run this project on your machine, follow these steps.
First, make sure you have Python 3.8 or higher installed. Then clone or download the project repository to your computer.
Next, open a terminal inside the project folder and create a virtual environment by running python -m venv .venv. Activate it — on Windows use .venv\Scripts\activate, and on Mac or Linux use source .venv/bin/activate.
After activating the environment, install Flask by running pip install flask.
Now initialize the database. Go into the Database Scheme & Testing folder and run python registration.py to create the tables, then run python reg_insert_data.py to insert the sample data.
Finally, go into the flask_project folder and run python app.py. The application will start and you can open it in your browser at http://127.0.0.1:5000.
To log in as an admin, use the email admin@auaf.edu and password admin123.

4. Database Schema
The database uses SQLite and has four tables.
The users table stores all accounts in the system, whether admin or student. Each record has an ID, username, email, password, and a role field that is either "admin" or "student".
The students table stores extra profile information for student users. It links to the users table through a user ID, and also stores the student's full name and department.
The courses table holds all available courses. Each course has a name, instructor, number of credits, schedule, department, and a capacity limit for how many students can enroll.
The enrollments table connects students to courses. Each record stores the student ID, the course ID, and the current status of the enrollment, such as "enrolled" or "dropped". One student can have many enrollments, and one course can have many students enrolled in it.

5. API Endpoints
The application is organized into five route groups called Blueprints.
Authentication routes handle login, registration, and logout. Visiting /login shows the login form and submitting it checks the credentials and redirects to the appropriate dashboard. The /register route lets new students create an account. The /logout route clears the session and sends the user back to the login page.
Main routes handle the dashboards. After logging in, admins are sent to /dashboard which shows system statistics like total students, courses, and enrollments. Students are sent to /student-dashboard which shows their currently enrolled courses.
Course routes are found under /courses. Any user can view the course list at /courses/ or view a single course at /courses/<id>. Admins can add a new course at /courses/add, edit one at /courses/<id>/edit, and delete one at /courses/<id>/delete.
Student management routes are under /students and are only accessible to admins. Admins can view a list of all students, view an individual student's profile, and edit student information.
Enrollment routes are under /enrollment and are only for students. Students can browse available courses, search for courses by name, instructor, or department, enroll in a course, drop a course, and view their full enrollment history.

6. Data Models
The application stores user information in a session after login. The session holds the user's ID, username, role, full name, and email. This session data is used throughout the app to control what each user can see and do.
Admins have access to course management, student management, and the admin dashboard. Students have access to course browsing, enrollment, dropping courses, and viewing their history. Neither role has access to the other's features.

7. Testing
The project includes database tests located in the Database Scheme & Testing folder. To run them, navigate to that folder and run python test_database.py.
The tests check that all four database tables — users, courses, students, and enrollments — contain data after the setup scripts have been run. Each test uses an assertion to confirm at least one row exists in the table. If everything is working, you will see four pass messages printed in the terminal, one for each table.
For manual testing, you can verify the main features by going through the app directly. Register a new student account and confirm it redirects to the login page. Log in as a student and try enrolling in and dropping a course. Log in as an admin and try adding, editing, and deleting a course. Search for a course using a keyword and confirm the results are filtered correctly.

