from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def navigate_to_job(driver, wait, job_url):
    """Navigates to a job posting and attempts to click 'Easy Apply'."""
    try:
        driver.get(job_url)

        easy_apply_selectors = [
            (By.CLASS_NAME, "jobs-apply-button"),
            (By.XPATH, "//button[contains(text(), 'Easy Apply')]"),
            (By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]")
        ]

        for selector in easy_apply_selectors:
            try:
                button = wait.until(EC.element_to_be_clickable(selector))
                button.click()
                print("✅ Easy Apply Clicked")
                return True
            except:
                continue

        print("❌ 'Easy Apply' button not found.")
        return False

    except Exception as e:
        print(f"❌ Navigation Error: {e}")
        return False
