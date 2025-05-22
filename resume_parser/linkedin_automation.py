from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

class LinkedInAutomation:
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        self.driver = webdriver.Chrome(options=options)
    
    def login(self, email, password, max_retries=3):
        for attempt in range(max_retries):
            try:
                self.driver.get('https://www.linkedin.com/login')
                
                # Wait for email field and enter email
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
                email_field.send_keys(email)
                
                # Enter password
                password_field = self.driver.find_element(By.ID, "password")
                password_field.send_keys(password)
                
                # Click login button
                login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                login_button.click()
                
                # Wait for login to complete
                time.sleep(5)
                return True
            except Exception as e:
                print(f"Login attempt {attempt + 1} failed: {str(e)}")
                time.sleep(5)
        return False
    
    def apply_to_job(self, job_url, resume_data):
        try:
            for attempt in range(3):
                try:
                    self.driver.get(job_url)
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-control-name='jobdetails_topcard_inapply']"))
                    ).click()
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(3)
        
            # Add explicit waits between form steps
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "first-name"))
            ).send_keys(resume_data['first_name'])
            
            # Initialize form automation
            form_automation = FormAutomation(self.driver, resume_data)
            
            # Click Easy Apply button
            if not form_automation.click_easy_apply():
                return False
            
            # Fill out the application form
            while True:
                if not form_automation.fill_application_form():
                    break
                
                # Check if we've reached the end (Submit button)
                try:
                    submit_button = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Submit application']"))
                    )
                    submit_button.click()
                    time.sleep(2)
                    break
                except:
                    continue
            
            return True
        except Exception as e:
            print(f"Job application failed: {str(e)}")
            return False
    
    def close(self):
        if self.driver:
            self.driver.quit()