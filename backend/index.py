from flask import Flask, send_from_directory
from login import login_bp
from resume import resume_bp  # Remove the dot
from info import info_bp
from jobs import jobs_bp
from apply import apply_bp

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key

# Serve frontend files
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/login')
def login_page():
    return send_from_directory('../frontend', 'login.html')

@app.route('/resume')
def resume_page():
    return send_from_directory('../frontend', 'resume.html')

@app.route('/info')
def info_page():
    return send_from_directory('../frontend', 'info.html')

@app.route('/jobs')
def jobs_page():
    return send_from_directory('../frontend', 'jobs.html')

@app.route('/apply')
def apply_page():
    return send_from_directory('../frontend', 'apply.html')

# Register API blueprints
app.register_blueprint(login_bp, url_prefix='/api')
app.register_blueprint(resume_bp, url_prefix='/api')
app.register_blueprint(info_bp, url_prefix='/api')
app.register_blueprint(jobs_bp, url_prefix='/api')
app.register_blueprint(apply_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True)