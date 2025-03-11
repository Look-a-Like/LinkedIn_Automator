from selenium.webdriver.common.by import By


def click_next_button(driver):
    next_buttons = [
        "//button[contains(., 'Next')]",
        "//button[contains(., 'Continue')]",
        "//button[contains(., 'Review')]"
    ]

    for selector in next_buttons:
        try:
            driver.find_element(By.XPATH, selector).click()
            return True
        except:
            continue
    return False
