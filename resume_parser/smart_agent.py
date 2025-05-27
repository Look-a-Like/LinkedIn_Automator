from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import yaml
import os

class SmartAgent:
    def __init__(self, driver, resume_data):
        """Initialize the SmartAgent with a Selenium driver and resume data."""
        self.driver = driver
        self.resume_data = resume_data

    def load_resume_data(self):
        """Load resume data from the YAML file."""
        yaml_path = os.path.join('uploads', 'resume_data.yaml')
        with open(yaml_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)

    def login(self, email, password):
        """Log in to LinkedIn using provided credentials."""
        try:
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)  # Delay for page load
            
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(email)
            time.sleep(1)
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(password)
            time.sleep(1)
            
            sign_in_button = self.driver.find_element(By.CSS_SELECTOR, "[type='submit']")
            sign_in_button.click()
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module"))
            )
            print("Successfully logged in")
            return True
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def fill_form_field(self, field_type, value, delay=1):
        """Fill a form field based on its type."""
        try:
            selectors = {
                "name": "[name*='name'],.text-input,input[type='text']:not([name*='search'])",
                "email": "[name*='email'],[type='email']",
                "phone": "[name*='phone'],[type='tel']",
                "resume": "[name*='resume'],[type='file'],[accept*='pdf']"
            }
            
            if field_type in selectors:
                field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selectors[field_type]))
                )
                if field_type == "resume":
                    field.send_keys(value)
                else:
                    field.clear()
                    field.send_keys(value)
                time.sleep(delay)
                return True
        except Exception as e:
            print(f"Error filling {field_type}: {str(e)}")
        return False

    def apply_to_job(self, job_url):
        """Apply to a job at the given URL using resume data."""
        try:
           self.driver.get(job_url)
           time.sleep(3)
            
           easy_apply_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-apply-button"))
            )
           easy_apply_button.click()
           print("Clicked Easy Apply button")
           time.sleep(2)
            
           personal_info = self.resume_data['personal_information']
           resume_path = os.path.abspath(os.path.join('uploads', 'Madhuboni  Basu_resume.pdf'))
            
           while True:
                try:
                    self.fill_form_field("name", personal_info['name'])
                    self.fill_form_field("email", personal_info['email'])
                    self.fill_form_field("phone", personal_info['phone'])
                    self.fill_form_field("resume", resume_path)
                    
                    time.sleep(2)
                    
                    next_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "button[aria-label='Continue to next step'], button[aria-label='Submit application'], button[aria-label='Review your application']")
                        )
                    )
                    
                    if "Submit application" in next_button.get_attribute("aria-label"):
                        time.sleep(2)
                        next_button.click()
                        print("Application submitted successfully")
                        return True
                    else:
                        next_button.click()
                        print("Moved to next step")
                        time.sleep(3)
                        
                except TimeoutException:
                    print("No more steps found or application completed")
                    break
                    
        except TimeoutException:
            print("Timeout waiting for elements to load")
            return False
        except Exception as e:
            print(f"Error during application process: {str(e)}")
            return False