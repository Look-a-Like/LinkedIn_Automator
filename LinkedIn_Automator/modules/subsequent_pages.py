import time

from selenium.webdriver.common.by import By

from .required_fields import handle_required_fields

def handle_subsequent_pages(driver, resume_data):
    # Keep track of what page we're on
    page_count = 1
    max_pages = 10  # Safety limit

    while page_count < max_pages:
        try:
            # Wait for page to load
            time.sleep(3)
            page_count += 1
            print(f"Processing page {page_count}")

            # Check if we're on the final review page
            review_indicators = [
                "//h3[contains(text(), 'Review your application')]",
                "//button[contains(text(), 'Submit application')]"
            ]

            is_review_page = False
            for indicator in review_indicators:
                if driver.find_elements(By.XPATH, indicator):
                    is_review_page = True
                    break

            if is_review_page:
                print("On final review page")
                try:
                    submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Submit application')]")
                    print("Found Submit application button")
                    # Uncomment to actually submit
                    # submit_button.click()
                    # print("Application submitted successfully!")
                    # time.sleep(3)
                    break
                except Exception as e:
                    print(f"Error finding submit button: {e}")
                    break

            # ===== Handle "Can you start immediately?" question =====

            # Look for the question using various selectors
            start_immediately_indicators = [
                "//span[contains(text(), 'Can you start immediately')]",
                "//legend[contains(., 'Can you start immediately')]",
                "//span[contains(text(), 'start immediately')]",
                # Match the exact text from your image
                "//span[contains(text(), 'We must fill this position urgently. Can you start immediately?')]"
            ]

            found_start_question = False
            for indicator in start_immediately_indicators:
                if driver.find_elements(By.XPATH, indicator):
                    found_start_question = True
                    print("Found 'Can you start immediately?' question")
                    break

            if found_start_question:
                # Try multiple selectors for the "Yes" radio button
                yes_selectors = [
                    # First try the exact ID from your DOM structure
                    "//input[@id='urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:(4140798018,14989759068,multipleChoice)-0']",
                    # Then try more general selectors
                    "//input[@type='radio' and @value='Yes']",
                    "//label[text()='Yes']/preceding-sibling::input[@type='radio']",
                    "//label[contains(text(), 'Yes')]/preceding-sibling::input",
                    # Based on the image you sent
                    "//input[@type='radio'][following-sibling::label[contains(text(), 'Yes')]]"
                ]

                yes_selected = False
                for selector in yes_selectors:
                    try:
                        yes_elements = driver.find_elements(By.XPATH, selector)
                        if yes_elements:
                            yes_radio = yes_elements[0]
                            # Try both click methods
                            try:
                                # Regular click
                                if not yes_radio.is_selected():
                                    yes_radio.click()
                                    print(f"Selected 'Yes' using selector: {selector}")
                                    yes_selected = True
                                    time.sleep(1)
                                    break
                            except:
                                # JavaScript click
                                try:
                                    driver.execute_script("arguments[0].click();", yes_radio)
                                    print(f"Selected 'Yes' using JavaScript click and selector: {selector}")
                                    yes_selected = True
                                    time.sleep(1)
                                    break
                                except:
                                    print(f"JavaScript click failed for: {selector}")
                    except Exception as e:
                        print(f"Error with selector {selector}: {e}")

                if not yes_selected:
                    # Last resort: try clicking the label instead
                    try:
                        yes_label = driver.find_element(By.XPATH, "//label[contains(text(), 'Yes')]")
                        yes_label.click()
                        print("Selected 'Yes' by clicking label")
                        yes_selected = True
                    except Exception as e:
                        print(f"Error clicking Yes label: {e}")

                # Now look for the Review button
                review_button_selectors = [
                    # First try the exact ID from your DOM structure
                    "//button[@id='ember968']",
                    "//button[contains(@aria-label, 'Review your application')]",
                    "//button[contains(text(), 'Review')]",
                    "//button[contains(@class, 'artdeco-button--primary') and contains(., 'Review')]"
                ]

                review_clicked = False
                for selector in review_button_selectors:
                    try:
                        review_buttons = driver.find_elements(By.XPATH, selector)
                        if review_buttons:
                            review_button = review_buttons[0]
                            if review_button.is_displayed() and review_button.is_enabled():
                                review_button.click()
                                print(f"Clicked 'Review' button using selector: {selector}")
                                review_clicked = True
                                time.sleep(3)
                                break
                    except Exception as e:
                        print(f"Error with Review button selector {selector}: {e}")

                if not review_clicked:
                    # Try JavaScript click for Review button
                    try:
                        review_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Review')]")
                        driver.execute_script("arguments[0].click();", review_button)
                        print("Clicked 'Review' button using JavaScript")
                        time.sleep(3)
                    except Exception as e:
                        print(f"JavaScript click for Review button failed: {e}")

                continue  # Skip the rest of the loop and continue to next page

            # ===== Handle experience question fields =====
            experience_fields = driver.find_elements(By.XPATH,
                                                     "//label[contains(text(), 'years of work experience') or contains(text(), 'years of experience')]")

            if experience_fields:
                print(f"Found {len(experience_fields)} experience question fields")

                # Check if resume has experience section
                has_experience = resume_data.get("experience", "") != ""

                # Default value to fill in experience fields
                default_value = "1" if has_experience else "0"

                # Process each experience field
                for field in experience_fields:
                    try:
                        # Get the input field associated with this label
                        input_id = field.get_attribute("for")

                        if input_id:
                            # Find the input element by id
                            input_field = driver.find_element(By.ID, input_id)

                            # Get the label text
                            label_text = field.text.strip()
                            print(f"Processing field: {label_text}")

                            # Default fill with 0 or 1
                            input_field.clear()
                            input_field.send_keys(default_value)
                            print(f"Filled '{label_text}' with {default_value}")
                    except Exception as e:
                        print(f"Error filling experience field: {e}")

            # ===== Handle any other required fields =====
            handle_required_fields(driver)

            # ===== Try to find and click Next, Continue, Review, or Submit button =====
            button_selectors = [
                "//button[contains(@class, 'artdeco-button--primary') and contains(., 'Next')]",
                "//button[contains(@class, 'artdeco-button--primary') and contains(., 'Continue')]",
                "//button[contains(@class, 'artdeco-button--primary') and contains(., 'Review')]",
                "//button[contains(@class, 'artdeco-button--primary') and contains(., 'Submit')]"
            ]

            button_clicked = False
            for selector in button_selectors:
                try:
                    buttons = driver.find_elements(By.XPATH, selector)
                    if buttons:
                        button = buttons[0]
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.strip()
                            button.click()
                            print(f"Clicked '{button_text}' button")
                            button_clicked = True
                            time.sleep(3)

                            # If it was the Submit button, we're done
                            if "Submit" in button_text:
                                print("Application submitted successfully!")
                                return

                            break
                except Exception as e:
                    print(f"Error with button selector {selector}: {e}")

            if not button_clicked:
                print("No navigation buttons found. Application process may be complete or stuck.")
                break

        except Exception as e:
            print(f"Error handling page {page_count}: {e}")
            break
