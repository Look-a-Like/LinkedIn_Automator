from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

class FormAutomation:
    def __init__(self, driver, resume_data):
        self.driver = driver
        self.resume_data = resume_data
        self.wait = WebDriverWait(driver, 10)
    
    def click_easy_apply(self):
        try:
            # Wait for and click the Easy Apply button
            easy_apply_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-control-name='jobdetails_topcard_inapply']"))
            )
            easy_apply_button.click()
            return True
        except Exception as e:
            print(f"Failed to click Easy Apply: {str(e)}")
            return False
    
    def fill_form_field(self, field_id, value):
        try:
            field = self.wait.until(
                EC.presence_of_element_located((By.ID, field_id))
            )
            field.clear()
            field.send_keys(value)
            return True
        except:
            return False
    
    def fill_application_form(self):
        try:
            # Common form fields mapping
            field_mappings = {
                "first-name": self.resume_data.get('personal_information', {}).get('name', ''),
                "last-name": self.resume_data.get('personal_information', {}).get('surname', ''),
                "email": self.resume_data.get('personal_information', {}).get('email', ''),
                "phone-number": self.resume_data.get('personal_information', {}).get('phone', '')
            }
            
            # Fill each field if it exists
            for field_id, value in field_mappings.items():
                if value:
                    self.fill_form_field(field_id, value)
            
            # Handle multiple choice questions
            self.handle_multiple_choice_questions()
            
            # Click Next or Submit button
            self.click_next_or_submit()
            
            return True
        except Exception as e:
            print(f"Error filling form: {str(e)}")
            return False
    
    def handle_multiple_choice_questions(self):
        try:
            # Look for common multiple choice questions
            questions = self.driver.find_elements(By.CSS_SELECTOR, "fieldset.artdeco-form-field")
            
            for question in questions:
                question_text = question.find_element(By.CSS_SELECTOR, "legend").text.lower()
                
                # Handle work authorization question
                if "authorized" in question_text or "legally" in question_text:
                    yes_button = question.find_element(By.CSS_SELECTOR, "input[value='Yes']")
                    yes_button.click()
                
                # Handle sponsorship question
                elif "sponsor" in question_text:
                    no_button = question.find_element(By.CSS_SELECTOR, "input[value='No']")
                    no_button.click()
                
                # Handle relocation question
                elif "relocate" in question_text:
                    yes_button = question.find_element(By.CSS_SELECTOR, "input[value='Yes']")
                    yes_button.click()
        except:
            pass
    
    def click_next_or_submit(self):
        try:
            # Try to find and click Next button
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Continue to next step']"))
            )
            next_button.click()
            time.sleep(2)
            return True
        except:
            try:
                # If Next button not found, try Submit button
                submit_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Submit application']"))
                )
                submit_button.click()
                time.sleep(2)
                return True
            except:
                return False