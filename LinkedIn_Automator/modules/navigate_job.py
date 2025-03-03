from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


def navigate_to_job(driver, wait, job_url):
    driver.get(job_url)
    easy_apply_selectors = [
        (By.CLASS_NAME, "jobs-apply-button"),
        (By.XPATH, "//button[contains(., 'Easy Apply')]"),
        (By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]")
    ]

    for selector in easy_apply_selectors:
        try:
            wait.until(EC.element_to_be_clickable(selector)).click()
            return True
        except:
            continue
    return False
