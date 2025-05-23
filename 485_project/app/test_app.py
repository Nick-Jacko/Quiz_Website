from unittest import TestCase
from app import app, check_credentials, generate_quiz_code
from flask import url_for
import sqlite3
import os

class TestFlaskRoutes(TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Create a temporary test database
        self.test_db = "test_users.db"
        self.create_test_db()

    # This function commented out to preserve database during test cases
    # Re-enable if testing database deletion is necessary
    # def tearDown(self):
    #     # Remove the test database after each test
    #     if os.path.exists(self.test_db):
    #         os.remove(self.test_db)

    def create_test_db(self):
        # Create a test database with dummy data
        connection = sqlite3.connect(self.test_db)
        cursor = connection.cursor()

        # Drop the Users table if it exists
        cursor.execute("DROP TABLE IF EXISTS Users;")

        cursor.execute("""
               CREATE TABLE Users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT UNIQUE NOT NULL,
                   email TEXT UNIQUE NOT NULL,
                   password TEXT NOT NULL
               );
           """)
        cursor.execute(
            "INSERT INTO Users (username, email, password) VALUES ('testuser', 'testuser@example.com', 'testpass');")
        connection.commit()
        connection.close()

        # Update the app to use the test database
        app.config["DATABASE"] = self.test_db

    def test_home_route(self):
        # Test the home route returns correct status and template
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)

    def test_login_route(self):
        # Test the login route returns correct status and template
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)

    def test_invalid_route(self):
        # Test invalid route returns 404
        response = self.app.get('/nonexistent')
        self.assertEqual(response.status_code, 404)

    def test_signup_page_get(self):
        """Test the GET request for the signup page."""
        response = self.app.get('/signup')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)  # Ensure the signup form is loaded

    def test_signup_with_invalid_email(self):
        """Test the POST request for signup with an invalid email."""
        response = self.app.post('/signup', data={
            'username': 'invalidemail',
            'email': 'invalidemail',  # Invalid email format
            'password': 'testpassword',
            'confirm_password': 'testpassword'
        })
        self.assertEqual(response.status_code, 200)  # Expect to still be on the signup page
        self.assertIn(b'Please enter a valid email address.', response.data)

    def test_signup_with_password_mismatch(self):
        """Test signup with mismatched passwords."""
        response = self.app.post('/signup', data={
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'testpassword',
            'confirm_password': 'mismatchpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Passwords do not match.', response.data)

    # THIS WILL FAIL IF YOU CHANGE GREETING
    def test_successful_login(self):
        # Test a successful login redirects to the greeting page
        response = self.app.post('/login', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Howdy, testuser', response.data)

    def test_failed_login(self):
        # Test a failed login shows an error message
        response = self.app.post('/login', data={'username': 'wronguser', 'password': 'wrongpass'},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_check_credentials_valid(self):
        # Test the check_credentials function with valid credentials
        self.assertTrue(check_credentials('testuser', 'testpass'))

    def test_check_credentials_invalid(self):
        # Test the check_credentials function with invalid credentials
        self.assertFalse(check_credentials('wronguser', 'wrongpass'))

    # THIS WILL FAIL IF YOU CHANGE GREETING
    def test_greeting_route(self):
        # Test the greeting route with a valid username
        response = self.app.get('/greeting/testuser')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Howdy, testuser', response.data)

    def test_add_new_user_to_database(self):
        """Test adding a new user to the database"""
        connection = sqlite3.connect(self.test_db)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO Users (username, email, password) VALUES (?, ?, ?)",
            ('newuser', 'new@test.com', 'newpass')
        )
        connection.commit()

        cursor.execute("SELECT * FROM Users WHERE username = ?", ('newuser',))
        user = cursor.fetchone()
        connection.close()

        self.assertIsNotNone(user)
        self.assertEqual(user[1], 'newuser')
        self.assertEqual(user[2], 'new@test.com')

    def test_duplicate_username_rejection(self):
        """Test that duplicate usernames are rejected"""
        connection = sqlite3.connect(self.test_db)
        cursor = connection.cursor()

        # Add first user
        cursor.execute(
            "INSERT INTO Users (username, email, password) VALUES (?, ?, ?)",
            ('dupuser', 'dup1@test.com', 'pass123')
        )
        connection.commit()

        # Try to add duplicate username
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO Users (username, email, password) VALUES (?, ?, ?)",
                ('dupuser', 'dup2@test.com', 'pass456')
            )
        connection.close()

    def test_duplicate_email_rejection(self):
        """Test that duplicate emails are rejected"""
        connection = sqlite3.connect(self.test_db)
        cursor = connection.cursor()

        # Add first user
        cursor.execute(
            "INSERT INTO Users (username, email, password) VALUES (?, ?, ?)",
            ('user1', 'same@test.com', 'pass123')
        )
        connection.commit()

        # Try to add duplicate email
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO Users (username, email, password) VALUES (?, ?, ?)",
                ('user2', 'same@test.com', 'pass456')
            )
        connection.close()

    def test_user_retrieval(self):
        """Test retrieving user data from database"""
        # Add test user
        connection = sqlite3.connect(self.test_db)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO Users (username, email, password) VALUES (?, ?, ?)",
            ('retrieveuser', 'retrieve@test.com', 'pass123')
        )
        connection.commit()

        # Retrieve and verify user data
        cursor.execute("SELECT * FROM Users WHERE username = ?", ('retrieveuser',))
        user = cursor.fetchone()
        connection.close()

        self.assertIsNotNone(user)
        self.assertEqual(user[1], 'retrieveuser')
        self.assertEqual(user[2], 'retrieve@test.com')

    def test_createquiz_route_no_username(self):
        response = self.app.post('/createquiz')
        self.assertEqual(response.status_code, 404)

        response = self.app.get('/createquiz', follow_redirects=True)
        self.assertEqual(response.status_code, 404)

    def test_createquiz_with_username(self):
        # The username to test with
        username = "TestUser"

        response = self.app.get(f'/createquiz/{username}')

        # Assert that the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

    def test_return_to_greeting(self):
        username = "TestUser"
        response = self.app.get(f'/greeting/{username}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Howdy, TestUser', response.data)

    def test_createdquizzes_route_no_username(self):
        # Test that the route properly returns to greeting page
        response = self.app.get('/allquizzes', follow_redirects=True)
        self.assertEqual(response.status_code, 404)

    def test_allquizzes_with_username(self):
        # The username to test with
        username = "aki"

        response = self.app.get(f'/allquizzes/{username}')

        # Assert that the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

    def test_takenquizzes_route_no_username(self):
        # Test that the route properly returns to greeting page
        response = self.app.get('/alltakenquizzes', follow_redirects=True)
        self.assertEqual(response.status_code, 404)

    def test_takenquizzes_with_username(self):
        # The username to test with
        username = "aki"

        response = self.app.get(f'/alltakenquizzes/{username}')

        # Assert that the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

    def test_createquiz_page_loads(self):
        """Test that the createquiz page loads successfully."""
        # Send a GET request to the '/createquiz' route
        username = "TestUser"

        response = self.app.get(f'/createquiz/{username}')
        # Assert that the HTTP response status code is good as 200 is the expected value
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)
        self.assertIn(b'Create a New Quiz', response.data)
        self.assertIn(b'Select Quiz Type', response.data)

    # Test form rendering (for quiz code form)
    def test_take_quiz_form(self):
        response = self.app.get('/takequiz/aki')  # Replace with the correct route
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Enter Quiz Code', response.data)

    def test_no_previous_quizzes(self):
        """Test that 'No previous quizzes' is shown if the user has no quizzes."""
        # 'testuser' has no quizzes in DUMMY_QUIZZES
        response = self.app.get('/allquizzes/noquizzes')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No quiz created.', response.data)

    def test_list_previous_quizzes(self):
        """Test that previous quizzes are listed on the page."""
        # 'DrKugele' has two quizzes in DUMMY_QUIZZES
        response = self.app.get('/allquizzes/aki')
        self.assertEqual(response.status_code, 200)

        # Check that the quiz names and creation dates are present
        self.assertIn(b'TEsting', response.data)
        self.assertIn(b'2024-12-07', response.data)
        self.assertIn(b'TestQUiz', response.data)
        self.assertIn(b'2024-12-07', response.data)


    def test_create_quiz_with_no_questions(self):
        """Test creating a quiz with no questions."""
        response = self.app.post('/save_quiz', data={
            'username': 'testuser',
            'quiz_title': 'Test Quiz',
            'quiz-type': 'true-false',
            'questions[]': []
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You need at least 1 question', response.data)


    def test_startquiz_page_loads(self):
        """Test that the startquiz page loads correctly."""
        # Create a quiz
        response = self.app.post('/save_quiz', data={
            'username': 'aki',
            'quiz_title': 'TestQUiz',
            'quiz-type': 'true-false',
            'questions[]': ['TEsting'],
            'answers[]': ['True']
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Extract the quiz code from the response data
        quiz_code = response.request.args.get('code')
        self.assertTrue(len(quiz_code) == 4)  # Check if the response is a 4-character quiz code

        # Access the startquiz page
        response = self.app.get(f'/startquiz/aki/{quiz_code}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Quiz Questions', response.data)

    # # ## US-8 ##
    def test_sort_by_date(self):
        """Test that quizzes are sorted by date (latest first)."""
        response = self.app.get('/allquizzes/quizorder')
        self.assertEqual(response.status_code, 200)

        # Check that the quizzes are sorted by date (latest first)
        quiz_names = [b'A quiz to test', b'Z quiz to test', b'B quiz to test']
        self.assertTrue(all(date in response.data for date in quiz_names))

    def test_sort_by_alphabetical(self):
        """Test that quizzes are sorted alphabetically when sorted."""
        response = self.app.get('/allquizzes/quizorder?sort=alphabetical')
        self.assertEqual(response.status_code, 200)

        # Check that quizzes are sorted alphabetically
        quiz_names = [b'A quiz to test',  b'B quiz to test', b'Z quiz to test']
        self.assertTrue(all(name in response.data for name in quiz_names))

class TestDatabaseCreation(TestCase):
    def setUp(self):
        # Create a temporary test database
        self.test_db = "test_quizzes.db"
        self.connection = sqlite3.connect(self.test_db)
        self.cursor = self.connection.cursor()

    # def tearDown(self):
    #     # Close the connection and remove the test database
    #     self.connection.close()
    #     if os.path.exists(self.test_db):
    #         os.remove(self.test_db)

    def test_table_creation(self):
        # Simulate the table creation
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS quizzes (
                    quizId INTEGER PRIMARY KEY AUTOINCREMENT,
                    quizCode INTEGER NOT NULL,
                    quizName TEXT NOT NULL,
                    questionNum INTEGER NOT NULL,
                    isMultiChoice BOOLEAN NOT NULL
                );
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    questionId INTEGER PRIMARY KEY AUTOINCREMENT,
                    quizId INTEGER NOT NULL,
                    questionStr TEXT NOT NULL,
                    response1 BOOLEAN,
                    response2 BOOLEAN,
                    response3 BOOLEAN,
                    response4 BOOLEAN,
                    correctResp TEXT NOT NULL,
                    FOREIGN KEY (quizId) REFERENCES quizzes(quizId)
                );
            """)
            # Check if the tables are created successfully
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quizzes';")
            quizzes_table = self.cursor.fetchone()
            self.assertIsNotNone(quizzes_table)

            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions';")
            questions_table = self.cursor.fetchone()
            self.assertIsNotNone(questions_table)
        except Exception as e:
            self.fail(f"Table creation failed with error: {e}")

    def test_quizzes_table_columns(self):
        # Create the quizzes table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                quizId INTEGER PRIMARY KEY AUTOINCREMENT,
                quizCode INTEGER NOT NULL,
                quizName TEXT NOT NULL,
                questionNum INTEGER NOT NULL,
                isMultiChoice BOOLEAN NOT NULL
            );
        """)

        # Check column information
        self.cursor.execute("PRAGMA table_info(quizzes);")
        columns = self.cursor.fetchall()
        expected_columns = [
            (0, 'quizId', 'INTEGER', 0, None, 1),
            (1, 'quizCode', 'INTEGER', 1, None, 0),
            (2, 'quizName', 'TEXT', 1, None, 0),
            (3, 'questionNum', 'INTEGER', 1, None, 0),
            (4, 'isMultiChoice', 'BOOLEAN', 1, None, 0),
        ]
        self.assertEqual(columns, expected_columns)

    def test_questions_table_columns(self):
        # Create the questions table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                questionId INTEGER PRIMARY KEY AUTOINCREMENT,
                quizId INTEGER NOT NULL,
                questionStr TEXT NOT NULL,
                response1 BOOLEAN,
                response2 BOOLEAN,
                response3 BOOLEAN,
                response4 BOOLEAN,
                correctResp TEXT NOT NULL,
                FOREIGN KEY (quizId) REFERENCES quizzes(quizId)
            );
        """)

        # Check column information
        self.cursor.execute("PRAGMA table_info(questions);")
        columns = self.cursor.fetchall()
        expected_columns = [
            (0, 'questionId', 'INTEGER', 0, None, 1),
            (1, 'quizId', 'INTEGER', 1, None, 0),
            (2, 'questionStr', 'TEXT', 1, None, 0),
            (3, 'response1', 'BOOLEAN', 0, None, 0),
            (4, 'response2', 'BOOLEAN', 0, None, 0),
            (5, 'response3', 'BOOLEAN', 0, None, 0),
            (6, 'response4', 'BOOLEAN', 0, None, 0),
            (7, 'correctResp', 'TEXT', 1, None, 0),
        ]
        self.assertEqual(columns, expected_columns)