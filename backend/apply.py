from flask import Blueprint, request, session, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

apply_bp = Blueprint('apply', __name__)

def get_job_recommendations(skills):
    # Mock function
    return [
        {'title': 'Python Developer', 'url': 'https://example.com/job1'},
        {'title': 'Flask Expert', 'url': 'https://example.com/job2'}
    ]

@apply_bp.route('/apply_jobs', methods=['POST'])
def apply_jobs():
    if 'linkedin_logged_in' not in session or not session['linkedin_logged_in']:
        return jsonify({'message': 'Please log in to LinkedIn first'}), 401
    email = session['linkedin_email']
    password = session['linkedin_password']
    num_jobs = int(request.form['numJobs'])
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        driver.get('https://www.linkedin.com/login')
        driver.find_element(By.ID, 'username').send_keys(email)
        driver.find_element(By.ID, 'password').send_keys(password + Keys.RETURN)
        time.sleep(5)
        if 'feed' not in driver.current_url:
            return jsonify({'message': 'Login failed'}), 401
        info = session.get('info', {})
        skills = info.get('Skills', [])
        jobs = get_job_recommendations(skills)[:num_jobs]
        for i, job in enumerate(jobs, 1):
            time.sleep(1)  # Simulate applying
            print(f"Applied to job {i}: {job['title']}")
        return jsonify({'message': f'Applied to {len(jobs)} jobs successfully'})
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500
    finally:
        driver.quit()