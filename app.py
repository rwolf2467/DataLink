import flask
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file
import os
import zipfile
import secrets
from werkzeug.utils import secure_filename

app = flask.Flask(__name__, template_folder="web", static_folder="static")

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt", "pdf", "zip", "mp4", "mp3", "jpg", "jpeg", "gif", "png", "docx", "doc", "ppx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB Max file size
app.config['SECRET_KEY'] = secrets.token_hex(16)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_zip(file_list):
    zip_name = f'DataLink-{secrets.token_hex(10)}.zip'
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_name)

    with zipfile.ZipFile(zip_path, 'w') as zip_file:
        for file in file_list:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
            zip_file.write(file_path, file)

    return zip_name

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files[]' not in request.files:
        return redirect(request.url)

    files = request.files.getlist('files[]')

    if not files:
        return redirect(request.url)

    file_list = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_list.append(filename)

    if file_list:
        zip_name = create_zip(file_list)
        return redirect(url_for('success', zip_name=zip_name))
    else:
        return 'Ungültige Dateien'

@app.route('/success/<zip_name>')
def success(zip_name):
    return render_template('success.html', zip_name=zip_name)



@app.route('/download_page/<zip_name>')
def download_page(zip_name):
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_name)
    file_size = os.path.getsize(zip_path) / (1024 * 1024)  # Convert to MB
    return render_template('download_page.html', zip_name=zip_name, file_size=file_size)

@app.route('/download_file/<zip_name>')
def download_file(zip_name):
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_name)
    return send_file(zip_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
