from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException


def click_next_button(driver):
    """
    Attempts to click the next/continue/review button on a form.
    Uses a list of common selectors for these buttons.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        bool: True if a button was successfully clicked, False otherwise
    """
    # List of possible button selectors - XPath based on your approach
    next_buttons = [
        "//button[contains(., 'Next')]",
        "//button[contains(., 'Continue')]",
        "//button[contains(., 'Review')]",
        # Additional selectors that might be useful
        "//input[@type='submit']",
        "//button[@type='submit']",
        "//button[contains(., 'Save')]",
        "//button[contains(., 'Submit')]"
    ]

    # Try each selector
    for selector in next_buttons:
        try:
            # Wait briefly for the button to be clickable
            wait = WebDriverWait(driver, 3)
            button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))

            # Print which button was found (useful for debugging)
            print(f"Found clickable button: {selector}")

            # Click the button
            button.click()
            return True

        except (NoSuchElementException, ElementNotInteractableException, TimeoutException):
            # If this selector didn't work, try the next one
            continue

    # If we got here, no buttons were found/clicked
    print("Could not find any next/continue buttons")
    return False