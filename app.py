import os
import secrets
import zipfile
import mimetypes
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

import quart
from quart import Quart, render_template, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename

app = Quart(__name__, template_folder="web", static_folder="static")

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {
    "txt",
    "pdf",
    "zip",
    "mp4",
    "mp3",
    "jpg",
    "jpeg",
    "gif",
    "png",
    "docx",
    "doc",
    "pptx",
    "ppt",
    "xlsx",
    "xls",
    "mov",
    "wav",
    "py",
    "java",
    "jar",
    "exe",
    "pem",
    "json",
    "html",
    "css",
    "js",
    "xml",
    "yml",
    "yaml",
    "log",
    "sh",
    "bash",
    "md",
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024 * 1024  
app.config["SECRET_KEY"] = secrets.token_hex(16)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def detect_language(text, filename=""):
    extension_to_lexer = {
        ".py": "python",
        ".js": "javascript",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".xml": "xml",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".sh": "bash",
        ".bash": "bash",
        ".log": "text",
        ".txt": "text",
        ".md": "markdown",
        ".java": "java",
    }

    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext in extension_to_lexer:
            try:
                return get_lexer_by_name(extension_to_lexer[ext])
            except ClassNotFound:
                pass

    try:
        return guess_lexer(text)
    except ClassNotFound:
        return TextLexer()


def highlight_code(text, filename=""):
    
    lines = text.splitlines()
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    end = len(lines)
    while end > start and not lines[end - 1].strip():
        end -= 1
    trimmed_text = "\n".join(lines[start:end])

    lexer = detect_language(trimmed_text, filename)
    formatter = HtmlFormatter(
        style="github-dark",
        noclasses=True,
        linenos=False,  
        cssclass="highlight",
    )
    return highlight(trimmed_text, lexer, formatter)


def create_zip(file_list):
    zip_name = f"DataLink-{secrets.token_hex(10)}.zip"
    zip_path = os.path.join(app.config["UPLOAD_FOLDER"], zip_name)

    with zipfile.ZipFile(zip_path, "w") as zip_file:
        for file in file_list:
            file_path = str(os.path.join(app.config["UPLOAD_FOLDER"], file))
            zip_file.write(file_path, file)

    return zip_name


@app.route("/")
async def home():
    return await render_template("index.html")


@app.route("/upload", methods=["POST"])
async def upload_file():
    form = await request.form
    files = await request.files
    text_content = form.get("text_content", "").strip()
    file_list = files.getlist("files[]") if "files[]" in files else []

    
    if text_content and not file_list:
        file_type = form.get("file_type", "auto")
        ext_map = {
            "python": ".py",
            "javascript": ".js",
            "html": ".html",
            "css": ".css",
            "json": ".json",
            "bash": ".sh",
            "yaml": ".yml",
            "markdown": ".md",
            "java": ".java",
            "xml": ".xml",
            "txt": ".txt",
        }

        if file_type != "auto" and file_type in ext_map:
            ext = ext_map[file_type]
        else:
            
            try:
                lexer = detect_language(text_content)
                ext = ext_map.get(file_type, ".txt")
                
                lexer_ext_map = {
                    "Python": ".py",
                    "JavaScript": ".js",
                    "HTML": ".html",
                    "CSS": ".css",
                    "JSON": ".json",
                    "Bash": ".sh",
                    "YAML": ".yml",
                    "Markdown": ".md",
                    "Java": ".java",
                    "XML": ".xml",
                }
                ext = lexer_ext_map.get(lexer.name, ".txt")
            except Exception:
                ext = ".txt"

        filename = f"note-{secrets.token_hex(6)}{ext}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        return redirect(url_for("download_page", zip_name=filename))

    
    saved_files = []
    for file in file_list:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            await file.save(file_path)
            saved_files.append(filename)

    if saved_files:
        
        if len(saved_files) == 1:
            filename = saved_files[0]
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type:
                if (
                    mime_type.startswith("image/")
                    or mime_type.startswith("video/")
                    or filename.lower().endswith(
                        (
                            ".txt",
                            ".py",
                            ".js",
                            ".json",
                            ".html",
                            ".css",
                            ".xml",
                            ".yml",
                            ".yaml",
                            ".sh",
                            ".md",
                            ".log",
                        )
                    )
                ):
                    return redirect(url_for("download_page", zip_name=filename))

        
        
        
        all_images = True
        image_files = []
        for fname in saved_files:
            mime_type, _ = mimetypes.guess_type(fname)
            if not (mime_type and mime_type.startswith("image/")):
                all_images = False
                break
            image_files.append(fname)

        if all_images and len(image_files) > 1:
            
            gallery_name = f"gallery-{secrets.token_hex(6)}.list"
            gallery_path = os.path.join(app.config["UPLOAD_FOLDER"], gallery_name)
            with open(gallery_path, "w", encoding="utf-8") as f:
                f.write("\n".join(image_files))
            return redirect(url_for("download_page", zip_name=gallery_name))

        
        zip_name = create_zip(saved_files)
        return redirect(url_for("download_page", zip_name=zip_name))

    
    return await render_template("error.html")


@app.route("/d/<zip_name>")
async def download_page(zip_name):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], zip_name)
    if not os.path.exists(file_path):
        return "File not found", 404

    file_size = os.path.getsize(file_path) / (1024 * 1024)

    
    is_gallery = zip_name.endswith(".list")
    image_files = []
    if is_gallery:
        with open(file_path, "r", encoding="utf-8") as f:
            image_files = [line.strip() for line in f.readlines() if line.strip()]
        
        total_size = sum(
            os.path.getsize(os.path.join(app.config["UPLOAD_FOLDER"], img))
            for img in image_files
            if os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], img))
        )
        file_size = total_size / (1024 * 1024)

    mime_type, _ = mimetypes.guess_type(zip_name)
    is_image = mime_type and mime_type.startswith("image/")
    is_video = mime_type and mime_type.startswith("video/")
    is_text_like = zip_name.lower().endswith(
        (
            ".txt",
            ".py",
            ".js",
            ".json",
            ".html",
            ".css",
            ".xml",
            ".yml",
            ".yaml",
            ".sh",
            ".md",
            ".log",
        )
    )

    highlighted_content = None
    if is_text_like and not is_gallery:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            highlighted_content = highlight_code(content, zip_name)
        except Exception:
            pass

    return await render_template(
        "download_page.html",
        zip_name=zip_name,
        file_size=file_size,
        is_image=is_image,
        is_video=is_video,
        is_text=is_text_like,
        highlighted_content=highlighted_content,
        is_gallery=is_gallery,
        image_files=image_files,
    )


@app.route("/download/<zip_name>")
async def download_file(zip_name):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], zip_name)
    if not os.path.exists(file_path):
        return "File not found", 404
    return await send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=1654)
