import sqlite3
import csv

def populate_user(csv_file):
    try:
        connection = sqlite3.connect("../app/users.db")
        cursor = connection.cursor()

        # Read the CSV file
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    cursor.execute("""
                        INSERT INTO Users (username, email, password)
                        VALUES (?, ?, ?);
                    """, (row['username'], row['email'], row['password']))
                except sqlite3.IntegrityError:
                    print(f"User {row['username']} already exists.")

        connection.commit()
        print("Table 'Users' populated successfully.")
    except Exception as e:
        print(f"Error populating table: {e}")
    finally:
        connection.close()

import sqlite3
import csv

# This will look like it throws errors, but it won't. Probably
def populate_quizzes(csv_file):
    try:
        connection = sqlite3.connect("../app/quizzes.db")
        cursor = connection.cursor()

        # Read the CSV file
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    cursor.execute("""
                        INSERT INTO quizzes (
                            quizCode, quizName, questionNum, isMultiChoice, questionStr,
                            response1, response2, response3, response4, correctResp
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        row['quizCode'],
                        row['quizName'],
                        int(row['questionNum']),
                        bool(int(row['isMultiChoice'])),
                        row['questionStr'],
                        row['response1'],
                        row['response2'],
                        row.get('response3', None),
                        row.get('response4', None),
                        int(row['correctResp'])
                    ))
                except sqlite3.IntegrityError as e:
                    print(f"Error inserting quiz {row['quizCode']} question {row['questionNum']}: {e}")

        connection.commit()
        print("Table 'quizzes' populated successfully.")
    except Exception as e:
        print(f"Error populating quizzes: {e}")
    finally:
        connection.close()

def populate_owners(csv_file):
    try:
        connection = sqlite3.connect("../app/owners.db")
        cursor = connection.cursor()

        # Read the CSV file
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    cursor.execute("""
                        INSERT INTO owners (userId, quizId)
                        VALUES (?, ?);
                    """, (row['userId'], row['quizId']))
                except sqlite3.IntegrityError:
                    print(f"Owner mapping for User {row['userId']} and Quiz {row['quizId']} already exists.")

        connection.commit()
        print("Table 'owners' populated successfully.")
    except Exception as e:
        print(f"Error populating owners: {e}")
    finally:
        connection.close()


if __name__ == "__main__":
    # Provide the path to your CSV file
    populate_user('users.csv')
    populate_quizzes('quizzes.csv')
    populate_owners('owners.csv')

