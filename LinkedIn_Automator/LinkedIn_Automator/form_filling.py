from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from click_handler import click_next_button
from resume_upload import handle_resume_upload
from subsequent_pages import handle_subsequent_pages

def fill_linkedin_form(driver, resume_data, resume_path):
    wait = WebDriverWait(driver, 10)

    try:
        # Select Email from dropdown (if available)
        try:
            email_dropdowns = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, "//select[contains(@id, 'formElement') and contains(@id, 'multipleChoice')]")
            ))
            if email_dropdowns:
                email_dropdown = email_dropdowns[0]
                email_select = Select(email_dropdown)
                if len(email_select.options) > 1:
                    email_select.select_by_index(1)
                    print("Successfully selected email from dropdown")
                else:
                    print("No selectable email options found")
        except Exception as e:
            print(f"Error selecting email: {e}")

        # Select Country Code (if available)
        try:
            country_fields = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, "//select[contains(@id, 'phoneNumber-country')]")
            ))
            if country_fields:
                country_select = Select(country_fields[0])
                try:
                    country_select.select_by_visible_text("India (+91)")
                except:
                    if len(country_select.options) > 1:
                        country_select.select_by_index(1)
                print("Successfully selected country code")
        except Exception as e:
            print(f"Error selecting country code: {e}")

        # Enter Phone Number (if available)
        try:
            phone_fields = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, "//input[contains(@id, 'phoneNumber-nationalNumber')]")
            ))
            if phone_fields:
                phone_input = phone_fields[0]
                phone_number = resume_data["phone"].lstrip("+91")  # Remove country code if present
                phone_input.clear()
                phone_input.send_keys(phone_number)
                print("Successfully entered phone number")
        except Exception as e:
            print(f"Error entering phone number: {e}")

        # Click Next button
        try:
            click_next_button(driver)
            print("Clicked Next button successfully")
        except Exception as e:
            print(f"Error clicking Next button: {e}")

        # Handle Resume Upload Page
        try:
            handle_resume_upload(driver, resume_path)
            print("Handled resume upload successfully")
        except Exception as e:
            print(f"Error uploading resume: {e}")

        # Handle subsequent pages
        try:
            handle_subsequent_pages(driver, resume_data)
            print("Handled subsequent pages successfully")
        except Exception as e:
            print(f"Error handling subsequent pages: {e}")

    except Exception as e:
        print(f"Error in form filling process: {e}")