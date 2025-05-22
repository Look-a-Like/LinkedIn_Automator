from flask import Blueprint, request, session, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from flask_cors import CORS

login_bp = Blueprint('login', __name__)
CORS(login_bp)

@login_bp.route('/login', methods=['POST'])
def login():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400

        options = webdriver.ChromeOptions()
        # Removed headless mode to see the browser
        # Added window size for better visibility
        options.add_argument('--start-maximized')
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        try:
            driver.get('https://www.linkedin.com/login')
            # Added delay to see the page load
            time.sleep(2)
            
            # Type email with delay to see the automation
            email_field = driver.find_element(By.ID, 'username')
            for char in email:
                email_field.send_keys(char)
                time.sleep(0.1)
            
            time.sleep(1)
            
            # Type password with delay to see the automation
            password_field = driver.find_element(By.ID, 'password')
            for char in password:
                password_field.send_keys(char)
                time.sleep(0.1)
                
            time.sleep(1)
            password_field.send_keys(Keys.RETURN)
            
            # Wait longer to see if login is successful
            time.sleep(5)
            
            if 'feed' in driver.current_url:
                session['linkedin_email'] = email
                session['linkedin_password'] = password
                session['linkedin_logged_in'] = True
                return jsonify({'message': 'Logged in to LinkedIn successfully'})
            return jsonify({'message': 'Login failed'}), 401
            
        finally:
            driver.quit()
            
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500