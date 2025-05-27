import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def handle_resume_upload(driver, resume_path):
    try:
        # Validate if the resume file exists before proceeding
        abs_resume_path = os.path.abspath(resume_path)
        if not os.path.exists(abs_resume_path):
            print(f"❌ Error: Resume file not found at {abs_resume_path}")
            return
        
        # XPath for file input field (ensure it's correct)
        upload_xpath = "//input[@type='file']"

        # Wait for file input field to be present and visible
        wait = WebDriverWait(driver, 10)
        upload_field = wait.until(EC.presence_of_element_located((By.XPATH, upload_xpath)))
        
        print("✅ Upload field found!")

        # Ensure the input field is interactable
        driver.execute_script("arguments[0].style.display = 'block'; arguments[0].removeAttribute('hidden'); arguments[0].removeAttribute('disabled');", upload_field)
        
        # Upload the resume
        upload_field.send_keys(abs_resume_path)
        time.sleep(3)  # Allow time for upload

        print("✅ Resume uploaded successfully!")

    except Exception as e:
        print(f"❌ Error uploading resume: {e}")
