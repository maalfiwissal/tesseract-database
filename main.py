from flask import Flask, render_template, request, redirect, url_for
from PIL import Image
import pytesseract
import mysql.connector
import re

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'votre_cle_secrete'  # Changez cela dans un environnement de production
USERNAME = 'admin'
PASSWORD = '1234'

# Set up MySQL connection
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'teseract',
    'port': 3306,
}

conn = mysql.connector.connect(**mysql_config)
cursor = conn.cursor()

# Function to extract text from the image using Tesseract
def extract_text(image_path):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Tesseract-OCR\tesseract.exe'
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text

# Function to parse relevant information from the OCR result
def parse_information(text):
    # Example parsing logic; adjust based on the actual structure of your OCR result
    match_name = re.search(r'(Prénom\(s\): |Prénom{s\): )(\w+)', text)
    name = match_name.group(2) if match_name else None

    match_gender = re.search(r'(Sexe :|Sexe: )(\w+)', text)
    gender = match_gender.group(2) if match_gender else None

    #match_birthdate = re.search(r'née} le: (.+)', text)
    #birthdate = match_birthdate.group(1) if match_birthdate else None

    match_birthdate = re.search(r'(née} le:|Né\(e\) le:|Néle\)|Né\(e\) le =) (.+)', text)
    birthdate = match_birthdate.group(2) if match_birthdate else None

    match_place_of_birth = re.search(r'a: (.+)', text)
    place_of_birth = match_place_of_birth.group(1) if match_place_of_birth else None

    #match_height = re.search(r'Taille : (.+)', text)
    #height = match_height.group(1) if match_height else None

    match_height = re.search(r'(Taille :|Taille:)(.+)', text)
    height = match_height.group(2) if match_height else None

    # Provide default values for fields that may be None
    name = name or 'Unknown'
    gender = gender or 'Unknown'
    birthdate = birthdate or 'Unknown'
    place_of_birth = place_of_birth or 'Unknown'
    height = height or 'Unknown'

    return name, gender, birthdate, place_of_birth, height

# Function to save text to MySQL database
def save_to_database(parsed_info):
    query = "INSERT INTO table1 (name, sexe, birthdate, place_of_birth, taille) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(query, parsed_info)
    conn.commit()

@app.route('/')
def login():
    return render_template('home.html')

@app.route('/home', methods=['POST'])
def home():
    if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
        # Change the redirect route to '/index' or the desired route
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def result():
    if request.method == 'POST':
        try:
            file = request.files['file']
            if file:
                file_path = f"uploads/{file.filename}"
                file.save(file_path)

                text = extract_text(file_path)
                parsed_info = parse_information(text)
                save_to_database(parsed_info)

                return render_template('result.html', text=text, user_data=parsed_info)
        except Exception as e:
            return str(e)

    return render_template('result.html', text=None, user_data=None)

@app.route('/view_data', methods=['GET', 'POST'])
def view_data():
    if request.method == 'POST':
        # If a search term is provided, filter the data based on the name
        search_name = request.form.get('search_name')
        if search_name:
            query = "SELECT * FROM table1 WHERE name LIKE %s"
            cursor.execute(query, ('%' + search_name + '%',))
            rows = cursor.fetchall()
        else:
            # If no search term, retrieve all rows
            query = "SELECT * FROM table1"
            cursor.execute(query)
            rows = cursor.fetchall()

    else:
        # If it's a GET request, retrieve all rows
        query = "SELECT * FROM table1"
        cursor.execute(query)
        rows = cursor.fetchall()

    return render_template('view_data.html', rows=rows)
def delete_row(row_name):
    query = "DELETE FROM table1 WHERE name = %s"
    cursor.execute(query, (row_name,))
    conn.commit()

@app.route('/delete_row', methods=['POST'])
def delete_row_view():
    if request.method == 'POST':
        row_name = request.form.get('row_name')
        if row_name:
            delete_row(row_name)
    return redirect(url_for('view_data'))


if __name__ == '__main__':
    app.run(debug=True)
