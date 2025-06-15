from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import yaml
import os
import json
import google.generativeai as genai
import logging
import random
import hashlib

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [DEBUG] %(message)s')
logger = logging.getLogger(__name__)

# In-memory cache for form field mappings
form_cache = {}

# Configure Gemini API (replace with your actual API key)
try:
    genai.configure(api_key='AIzaSyCJmq6kTd67TxzLj4W3en_M_cqqxz5ABEg')
    model = genai.GenerativeModel('gemini-1.5-pro')
except Exception as e:
    print(f"Error configuring Gemini API: {str(e)}")
    raise

class SmartAgent:
    def __init__(self, driver, resume_data):
        """Initialize the SmartAgent with a Selenium driver and resume data."""
        self.driver = driver
        self.resume_data = resume_data
        self.model = model  # Attach Gemini model to the instance

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
        """Fill a form field based on its type using fallback selectors."""
        try:
            selectors = {
                "name": "[name*='name'],.text-input,input[type='text']:not([name*='search'])",
                "email": "[name*='email'],[type='email']",
                "phone": "[id*='phoneNumber-nationalNumber'],[type='text'][id*='phoneNumber']",
                "resume": "[name*='resume'],[type='file'],[accept*='pdf']"
            }
            if field_type in selectors and value:
                field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selectors[field_type]))
                )
                logger.debug(f"Using fallback selector for {field_type}: {selectors[field_type]}")
                if field_type == "resume":
                    field.send_keys(value)
                else:
                    field.clear()
                    field.send_keys(value)
                time.sleep(delay)
                return True
        except Exception as e:
            logger.debug(f"Error filling {field_type} with fallback: {str(e)}")
        return False

    def analyze_form_with_gemini(self, form_html):
        """Analyze the form using Gemini API and return field mappings."""
        form_hash = hashlib.md5(form_html.encode('utf-8')).hexdigest()
        if form_hash in form_cache:
            logger.debug(f"Using cached field mapping for form hash: {form_hash}")
            return form_cache[form_hash]
        
        prompt = f"""
        Analyze this LinkedIn Easy Apply form and return a JSON object where:
        - Keys are the field names or IDs.
        - Values describe the field purpose (use exact terms: 'name', 'email', 'phone', 'resume').
        - Ignore buttons.
        - For each field, check associated labels, placeholders, and attributes.
        Form HTML:
        {form_html}
        """
        try:
            response = self.model.generate_content(prompt)
            mapping = json.loads(response.text)
            form_cache[form_hash] = mapping
            logger.debug(f"Cached field mapping for form hash: {form_hash}")
            return mapping
        except Exception as e:
            logger.debug(f"Error with Gemini API: {str(e)}")
            return {}

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
                    # Try filling fields with fallback selectors
                    fields_filled = 0
                    for field_type, value in [
                        ("name", personal_info.get('name', '')),
                        ("email", personal_info.get('email', '')),
                        ("phone", personal_info.get('phone', '')),
                        ("resume", resume_path)
                    ]:
                        if self.fill_form_field(field_type, value):
                            fields_filled += 1
                    logger.debug(f"Fields filled with fallback: {fields_filled}")

                    # Handle custom experience questions
                    try:
                        labels = self.driver.find_elements(By.XPATH, "//label[contains(text(), 'years of work experience')]")
                        for label in labels:
                            input_id = label.get_attribute('for')
                            if input_id:
                                input_field = self.driver.find_element(By.ID, input_id)
                                random_experience = str(random.randint(1, 4))
                                input_field.clear()
                                input_field.send_keys(random_experience)
                                logger.debug(f"Filled experience field with random value: {random_experience}")
                    except Exception as e:
                        logger.debug(f"Error handling experience questions: {str(e)}")

                    # Use Gemini API if fallback selectors failed
                    if fields_filled == 0:
                        logger.debug("Fallback selectors failed, analyzing form with Gemini API")
                        form_element = self.driver.find_element(By.CSS_SELECTOR, "form")
                        form_html = form_element.get_attribute('outerHTML')
                        field_mapping = self.analyze_form_with_gemini(form_html)
                        
                        for field_identifier, purpose in field_mapping.items():
                            purpose_lower = purpose.lower()
                            value = None
                            if "name" in purpose_lower:
                                value = personal_info.get('name', '')
                            elif "email" in purpose_lower:
                                value = personal_info.get('email', '')
                            elif "phone" in purpose_lower:
                                value = personal_info.get('phone', '')
                            elif "resume" in purpose_lower:
                                value = resume_path
                            
                            if value:
                                try:
                                    element = self.driver.find_element(By.ID, field_identifier)
                                    if "resume" in purpose_lower:
                                        element.send_keys(value)
                                    else:
                                        element.clear()
                                        element.send_keys(value)
                                    time.sleep(1)
                                except Exception as e:
                                    logger.debug(f"Could not locate field {field_identifier}: {str(e)}")
                    
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

# Example usage
if __name__ == "__main__":
    driver = webdriver.Chrome()
    resume_data = SmartAgent(driver, None).load_resume_data()
    agent = SmartAgent(driver, resume_data)
    
    email = "your_email"
    password = "your_password"
    if agent.login(email, password):
        job_url = "https://www.linkedin.com/jobs/view/123456"  # Replace with actual job URL
        agent.apply_to_job(job_url)
    
    driver.quit()