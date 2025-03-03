import os
import time

from selenium.webdriver.common.by import By


def handle_resume_upload(driver, resume_path):
    upload_field = driver.find_element(By.XPATH, "//input[@type='file' and contains(@accept, '.pdf')]")
    upload_field.send_keys(os.path.abspath(resume_path))
    time.sleep(3)
