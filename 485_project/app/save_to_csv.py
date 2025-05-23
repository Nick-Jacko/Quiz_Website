import csv
import os

def save_to_csv(username, email, password, csv_file='users.csv'):
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['username', 'email', 'password'])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'username': username,
            'email': email,
            'password': password
        })