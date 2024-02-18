import flask

app = flask.Flask(__name__, template_folder="web", static_folder="static")

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt", "pdf", "zip", "mp4", "mp3", "jpg", "jpeg", "gif", "png", "docx", "doc", "ppt"}
