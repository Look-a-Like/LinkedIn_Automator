import time
import os
from selenium.webdriver.common.by import By
from smart_agent import SmartAgent
from click_handler import click_next_button
from required_fields import handle_required_fields


def handle_subsequent_pages(driver, resume_data, resume_path="resume_data.yaml"):
    """
    Handle subsequent pages in the LinkedIn application process.
    Uses SmartAgent to intelligently fill out form questions.

    Args:
        driver: Selenium WebDriver instance
        resume_data: Dictionary containing resume data
        resume_path: Path to the YAML resume file for SmartAgent

    Returns:
        bool: True if successful, False otherwise
    """
    # Normalize resume path
    resume_path = os.path.normpath(resume_path)
    print(f"Using resume path: {resume_path}")

    # Initialize the SmartAgent
    agent = SmartAgent(driver, resume_path=resume_path)

    # Keep track of what page we're on
    page_count = 1
    max_pages = 10  # Safety limit

    while page_count < max_pages:
        try:
            # Wait for page to load
            time.sleep(3)
            print(f"\n==== Processing page {page_count} ====")
            page_count += 1

            # Check if we're on the final review page
            review_indicators = [
                "//h3[contains(text(), 'Review your application')]",
                "//h2[contains(text(), 'Review your application')]",
                "//button[contains(text(), 'Submit application')]",
                "//button[contains(text(), 'Submit')][@type='submit']",
                "//button[contains(text(), 'Review')][@type='submit']"
            ]

            is_review_page = False
            for indicator in review_indicators:
                if driver.find_elements(By.XPATH, indicator):
                    is_review_page = True
                    break

            if is_review_page:
                print("Detected final review page")
                try:
                    submit_button = driver.find_element(
                        By.XPATH,
                        "//button[contains(text(), 'Submit application') or contains(text(), 'Submit')]"
                    )
                    print("Found Submit application button")
                    # Uncomment to actually submit
                    # submit_button.click()
                    # print("Application submitted successfully!")
                    # time.sleep(3)
                    break
                except Exception as e:
                    print(f"Error finding submit button: {e}")
                    break

            # === Use improved SmartAgent to process all form questions ===
            print("Using SmartAgent to handle form questions...")
            success = agent.process_page_questions_with_submit_check()

            if not success:
                print("SmartAgent couldn't find/process any questions - trying specific known questions...")

                # Try to handle specific known questions that might have been missed

                # === Special handling for "Can you start immediately?" question ===
                start_immediately_indicators = [
                    "//span[contains(text(), 'start immediately')]",
                    "//span[contains(text(), 'Can you start immediately')]",
                    "//legend[contains(., 'Can you start immediately')]",
                    "//label[contains(text(), 'start immediately')]",
                    "//h3[contains(text(), 'start immediately')]",
                    "//span[contains(text(), 'We must fill this position urgently')]"
                ]

                for indicator in start_immediately_indicators:
                    elements = driver.find_elements(By.XPATH, indicator)
                    if elements:
                        print("Found 'Can you start immediately?' question")
                        question_element = elements[0]
                        agent.handle_specific_question(question_element.text)
                        break

                # === Handle experience question fields ===
                experience_fields = driver.find_elements(
                    By.XPATH,
                    "//label[contains(text(), 'years of work experience') or contains(text(), 'years of experience')]"
                )

                if experience_fields:
                    print(f"Found {len(experience_fields)} experience question fields")
                    for field in experience_fields:
                        agent.handle_specific_question(field.text)

                # === Handle education level fields ===
                education_fields = driver.find_elements(
                    By.XPATH,
                    "//label[contains(text(), 'education') or contains(text(), 'degree')]"
                )

                if education_fields:
                    print(f"Found {len(education_fields)} education question fields")
                    for field in education_fields:
                        agent.handle_specific_question(field.text)

                # === Handle work authorization questions ===
                authorization_fields = driver.find_elements(
                    By.XPATH,
                    "//label[contains(text(), 'authorized to work') or contains(text(), 'require sponsorship') or contains(text(), 'visa')]"
                )

                if authorization_fields:
                    print(f"Found {len(authorization_fields)} work authorization question fields")
                    for field in authorization_fields:
                        agent.handle_specific_question(field.text)

            # === Handle any other required fields as a last resort ===
            handle_required_fields(driver)

            # === Try to find and click Next, Continue, Review, or Submit button ===
            print("Clicking 'Next' button...")
            next_clicked = click_next_button(driver)
            if not next_clicked:
                print("Warning: Could not click Next/Continue button with standard handler.")

                # Try more aggressive button finding logic
                button_selectors = [
                    "//button[contains(@class, 'artdeco-button--primary')]",  # LinkedIn primary buttons
                    "//button[contains(@class, 'artdeco-button')]",  # Any LinkedIn button
                    "//button[contains(@class, 'primary')]",  # Common primary button class
                    "//input[@type='submit']",  # Submit inputs
                    "//a[contains(@class, 'button') or contains(@class, 'btn')]"  # Link-buttons
                ]

                for selector in button_selectors:
                    try:
                        buttons = driver.find_elements(By.XPATH, selector)
                        if buttons:
                            # Try to find the right button - typically primary buttons are for moving forward
                            # Click the one that's likely to be the "next" button (usually contains specific text)
                            for button in buttons:
                                button_text = button.text.lower()
                                if any(term in button_text for term in
                                       ["next", "continue", "review", "submit", "save"]):
                                    button.click()
                                    print(f"Clicked button with text: {button.text}")
                                    next_clicked = True
                                    break

                            # If no button with specific text found, just click the first one as a last resort
                            if not next_clicked and buttons:
                                buttons[0].click()
                                print(f"Clicked first available button as fallback: {buttons[0].text}")
                                next_clicked = True

                            if next_clicked:
                                break
                    except Exception as e:
                        print(f"Error trying selector {selector}: {e}")

                if not next_clicked:
                    print("Could not find any button to proceed. Manual intervention needed.")
                    break

            print("Waiting for next page to load...")
            time.sleep(3)  # Wait for page transition

        except Exception as e:
            print(f"Error handling page {page_count}: {e}")
            break

    return True