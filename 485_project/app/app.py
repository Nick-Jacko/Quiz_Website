from flask import Flask, session, render_template, request, redirect, url_for, flash
import sqlite3
import csv
import os
import random
from datetime import datetime

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = '123456'

DATABASE = "users.db"
CSV_FILE = "users.csv"

# Dummy userx data
DUMMY_USERS = {
    'testuser': 'testpass',
    'admin': 'password',
    'DrKugele': '1234'
}

# Dummy data for quizzes created
DUMMY_QUIZZES = {
    "DrKugele": [
        {"quiz_id": 1, "quiz_name": "Biology Basics", "created_at": "2024-11-10"},
        {"quiz_id": 2, "quiz_name": "Advanced Biology", "created_at": "2024-11-15"}
    ],
    "testuser": [],
    "aki": [
        {"quiz_id": 12, "quiz_name": "Pineapple valid on pizza", "created_at": "2024-11-20"},
        {"quiz_id": 13, "quiz_name": "Is cereal soup?", "created_at": "2024-11-21"},
        {"quiz_id": 14, "quiz_name": "Is water wet?", "created_at": "2024-11-22"}
    ]
}


def save_to_csv(username, email, password):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['username', 'email', 'password'])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'username': username,
            'email': email,
            'password': password
        })

def populate_database_from_csv():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    """)

    with open(CSV_FILE, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                cursor.execute("""
                    INSERT INTO Users (username, email, password)
                    VALUES (?, ?, ?);
                """, (row['username'], row['email'], row['password']))
            except sqlite3.IntegrityError:
                continue

    connection.commit()
    connection.close()

def check_credentials(username, password):
    # First check dummy users
    if DUMMY_USERS.get(username) == password:
        return True

    # Then check database
    try:
        connection = sqlite3.connect(DATABASE)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return user is not None
    except Exception as e:
        print(f"Database error: {e}")
        return False

def generate_quiz_code():
    characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    code = ''.join(random.choice(characters) for _ in range(4))
    return code


@app.route('/')
def home():
    return render_template('index.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if check_credentials(username, password):
            return redirect(url_for("greeting", username=username))
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address.', 'error')
            return render_template('sign-up.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('sign-up.html')

        save_to_csv(username, email, password)
        populate_database_from_csv()

        return redirect(url_for('greeting', username=username))

    return render_template('sign-up.html')

@app.route('/save_quiz', methods=['POST'])
def save_quiz():
    # Get quiz data from the form
    username = request.form.get('username')
    quiz_title = request.form.get('quiz_title')
    quiz_type = request.form.get('quiz-type')
    questions = request.form.getlist('questions[]')

    # Generate the quiz code
    quiz_code = generate_quiz_code()

    if len(questions) == 0:
        flash("You need at least 1 question", "error")
        return redirect(url_for('createquiz', username=username))

    try:
        # Connect to users.db to fetch user ID
        conn_users = sqlite3.connect("users.db")
        cur_users = conn_users.cursor()
        user_id_query = "SELECT id FROM Users WHERE username = ?"
        user_id = cur_users.execute(user_id_query, (username,)).fetchone()
        if not user_id:
            flash("User not found.")
            conn_users.close()
            return redirect(url_for("greeting", username=username))
        user_id = user_id[0]
        conn_users.close()

        connection = sqlite3.connect("quizzes.db")
        cursor = connection.cursor()

        for index, question in enumerate(questions):
            if quiz_type == 'true-false':
                answer = request.form.getlist('answers[]')[index]
                cursor.execute("""
                    INSERT INTO quizzes (userId, quizCode, quizName, questionNum, isMultiChoice, questionStr, response1, response2, correctResp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, quiz_code, quiz_title, index + 1, 0, question, 'True', 'False', answer))
            elif quiz_type == 'multiple-choice':
                options = request.form.getlist(f'options-{index + 1}[]')
                correct_answer = request.form.get(f'correct-answer-{index + 1}')
                cursor.execute("""
                    INSERT INTO quizzes (userId, quizCode, quizName, questionNum, isMultiChoice, questionStr, response1, response2, response3, response4, correctResp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, quiz_code, quiz_title, index + 1, 1, question, options[0], options[1], options[2], options[3], correct_answer))

        connection.commit()
        return redirect(url_for('sharequiz', title=quiz_title, code=quiz_code, username=username))

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "An error occurred while saving the quiz. Please try again.", 500

    finally:
        if connection:
            connection.close()

@app.route("/greeting/<username>")
def greeting(username):
    return render_template("greeting.html", username=username)

@app.route("/createquiz/<username>")
def createquiz(username):
    return render_template("createquiz.html", username=username)




@app.route("/allquizzes/<username>")

def allquizzes(username):
    sort = request.args.get('sort', 'all')
    # Connect to the databases
    conn_users = sqlite3.connect('users.db')
    conn_quizzes = sqlite3.connect('quizzes.db')
    conn_dates = sqlite3.connect('responses.db')

    # Get the user ID from the username
    cursor_users = conn_users.cursor()
    cursor_users.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor_users.fetchone()

    if user:
        user_id = user[0]

        # Fetch quizzes created by the user
        cursor_quizzes = conn_quizzes.cursor()
        cursor_quizzes.execute("SELECT quizName, quizCode FROM quizzes WHERE userID = ?", (user_id,))
        quizzes = cursor_quizzes.fetchall()

        # Fetch the timestamp for each quiz and format it to just the date
        cursor_dates = conn_dates.cursor()
        quizzes_with_dates = []
        for quiz in quizzes:
            quiz_name = quiz[0]
            quiz_code = quiz[1]

            # Get the timestamp from responses for the quiz
            cursor_dates.execute("SELECT timestamp FROM responses WHERE quizCode = ?", (quiz_code,))
            quiz_timestamp = cursor_dates.fetchone()

            if quiz_timestamp:
                timestamp = quiz_timestamp[0]
                date_only = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").date()  # Extract date only
                quizzes_with_dates.append((quiz_name, quiz_code, date_only))
            else:
                quizzes_with_dates.append((quiz_name, quiz_code, None))  # No timestamp

         # Sorting logic based on the sort parameter
        if sort == 'recent':
            quizzes_with_dates = quizzes_with_dates[-5:]  # Get the recent 5 quizzes
        elif sort == 'date':
            # Sort quizzes by date, converting both sides to `date` type for comparison
            quizzes_with_dates.sort(key=lambda x: x[2] or datetime(1900, 1, 1).date(), reverse=True)
        elif sort == 'alphabetical':
            quizzes_with_dates.sort(key=lambda x: x[0], reverse=False)  # Sort by quiz name alphabetically
        # 'all' will leave quizzes as they are

    if not quizzes_with_dates:
        message = "No quiz created."
    else:
        message = None

    # Close the database connections
    conn_users.close()
    conn_quizzes.close()
    conn_dates.close()

    return render_template('allquizzes.html', username=username, quizzes=quizzes_with_dates, sort=sort, message=message)


@app.route("/alltakenquizzes/<username>")
def alltakenquizzes(username):
    sort = request.args.get('sort', 'all')  # Default sort is 'all'

    # Connect to the databases
    conn_users = sqlite3.connect('users.db')
    conn_responses = sqlite3.connect('responses.db')
    conn_quizzes = sqlite3.connect('quizzes.db')

    try:
        # Fetch user IDs
        cursor_users = conn_users.cursor()
        cursor_users.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor_users.fetchone()

        if not user:
            return {"error": "User not found"}, 404

        user_id = user[0]

        # Fetch quiz responses with timestamps
        cursor_responses = conn_responses.cursor()
        cursor_responses.execute(
            "SELECT DISTINCT quizId, timestamp FROM responses WHERE userID = ?", (user_id,)
        )
        response_data = cursor_responses.fetchall()

        if not response_data:
            return render_template('alltakenquizzes.html', username=username, quizzes=[])

        # Fetch quiz details
        quiz_ids = set([row[0] for row in response_data])
        placeholders = ', '.join('?' for _ in quiz_ids)
        cursor_quizzes = conn_quizzes.cursor()
        cursor_quizzes.execute(
            f"SELECT quizID, quizName FROM quizzes WHERE quizID IN ({placeholders})",
            tuple(quiz_ids)
        )
        quizzes = {row[0]: row[1] for row in cursor_quizzes.fetchall()}

        # Combine quiz details with response timestamps
        quizzes_with_dates = [
            {"quizId": quiz_id, "quizName": quizzes.get(quiz_id), "date": timestamp}
            for quiz_id, timestamp in response_data
        ]

        # Sorting logic
        if sort == 'recent':
            quizzes_with_dates = sorted(
                quizzes_with_dates, key=lambda x: x['date'], reverse=True
            )[:5]  # Limit to 5 recent
        elif sort == 'alphabetical':
            quizzes_with_dates.sort(key=lambda x: x['quizName'].lower() if x['quizName'] else "")
        elif sort == 'date':
            quizzes_with_dates.sort(key=lambda x: x['date'], reverse=True)

        return render_template(
            'alltakenquizzes.html',
            username=username,
            quizzes=quizzes_with_dates,
            sort=sort
        )

    finally:
        conn_users.close()
        conn_responses.close()
        conn_quizzes.close()


@app.route("/quizscore/<username>/<quiz_id>")
def quiz_score(username, quiz_id):
    # Connect to necessary databases
    conn_responses = sqlite3.connect('responses.db')
    conn_users = sqlite3.connect('users.db')
    conn_quizzes = sqlite3.connect('quizzes.db')

    try:
        # Fetch user ID
        cursor_users = conn_users.cursor()
        cursor_users.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor_users.fetchone()

        if not user:
            return {"error": "User not found"}, 404

        user_id = user[0]

        # Fetch quiz name
        cursor_quizzes = conn_quizzes.cursor()
        cursor_quizzes.execute("SELECT quizName FROM quizzes WHERE quizID = ?", (quiz_id,))
        quiz = cursor_quizzes.fetchone()

        if not quiz:
            return {"error": "Quiz not found"}, 404

        quiz_name = quiz[0]

        # Fetch user responses for the quiz
        cursor_responses = conn_responses.cursor()
        cursor_responses.execute(
            "SELECT questionNum, userResponse FROM responses WHERE quizId = ? AND userId = ?",
            (quiz_id, user_id)
        )
        user_responses = cursor_responses.fetchall()

        # Fetch all correct responses for each question in this quiz
        cursor_quizzes.execute(
            "SELECT questionNum, correctResp FROM quizzes WHERE quizID = ?",
            (quiz_id,)
        )
        correct_responses = cursor_quizzes.fetchall()  # Fetch all correct responses

        # Create a dictionary of correct answers for each question (for later use in HTML)
        correct_answers = {row[0]: row[1] for row in correct_responses}

        # Calculate score
        correct_responses_count = 0
        total_responses = len(user_responses)

        for question_num, user_answer in user_responses:
            correct_answer = correct_answers.get(question_num)
            if correct_answer and user_answer.strip().lower() == correct_answer.strip().lower():
                correct_responses_count += 1

        # Render score page
        return render_template(
            "quizscore.html",
            username=username,
            quiz_name=quiz_name,
            correct_responses=correct_responses_count,
            total_responses=total_responses,
            user_responses=user_responses,  # Add user_responses for debugging
            correct_answers=correct_answers  # Add correct_answers for debugging
        )



    finally:
        conn_responses.close()
        conn_users.close()
        conn_quizzes.close()





@app.route("/takequiz/<username>", methods=["GET", "POST"])
def takequiz(username):
    if request.method == "POST":
        quiz_code = request.form.get("quiz_code")

        # Fetch the quiz based on the quiz code
        conn = sqlite3.connect("quizzes.db")
        cur = conn.cursor()
        cur.execute("SELECT quizId FROM quizzes WHERE quizCode = ?", (quiz_code,))
        quiz = cur.fetchone()
        conn.close()

        if quiz:
            # Redirect to the quiz-taking page with the quiz code
            return redirect(url_for("start_quiz", username=username, quiz_code=quiz_code))
        else:
            # If invalid, show an error
            flash("Invalid quiz code. Please try again.", "error")
            return redirect(url_for("takequiz", username=username))

    return render_template("takequiz.html", username=username)






@app.route("/startquiz/<username>/<quiz_code>")
def start_quiz(username, quiz_code):
    # Fetch the quiz details using the quiz code
    conn = sqlite3.connect("quizzes.db")
    cur = conn.cursor()
    # Fetch the quiz questions based on the quiz code
    quiz_query = """
            SELECT DISTINCT questionNum, questionStr, response1, response2, response3, response4, isMultiChoice
            FROM quizzes
            WHERE quizCode = ?
            ORDER BY questionNum
        """
    questions = cur.execute(quiz_query, (quiz_code,)).fetchall()

    # Format questions for rendering in the template
    formatted_questions = [
        {
            "id": row[0],
            "question": row[1],
            "choices": [row[2], row[3], row[4], row[5]],
            "is_multi_choice": row[6]
        }
        for row in questions
    ]
    return render_template("startquiz.html", username=username, quiz_code=quiz_code, questions=formatted_questions, enumerate=enumerate)


@app.route('/submit_quiz/<username>/<quiz_code>', methods=['POST'])
def submit_quiz(username, quiz_code):
    # Connect to users.db to fetch user ID
    conn_users = sqlite3.connect("users.db")
    cur_users = conn_users.cursor()

    user_id_query = "SELECT id FROM Users WHERE username = ?"
    user_id = cur_users.execute(user_id_query, (username,)).fetchone()
    if not user_id:
        flash("User not found.")
        conn_users.close()
        return redirect(url_for("greeting", username=username))
    user_id = user_id[0]
    conn_users.close()

    # Connect to quizzes.db to fetch quiz ID
    conn_quizzes = sqlite3.connect("quizzes.db")
    cur_quizzes = conn_quizzes.cursor()

    quiz_id_query = "SELECT quizId FROM quizzes WHERE quizCode = ?"
    quiz_id = cur_quizzes.execute(quiz_id_query, (quiz_code,)).fetchone()
    if not quiz_id:
        flash("Quiz not found.")
        conn_quizzes.close()
        return redirect(url_for("greeting", username=username))
    quiz_id = quiz_id[0]
    conn_quizzes.close()

    # Connect to responses.db to save responses
    conn_responses = sqlite3.connect("responses.db")
    cur_responses = conn_responses.cursor()

    for key, value in request.form.items():
        if key.startswith("question_"):
            try:
                question_num = int(key.split("_")[1]) + 1  # Adjust to start from 1
                user_response = value

                cur_responses.execute("""
                    INSERT INTO responses (userId, quizId, quizCode, questionNum, userResponse)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, quiz_id, quiz_code, question_num, user_response))
            except ValueError:
                flash(f"Invalid question number format: {key}. Skipping.")
                continue

    conn_responses.commit()
    conn_responses.close()

    return redirect(url_for("results", username=username, quiz_code=quiz_code))


''''@app.route("/view_responses/<username>/<quiz_id>")
def view_responses(username, quiz_id):
    conn_users = sqlite3.connect('users.db')

    # Get the user ID from the username
    cursor_users = conn_users.cursor()
    cursor_users.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor_users.fetchone()
    user_id = user[0]

    conn = sqlite3.connect("owners.db")
    cur = conn.cursor()

    conn = sqlite3.connect("responses.db")
    cur = conn.cursor()
    cur.execute("SELECT userId, questionNum, userResponse, timestamp FROM responses WHERE quizId = ?", (quiz_id,))
    responses = cur.fetchall()
    conn.close()
    conn_users.close()

    return render_template("view_responses.html", responses=responses)'''

'''
@app.route("/view_responses/<username>/<quiz_id>")
def view_responses(username, quiz_id):
    conn_users = sqlite3.connect("users.db")
    cursor_users = conn_users.cursor()
    cursor_users.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor_users.fetchone()
    user_id = user[0]

    print(quiz_id)

    conn_quiz = sqlite3.connect("quizzes.db")
    cursor_quiz = conn_quiz.cursor()
    cursor_quiz.execute("SELECT quizName FROM quizzes WHERE quizCode = ?", (quiz_id,))
    quiz_name = cursor_quiz.fetchone()[0]

    conn_responses = sqlite3.connect("responses.db")
    cursor_responses = conn_responses.cursor()
    cursor_responses.execute("""
        SELECT r.userId, r.questionNum, r.userResponse, r.timestamp, q1.questionSTR, q1.correctResp
        FROM responses r, quizzes q1
        JOIN quizzes q ON r.quizId = q.quizId AND r.questionNum = q.questionNum
        WHERE r.quizId = ?
    """, (quiz_id,))
    rows = cursor_responses.fetchall()

    responses_by_user = {}
    for user_id, question_num, user_response, timestamp, question_str, correct_resp in rows:
        if user_id not in responses_by_user:
            responses_by_user[user_id] = {"username": f"User{user_id}", "responses": []}
        responses_by_user[user_id]["responses"].append({
            "question_num": question_num,
            "question_str": question_str,
            "user_response": user_response,
            "correct_answer": correct_resp,
        })

    conn_users.close()
    conn_quiz.close()
    conn_responses.close()

    return render_template("view_responses.html", quiz_name=quiz_name, responses_by_user=responses_by_user)
    '''
@app.route("/view_responses/<username>/<quiz_code>")
def view_responses(username, quiz_code):
    # Get userId
    conn_users = sqlite3.connect("users.db")
    cursor_users = conn_users.cursor()
    cursor_users.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor_users.fetchone()
    user_id = user[0]
    

    # Fetch quizCode using userId
    conn_quiz = sqlite3.connect("quizzes.db")
    cursor_quiz = conn_quiz.cursor()
    cursor_quiz.execute("SELECT quizId, quizName FROM quizzes WHERE quizCode = ?", (quiz_code,))
    quiz = cursor_quiz.fetchone()
    
    if not quiz:
        return "Quiz not found", 404
    
    quiz_id, quiz_name = quiz

    # print(quiz_id, quiz_name)

    # Fetch responses from 'responses.db' where both userId and quizId match
    conn_responses = sqlite3.connect("responses.db")
    cursor_responses = conn_responses.cursor()
    cursor_responses.execute("""
        SELECT questionNum, userResponse, timestamp
        FROM responses
        WHERE userId = ? AND quizId = ?
    """, (user_id, quiz_id))

    rows = cursor_responses.fetchall()

    if not rows:
        return f"No responses found for user {username} in quiz {quiz_name}.", 404  # Handle if no responses found
    
    # Organize reponses by questions numbers
    responses = []
    for question_num, user_response, timestamp in rows:
        # Assuming 'timestamp' is a string like "2024-12-09 12:30:45"
        formatted_timestamp = timestamp[:10]  # Get the first 10 characters (YYYY-MM-DD)


        responses.append({
            "question_num": question_num,
            "user_response": user_response,
            "timestamp": formatted_timestamp
        })

    
    # print(rows)
        

    # Close database connections
    conn_users.close()
    conn_quiz.close()
    conn_responses.close()

    # Step 5: Render the template with the quiz and responses data
    return render_template("view_responses.html", quiz_name=quiz_name, responses=responses)




@app.route('/view_quizzes')
def view_quizzes():
    try:
        # Connect to the database
        connection = sqlite3.connect("quizzes.db")
        cursor = connection.cursor()

        # Fetch quiz data
        cursor.execute("""
            SELECT *
            FROM quizzes 
        """)
        quizzes = cursor.fetchall()

        # Close the connection
        connection.close()

        # Pass the quiz data to the template
        return render_template("view_quizzes.html", quizzes=quizzes)

    except sqlite3.Error as e:
        return f"Error fetching quizzes: {e}"



'''SHARING QUIZ'''


@app.route('/sharequiz')
def sharequiz():
    quiz_title = request.args.get('title')
    quiz_code = request.args.get('code')
    username = request.args.get('username')
    return render_template('sharequiz.html', title=quiz_title, code=quiz_code, username=username)




@app.route('/results/<username>/<quiz_code>')
def results(username, quiz_code):
    # Connect to users.db to fetch user ID
    conn_users = sqlite3.connect("users.db")
    cur_users = conn_users.cursor()

    user_id_query = "SELECT id FROM Users WHERE username = ?"
    user_id = cur_users.execute(user_id_query, (username,)).fetchone()
    if not user_id:
        flash("User not found.")
        conn_users.close()
        return redirect(url_for("greeting", username=username))
    user_id = user_id[0]
    conn_users.close()

    # Connect to responses.db to fetch the response with the highest responseId
    conn_responses = sqlite3.connect("responses.db")
    cur_responses = conn_responses.cursor()

    highest_response_query = """
        SELECT responseId, timestamp
        FROM responses
        WHERE userId = ? AND quizCode = ?
        ORDER BY responseId DESC
        LIMIT 1
    """
    cur_responses.execute(highest_response_query, (user_id, quiz_code))
    highest_response = cur_responses.fetchone()
    if not highest_response:
        flash("No responses found for this quiz.")
        conn_responses.close()
        return redirect(url_for("greeting", username=username))

    highest_response_id, highest_timestamp = highest_response

    # Fetch all responses with the same timestamp and quizCode
    responses_query = """
        SELECT questionNum, userResponse
        FROM responses
        WHERE userId = ? AND quizCode = ? AND timestamp = ?
        ORDER BY questionNum ASC
    """
    cur_responses.execute(responses_query, (user_id, quiz_code, highest_timestamp))
    user_responses = cur_responses.fetchall()
    conn_responses.close()

    # Connect to quizzes.db to fetch correct answers and response options
    conn_quizzes = sqlite3.connect("quizzes.db")
    cur_quizzes = conn_quizzes.cursor()

    correct_answers_query = """
        SELECT questionNum, isMultiChoice, correctResp, response1, response2, response3, response4
        FROM quizzes
        WHERE quizCode = ?
    """
    cur_quizzes.execute(correct_answers_query, (quiz_code,))
    correct_answers = cur_quizzes.fetchall()
    conn_quizzes.close()

    # Compare responses and correct answers
    results = []
    for user_response in user_responses:
        question_num, user_answer = user_response
        correct_answer_data = next((data for data in correct_answers if data[0] == question_num), None)
        if correct_answer_data:
            is_multi_choice = correct_answer_data[1]
            correct_answer = correct_answer_data[2]
            if is_multi_choice:
                # Compare user response to each of the response columns
                correct = user_answer in correct_answer_data[3:7]
            else:
                # Compare user response to the correct response
                correct = user_answer == correct_answer_data[2]
            results.append({
                'question_num': question_num,
                'user_answer': user_answer,
                'correct': correct,
                'correct_answer': correct_answer
            })

    return render_template("results.html", username=username, results=results)

@app.route('/clear_results/<username>/<quiz_code>')
def clear_results(username, quiz_code):
    # Connect to responses.db to delete user responses for the current quiz
    conn_responses = sqlite3.connect("responses.db")
    cur_responses = conn_responses.cursor()

    delete_query = """
        DELETE FROM responses
        WHERE userId = (SELECT id FROM Users WHERE username = ?) AND quizCode = ?
    """
    cur_responses.execute(delete_query, (username, quiz_code))
    conn_responses.commit()
    conn_responses.close()

    return redirect(url_for('greeting', username=username))


if __name__ == '__main__':
    app.run(debug=True)