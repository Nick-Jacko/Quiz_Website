import sqlite3
import random

def create_table():
    try:
        # Connect to the database
        connection = sqlite3.connect("../app/quizzes.db")
        cursor = connection.cursor()

        # Create quizzes table with the new columns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                quizId INTEGER PRIMARY KEY AUTOINCREMENT,
                userId INTEGER NOT NULL,
                quizCode TEXT NOT NULL,
                quizName TEXT NOT NULL,
                questionNum INTEGER NOT NULL,
                isMultiChoice BOOLEAN NOT NULL,
                questionStr TEXT NOT NULL,
                response1 TEXT NOT NULL,
                response2 TEXT NOT NULL,
                response3 TEXT,
                response4 TEXT,
                correctResp TEXT,
                FOREIGN KEY(userId) REFERENCES Users(id)
            );
        """)

        connection.commit()
        connection.close()

        print("Table 'quizzes' created successfully.")

        # Create owners table in owners.db (this links users and quizzes)
        connection = sqlite3.connect("../app/owners.db")  # Adjust path as needed
        cursor = connection.cursor()

        # Create Owners table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS owners (
                userId INTEGER NOT NULL,
                quizId INTEGER NOT NULL,
                FOREIGN KEY(userId) REFERENCES Users(id),
                FOREIGN KEY(quizId) REFERENCES quizzes(quizId),
                PRIMARY KEY (userId, quizId)
            );
        """)

        connection.commit()
        connection.close()

        print("Table 'owners' created successfully.")

        # This code is for Users!
        connection = sqlite3.connect("../app/users.db")  # SQLite database file
        cursor = connection.cursor()

        # Create Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        """)

        print("Table 'users' created successfully.")

        connection.commit()

        # Create questions table
        cursor.execute("""
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

        print("Table 'questions' created successfully.")

        # Commit changes and close connection
        connection.commit()
        connection.close()

        # Create responses table in responses.db
        connection = sqlite3.connect("../app/responses.db")
        cursor = connection.cursor()

        # Create responses table--for tracking user responses to quizzes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                responseId INTEGER PRIMARY KEY AUTOINCREMENT,
                userId INTEGER NOT NULL,
                quizId INTEGER NOT NULL,
                quizCode TEXT NOT NULL,
                questionNum INTEGER NOT NULL,
                userResponse TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(userId) REFERENCES Users(id),
                FOREIGN KEY(quizId) REFERENCES quizzes(quizId)
            );
        """)

        connection.commit()
        connection.close()

        print("Table 'responses' created successfully.")

    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    create_table()