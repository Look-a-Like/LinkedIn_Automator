from modules.extract_resume_data import extract_resume_data
from modules.setup_login import setup_and_login
from modules.navigate_job import navigate_to_job
from modules.form_filling import fill_linkedin_form


def main():
    # Configuration
    LINKEDIN_USER = "gudesaidheeran@gmail.com"
    LINKEDIN_PASS = "123-abc@hjk"
    RESUME_PATH = "/Users/dheeranchowdary/Downloads/Dheeran_Chowdary_Resume.pdf"
    JOB_URL = "https://www.linkedin.com/jobs/search/?currentJobId=4169455446&distance=25&geoId=102713980&keywords=machine%20learning%20intern&origin=JOBS_HOME_KEYWORD_HISTORY&refresh=true"

    # Execution Flow
    resume_info = extract_resume_data(RESUME_PATH)
    driver, wait = setup_and_login(LINKEDIN_USER, LINKEDIN_PASS)

    try:
        if navigate_to_job(driver, wait, JOB_URL):
            fill_linkedin_form(driver, resume_info, RESUME_PATH)
            print("Application submitted!")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
