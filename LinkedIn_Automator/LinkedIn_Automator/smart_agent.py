import re
import yaml
import os
import time
import google.generativeai as genai
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from click_handler import click_next_button
import google.generativeai as genai
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from click_handler import click_next_button

# --- Constants ---
ASK_USER_FLAG = "__ASK_USER__"
GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"

# --- Direct field mappings ---
DIRECT_FIELD_MAPPINGS = {
    # Personal information
    "first name": {"path": ["personal_information", "name"]},
    "last name": {"path": ["personal_information", "surname"]},
    "full name": {"path": ["personal_information", "name"], "combine_with": ["personal_information", "surname"]},
    "email": {"path": ["personal_information", "email"]},
    "phone": {"path": ["personal_information", "phone"]},
    "mobile": {"path": ["personal_information", "phone"]},
    "cell": {"path": ["personal_information", "phone"]},
    "address": {"path": ["personal_information", "address"]},
    "city": {"path": ["personal_information", "city"]},
    "zip": {"path": ["personal_information", "zip_code"]},
    "postal code": {"path": ["personal_information", "zip_code"]},
    "country": {"path": ["personal_information", "country"]},
    "linkedin": {"path": ["personal_information", "linkedin"]},
    "github": {"path": ["personal_information", "github"]},
    # Experience
    "years of experience": {"path": ["experience_details"], "handler": "calculate_years_of_experience"},
    "work experience": {"path": ["experience_details"], "handler": "calculate_years_of_experience"},
    "years of work": {"path": ["experience_details"], "handler": "calculate_years_of_experience"},
    "how many years": {"path": ["experience_details"], "handler": "calculate_years_of_experience"},
    # Education
    "education": {"path": ["education_details"], "handler": "get_highest_education"},
    "highest level of education": {"path": ["education_details"], "handler": "get_highest_education"},
    "highest degree": {"path": ["education_details"], "handler": "get_highest_education"},
    "graduation": {"path": ["education_details"], "handler": "get_graduation_info"},
    "university": {"path": ["education_details"], "handler": "get_university"},
    "institution": {"path": ["education_details"], "handler": "get_university"},
    "degree": {"path": ["education_details"], "handler": "get_degree"},
    "field of study": {"path": ["education_details"], "handler": "get_field_of_study"},
    "major": {"path": ["education_details"], "handler": "get_field_of_study"},
    # Availability
    "start date": {"path": ["job_preferences", "date_availability"], "default": "Immediately"},
    "when can you start": {"path": ["job_preferences", "date_availability"], "default": "Immediately"},
    "start immediately": {"path": ["job_preferences", "date_availability"], "handler": "can_start_immediately"},
    "available to start": {"path": ["job_preferences", "date_availability"], "handler": "can_start_immediately"},
    # Authorization
    "authorized to work": {"path": ["legal_authorization", "work_authorization"], "default": "Yes"},
    "legally authorized": {"path": ["legal_authorization", "work_authorization"], "default": "Yes"},
    "require sponsorship": {"path": ["legal_authorization", "requires_sponsorship"], "default": "No"},
    "visa sponsorship": {"path": ["legal_authorization", "requires_sponsorship"], "default": "No"},
    # Preferences
    "willing to relocate": {"path": ["work_preferences", "open_to_relocation"], "default": "Yes"},
    "open to relocation": {"path": ["work_preferences", "open_to_relocation"], "default": "Yes"},
    "remote work": {"path": ["work_preferences", "remote_work"], "default": "Yes"},
    "work remotely": {"path": ["work_preferences", "remote_work"], "default": "Yes"},
    # Salary
    "salary": {"path": ["salary_expectations", "salary_range_usd"], "handler": "format_salary_expectation"},
    "compensation": {"path": ["salary_expectations", "salary_range_usd"], "handler": "format_salary_expectation"},
    # Checks
    "background check": {"path": ["work_preferences", "willing_to_undergo_background_checks"], "default": "Yes"},
    "drug test": {"path": ["work_preferences", "willing_to_undergo_drug_tests"], "default": "No"},
    # Skills
    "skills": {"path": ["skills"], "handler": "get_skills_list"},
    "proficient in": {"path": ["skills"], "handler": "check_skill"},
    "experience with": {"path": ["skills", "experience_details"], "handler": "check_skill_or_experience"},
    "familiar with": {"path": ["skills"], "handler": "check_skill"},
    "skill level": {"path": ["skills"], "handler": "get_skill_level"},
    # Static sections
    "contact info": {"static": "completed"},
    "resume": {"static": "uploaded"},
    "additional questions": {"handler": "handle_additional_questions"}
}

# --- LinkedIn patterns ---
LINKEDIN_FIELD_PATTERNS = {
    "first_name": ["first name", "firstname", "given name"],
    "last_name": ["last name", "lastname", "surname", "family name"],
    "email": ["email", "e-mail"],
    "phone": ["phone", "mobile", "cell", "telephone"],
    "address": ["address", "street"],
    "city": ["city", "town"],
    "state": ["state", "province", "region"],
    "zip": ["zip", "postal", "postcode"],
    "country": ["country", "nation"],
    "linkedin": ["linkedin", "linkedin url", "linkedin profile"],
    "website": ["website", "portfolio"],
    "github": ["github", "github url", "github profile"]
}


class SmartAgent:
    """
    An agent that uses Selenium to navigate a web form, reads questions,
    uses Google Gemini to answer based on a YAML resume, fills the form,
    and handles cases requiring human input via the console.
    """

    def __init__(self, driver: WebDriver, resume_path: str = "resume_data.yaml"):
        """
        Initializes the SmartAgent.

        Args:
            driver: The Selenium WebDriver instance.
            resume_path: Path to the YAML file containing resume data.
        """
        self.driver = driver
        self.resume_path = os.path.normpath(resume_path)
        print(f"Loading resume from: {self.resume_path}")
        self.resume_data = self._load_resume(self.resume_path)
        self.gemini_model = self._configure_gemini()
        self.answered_questions = set()  # To track questions we've already processed
        self.user_responses = {}  # To store user responses for reuse
        self.failed_fields = []

    def _load_resume(self, resume_path: str) -> dict:
        """Loads resume data from the specified YAML file."""
        if not os.path.exists(resume_path):
            # Try alternate paths if the file doesn't exist
            for alt in ["resume_data.yaml", "final_resume.yaml", "../resume_data.yaml", "../final_resume.yaml",
                        "./resume_data.yaml", "./final_resume.yaml"]:
                if os.path.exists(alt):
                    resume_path = alt
                    break
            else:
                print(f"Error: Resume file not found at {resume_path}")
                return {}

        try:
            with open(resume_path, 'r') as f:
                data = yaml.safe_load(f)
                print("Resume data loaded successfully.")
                return data if data else {}
        except yaml.YAMLError as e:
            print(f"Error parsing resume YAML file: {e}")
            return {}
        except Exception as e:
            print(f"An unexpected error occurred loading the resume: {e}")
            return {}

    def _configure_gemini(self) -> genai.GenerativeModel | None:
        """Configures the Google Generative AI client and model."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Error: GOOGLE_API_KEY environment variable not set.")
            return None
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            print(f"Gemini model '{GEMINI_MODEL_NAME}' configured successfully.")
            return model
        except Exception as e:
            print(f"Error configuring Gemini: {e}")
            return None

    def _check_resume_upload_page(self) -> bool:
        """
        Check if we're on a resume upload page and return True if it is.
        """
        try:
            # Look for common resume upload indicators
            upload_indicators = [
                "//h3[contains(text(),'Resume') or contains(text(),'CV')]",
                "//label[contains(text(),'Resume') or contains(text(),'CV')]",
                "//div[contains(text(),'Upload your resume') or contains(text(),'Upload your CV')]",
                "//button[contains(text(),'Upload Resume') or contains(text(),'Upload CV')]",
                "//input[@type='file' and contains(@accept, '.pdf') or contains(@accept, '.doc')]"
            ]

            for xpath in upload_indicators:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(f"Detected resume upload page: {elements[0].text}")
                    return True

            return False
        except Exception as e:
            print(f"Error checking for resume upload page: {e}")
            return False

    def _skip_resume_upload(self) -> bool:
        """
        Skip the resume upload page by clicking the next button.
        Returns True if successful, False otherwise.
        """
        try:
            # Look for the next button
            next_buttons = [
                "//button[contains(text(),'Next') or contains(text(),'Continue')]",
                "//button[contains(@class,'next') or contains(@class,'continue')]",
                "//a[contains(text(),'Next') or contains(text(),'Continue')]",
                "//input[@type='submit' and (contains(@value,'Next') or contains(@value,'Continue'))]"
            ]

            for xpath in next_buttons:
                buttons = self.driver.find_elements(By.XPATH, xpath)
                if buttons:
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            print("Clicking 'Next' button to skip resume upload")
                            button.click()
                            time.sleep(1)  # Wait for page to load
                            return True

            # Try using the click_next_button function if direct approach fails
            print("Trying alternative method to click next button")
            if click_next_button(self.driver):
                time.sleep(1)  # Wait for page to load
                return True

            print("Failed to find a Next button to skip resume upload")
            return False
        except Exception as e:
            print(f"Error skipping resume upload: {e}")
            return False

    def process_page(self) -> bool:
        """
        Process the current page, checking for special cases like resume upload.
        Returns True if processed successfully, False otherwise.
        """
        try:
            # First check if this is a resume upload page
            if self._check_resume_upload_page():
                print("Resume upload page detected, attempting to skip")
                return self._skip_resume_upload()

            # Otherwise process as a regular page with questions
            print("Processing page questions")
            return self.process_page_questions()

        except Exception as e:
            print(f"Error in process_page: {e}")
            return False

    def run(self):
        """
        Main function to run the SmartAgent. Processes pages until completion.
        """
        try:
            print("Starting SmartAgent...")

            # Wait for initial page load
            time.sleep(2)

            # Keep processing pages until we can't anymore
            page_count = 0
            max_pages = 20  # Safety limit

            while page_count < max_pages:
                print(f"\n--- Processing page {page_count + 1} ---")

                # Process the current page
                if self.process_page():
                    print("Page processed successfully")
                else:
                    print("No processable content found on page")

                # Try to move to the next page
                print("Attempting to move to next page...")

                # Try to click the next button
                if click_next_button(self.driver):
                    print("Successfully clicked next button")
                    page_count += 1
                    time.sleep(2)  # Wait for page transition
                else:
                    print("Could not find next button, assuming we're at the end")
                    break

            print(f"Completed form processing after {page_count} pages")

            if self.failed_fields:
                print(f"WARNING: {len(self.failed_fields)} fields could not be automatically filled:")
                for field in self.failed_fields:
                    print(f"  - {field}")

        except Exception as e:
            print(f"Error in run: {e}")
        finally:
            print("SmartAgent execution completed")

    def submit_application(self) -> bool:
        """
        Specifically handles clicking the submit application button.
        Returns True if successful, False otherwise.
        """
        try:
            print("Attempting to click the Submit application button...")

            # Try multiple strategies to find and click the submit button
            strategies = [
                # Direct approach - exact text match
                "//button[text()='Submit application']",
                # Case insensitive approach
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit application')]",
                # Partial match
                "//button[contains(text(), 'Submit')]",
                # Input type submit
                "//input[@type='submit']",
                # By class (common LinkedIn button classes)
                "//button[contains(@class, 'artdeco-button--primary')]",
                # Any element that looks like a submission button
                "//*[contains(text(), 'Submit') and (name()='button' or name()='a' or name()='input')]"
            ]

            # Try each strategy
            for xpath in strategies:
                try:
                    buttons = self.driver.find_elements(By.XPATH, xpath)

                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            print(f"Found submit button with text: '{button.text}'")

                            # Try direct click
                            try:
                                button.click()
                                print("Successfully clicked submit button")
                                time.sleep(2)  # Wait for submission to process
                                return True
                            except Exception as e:
                                print(f"Direct click failed: {e}")

                                # Try JavaScript click
                                try:
                                    self.driver.execute_script("arguments[0].click();", button)
                                    print("Successfully clicked submit button via JavaScript")
                                    time.sleep(2)
                                    return True
                                except Exception as e2:
                                    print(f"JavaScript click failed: {e2}")

                                # Try Actions click
                                try:
                                    actions = ActionChains(self.driver)
                                    actions.move_to_element(button).click().perform()
                                    print("Successfully clicked submit button via ActionChains")
                                    time.sleep(2)
                                    return True
                                except Exception as e3:
                                    print(f"ActionChains click failed: {e3}")
                except Exception as e:
                    print(f"Error with strategy {xpath}: {e}")
                    continue

            # If we get here, we couldn't find the button
            print("Couldn't find or click the submit application button.")
            return False

        except Exception as e:
            print(f"Error in submit_application: {e}")
            return False

    def check_and_submit_if_final_page(self) -> bool:
        """
        Checks if current page is the final submission page and submits if it is.
        Returns True if submission was attempted, False otherwise.
        """
        try:
            # Check for common submit button patterns
            submit_indicators = [
                "//button[contains(text(), 'Submit application')]",
                "//button[contains(text(), 'Submit')]",
                "//input[@type='submit']"
            ]

            for xpath in submit_indicators:
                if self.driver.find_elements(By.XPATH, xpath):
                    print("Final submission page detected")
                    return self.submit_application()

            return False
        except Exception as e:
            print(f"Error checking for final page: {e}")
            return False

    # Add this to your process_page_questions function (or wherever appropriate)
    def process_page_questions_with_submit_check(self) -> bool:
        """
        Wrapper for process_page_questions that also checks for submission.
        """
        # Process the page as usual
        result = self.process_page()

        # Check if this is a submission page and handle it
        if self.check_and_submit_if_final_page():
            return True

        return result


    def process_page_questions(self) -> bool:
        """
        Process all form questions on the current page.

        Returns:
            bool: True if at least one question was processed, False otherwise
        """
        try:
            # First process any radio buttons and specific types of fields for better accuracy
            self._process_radio_buttons()

            # Process numeric experience fields first
            self._process_experience_fields()

            # Process dropdown/select fields
            self._process_dropdown_fields()

            # Then try to auto-fill standard fields - this will handle common form fields
            self._auto_fill_standard_fields()

            # Look for yes/no questions about location first (special case)
            location_questions = self.driver.find_elements(
                By.XPATH,
                "//label[contains(text(), 'live in') or contains(text(), 'located in')]"
            )

            if location_questions:
                for question in location_questions:
                    self._process_location_question(question)

                # Skip resume upload step if detected
            resume_section_detected = self.driver.find_elements(By.XPATH,"//h3[contains(text(),'Resume') or contains(text(),'CV')]")
            if resume_section_detected:
                print("Resume upload section detected — skipping to next page.")
                click_next_button(self.driver)
                time.sleep(2)
                return True

            # Check for file upload requests
            # upload_elements = self.driver.find_elements(
            #     By.XPATH,
            #     "//input[@type='file'] | //button[contains(text(), 'Upload')] | //label[text()='Photo' or text()='Upload']"
            # )

            # if upload_elements:
            #     self._process_upload_elements(upload_elements)

            # Find all potential question elements
            selectors = [
                ".question-text",
                "label.form-label",
                ".form-question",
                ".question",
                "label:not(.artdeco-checkbox__label):not(.artdeco-radio__label)",
                "legend",  # For radio button groups
                "h3.t-16",  # LinkedIn commonly uses this for question text
                "span.artdeco-text-input__label"  # Another LinkedIn pattern
            ]

            selector_string = ", ".join(selectors)
            question_elements = self.driver.find_elements(By.CSS_SELECTOR, selector_string)

            # If no questions found, check if we're on a LinkedIn section page
            if not question_elements and self._check_linkedin_sections():
                return True

            # Filter out search boxes and already filled fields
            filtered_elements = []
            for elem in question_elements:
                txt = elem.text.strip()

                # Skip if empty or too short
                if not txt or len(txt) < 2:
                    continue

                # Skip search boxes and non-form fields
                if self._is_search_field(elem, txt):
                    print(f"Skipping search field: {txt}")
                    continue

                # Skip location questions we already handled
                if "live in" in txt.lower() or "located in" in txt.lower():
                    if hash(txt) in self.answered_questions:
                        continue

                # Skip if we've already processed this question
                question_hash = hash(txt)
                if question_hash in self.answered_questions:
                    print(f"Already processed question: {txt[:50]}...")
                    continue

                # Skip photo/upload elements we already handled
                if txt.lower() in ["photo", "upload"] :
                    continue

                # Check if input is already filled meaningfully
                input_elem = self._find_input_element_for_question(elem)
                if input_elem:
                    existing_value = input_elem.get_attribute('value')
                    if existing_value and len(existing_value) > 1 and existing_value != "completed":
                        print(f"Field '{txt}' already has value '{existing_value}', marking as processed")
                        self.answered_questions.add(question_hash)
                        continue

                # This element needs processing
                filtered_elements.append(elem)

            # Sort elements by vertical position to process in visual order
            filtered_elements.sort(key=lambda e: e.location['y'])

            # Track how many questions were successfully processed
            processed_count = 0

            for question_element in filtered_elements:
                question_text = question_element.text.strip()
                print(f"\nProcessing question: {question_text}")

                # Special handling for years of experience questions
                if "years of experience" in question_text.lower() or "years of work experience" in question_text.lower():
                    # Skip if we've already processed this type of question
                    if self._handle_experience_question(question_element, question_text):
                        processed_count += 1
                        self.answered_questions.add(hash(question_text))
                        continue

                # Process the question and track if successful
                if self._process_question(question_element, question_text):
                    processed_count += 1
                    self.answered_questions.add(hash(question_text))

                # Short pause between processing elements to avoid race conditions
                time.sleep(0.5)

            # If no fields needed processing but we found questions, consider it a success
            if not filtered_elements and question_elements:
                print("All fields appear to be already filled correctly")
                return True

            return processed_count > 0

        except Exception as e:
            print(f"Error in process_page_questions: {e}")
            return False

    def _process_radio_buttons(self):
        """Specifically find and process radio button groups."""
        try:
            # Look for common yes/no radio button groups
            radio_questions = [
                "Are you comfortable working in an onsite setting?",
                "Are you legally authorized to work in India?",
                "Are you comfortable commuting to this job's location?",
                "Have you completed the following level of education",
                "Do you have a valid work visa?",
                "Are you willing to relocate?",
                "Are you serving Notice with current employer?"
            ]

            for question_text in radio_questions:
                # Try to find the question element
                elements = self.driver.find_elements(
                    By.XPATH,
                    f"//*[contains(text(), '{question_text}')]"
                )

                if not elements:
                    continue

                question_element = elements[0]

                # Find the form/fieldset container
                container = question_element
                for _ in range(5):
                    try:
                        container = container.find_element(By.XPATH, "./..")
                        if container.tag_name.lower() in ["form", "fieldset", "div"]:
                            break
                    except:
                        continue

                # Find the radio buttons
                radio_labels = container.find_elements(By.CSS_SELECTOR, "label")

                # Determine the answer
                answer = None

                # Legal authorization or work visa
                if "legally authorized" in question_text.lower() or "work visa" in question_text.lower():
                    answer = "Yes" if self.resume_data.get("legal_authorization", {}).get(
                        "work_authorization") == "Yes" else "No"

                # Relocation
                elif "relocate" in question_text.lower():
                    answer = "Yes" if self.resume_data.get("work_preferences", {}).get(
                        "open_to_relocation") == "Yes" else "No"

                # Education (bachelor's degree)
                elif "education" in question_text.lower() and "Bachelor" in question_text:
                    # Check education level
                    has_bachelors = False
                    for edu in self.resume_data.get("education_details", []):
                        level = edu.get("education_level", "").lower()
                        if "bachelor" in level or "b.tech" in level or "b.e." in level or "b.s." in level:
                            has_bachelors = True
                            break
                    answer = "Yes" if has_bachelors else "No"

                # Onsite or commuting
                elif "onsite" in question_text.lower() or "commuting" in question_text.lower():
                    answer = "Yes"  # Default to Yes for these questions

                # Notice period
                elif "notice" in question_text.lower():
                    answer = "No"  # Default to No for notice period

                # If we have an answer, try to select it
                if answer:
                    for label in radio_labels:
                        label_text = label.text.strip().lower()
                        if (answer.lower() == "yes" and label_text == "yes") or \
                                (answer.lower() == "no" and label_text == "no"):
                            try:
                                label.click()
                                print(f"Selected {answer} for '{question_text}'")
                                self.answered_questions.add(hash(question_text))
                                time.sleep(0.5)  # Short pause after clicking
                                break
                            except Exception as e:
                                print(f"Error clicking radio label: {e}")
                                # Try via input element
                                try:
                                    for_id = label.get_attribute("for")
                                    if for_id:
                                        radio = self.driver.find_element(By.ID, for_id)
                                        radio.click()
                                        print(f"Selected {answer} via input for '{question_text}'")
                                        self.answered_questions.add(hash(question_text))
                                        time.sleep(0.5)
                                        break
                                except Exception as e2:
                                    print(f"Error clicking via input: {e2}")
        except Exception as e:
            print(f"Error processing radio buttons: {e}")

    def _process_dropdown_fields(self):
        """Find and process dropdown fields."""
        try:
            # Find all select elements
            select_elements = self.driver.find_elements(By.TAG_NAME, "select")

            for select_elem in select_elements:
                # Get the label or question for this dropdown
                label_text = self._get_label_for_input(select_elem)

                if not label_text:
                    continue

                # Skip if already processed
                if hash(label_text) in self.answered_questions:
                    continue

                print(f"Processing dropdown: {label_text}")

                # Determine the appropriate value based on the question
                select_value = None

                # English proficiency
                if "english" in label_text.lower() and "proficiency" in label_text.lower():
                    select_value = "Fluent"

                # Notice period related
                elif "notice" in label_text.lower():
                    select_value = "No"

                # If we have a value, try to select it
                if select_value:
                    try:
                        select = Select(select_elem)

                        # First try exact match
                        try:
                            select.select_by_visible_text(select_value)
                            print(f"Selected '{select_value}' for dropdown '{label_text}'")
                            self.answered_questions.add(hash(label_text))
                            continue
                        except:
                            # Try partial match
                            options = select.options
                            for option in options:
                                if select_value.lower() in option.text.lower():
                                    select.select_by_visible_text(option.text)
                                    print(f"Selected '{option.text}' for dropdown '{label_text}'")
                                    self.answered_questions.add(hash(label_text))
                                    break
                    except Exception as e:
                        print(f"Error selecting from dropdown: {e}")
        except Exception as e:
            print(f"Error processing dropdowns: {e}")

    def _process_experience_fields(self):
        """Find and process years of experience fields."""
        try:
            # Look for experience questions
            experience_labels = self.driver.find_elements(
                By.XPATH,
                "//label[contains(text(), 'years of experience') or contains(text(), 'years of work experience')]"
            )

            for label in experience_labels:
                question_text = label.text.strip()

                # Skip if already processed
                if hash(question_text) in self.answered_questions:
                    continue

                print(f"Processing experience field: {question_text}")

                # Find the input field
                input_id = label.get_attribute("for")
                if not input_id:
                    continue

                try:
                    input_field = self.driver.find_element(By.ID, input_id)

                    # Check if already filled
                    current_value = input_field.get_attribute("value")
                    if current_value and len(current_value) > 0 and current_value.isdigit():
                        print(f"Field already has numeric value: {current_value}")
                        self.answered_questions.add(hash(question_text))
                        continue

                    # Clear any existing non-numeric value
                    input_field.clear()

                    # Determine years based on question
                    years = "0"  # Default

                    # Python experience
                    if "python" in question_text.lower():
                        # Check skills
                        if "Python" in self.resume_data.get("skills", []):
                            years = "1"  # Default to 1 year if Python is listed as a skill
                        else:
                            years = "0"

                    # AWS experience
                    elif "aws" in question_text.lower() or "amazon web services" in question_text.lower():
                        # Check skills
                        if any("AWS" in skill for skill in self.resume_data.get("skills", [])):
                            years = "1"  # Default to 1 year if AWS is listed as a skill
                        else:
                            years = "0"

                    # Other IT/Tech experience
                    elif any(tech in question_text.lower() for tech in
                             ["software", "programming", "development", "coding"]):
                        it_years = self._calculate_it_experience()
                        years = it_years

                    # Fill the field
                    input_field.send_keys(years)
                    print(f"Filled experience field with {years} years")
                    self.answered_questions.add(hash(question_text))
                    time.sleep(0.3)  # Short pause

                except NoSuchElementException:
                    print(f"Could not find input for experience field: {input_id}")
                except Exception as e:
                    print(f"Error filling experience field: {e}")
        except Exception as e:
            print(f"Error processing experience fields: {e}")

    def _handle_experience_question(self, question_element, question_text):
        """Special handler for years of experience questions."""
        try:
            # Find the input element
            input_element = self._find_input_element_for_question(question_element)
            if not input_element:
                return False

            # Only handle text inputs
            if input_element.tag_name.lower() != "input" or input_element.get_attribute("type") not in ["text",
                                                                                                        "number"]:
                return False

            # Check if already filled with a valid number
            current_value = input_element.get_attribute("value")
            if current_value and current_value.isdigit():
                print(f"Experience field already has numeric value: {current_value}")
                return True

            # Clear any existing non-numeric value
            input_element.clear()

            # Determine years based on question
            years = "0"  # Default

            # Python experience
            if "python" in question_text.lower():
                # Check skills
                if "Python" in self.resume_data.get("skills", []):
                    years = "1"  # Default to 1 year if Python is listed as a skill
                else:
                    years = "0"

            # AWS experience
            elif "aws" in question_text.lower() or "amazon web services" in question_text.lower():
                # Check skills
                if any("AWS" in skill for skill in self.resume_data.get("skills", [])):
                    years = "1"  # Default to 1 year if AWS is listed as a skill
                else:
                    years = "0"

            # Communication experience
            elif "communication" in question_text.lower():
                years = "1"  # Default to 1 for communication

            # Other IT/Tech experience
            elif any(tech in question_text.lower() for tech in
                     ["software", "programming", "development", "coding", "information technology"]):
                it_years = self._calculate_it_experience()
                years = it_years

            # Fill the field
            input_element.send_keys(years)
            print(f"Filled experience question with {years} years")
            return True

        except Exception as e:
            print(f"Error handling experience question: {e}")
            return False

    def _is_search_field(self, element, text=None):
        """Check if an element is a search field."""
        try:
            # Check text content for search indicators
            if text and any(term in text.lower() for term in ["search by", "search for", "set job alert"]):
                return True

            # Check for search in element attributes
            input_elem = self._find_input_element_for_question(element)
            if input_elem:
                placeholder = input_elem.get_attribute("placeholder") or ""
                aria_label = input_elem.get_attribute("aria-label") or ""

                if any(term in attr.lower() for term in ["search", "find", "filter"]
                       for attr in [placeholder, aria_label]):
                    return True

                # Check for search in input ID or name
                input_id = input_elem.get_attribute("id") or ""
                input_name = input_elem.get_attribute("name") or ""

                if any(term in attr.lower() for term in ["search", "find", "filter", "query"]
                       for attr in [input_id, input_name]):
                    return True

            return False
        except Exception as e:
            print(f"Error checking if search field: {e}")
            return False

    def _auto_fill_standard_fields(self):
        """Auto-fill standard fields based on input attributes."""
        try:
            # Find all visible inputs excluding hidden and file inputs
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input:not([type='hidden']):not([type='file'])")

            for inp in inputs:
                # Skip if already filled with meaningful content (not just placeholder text)
                existing_value = inp.get_attribute('value')
                if existing_value and len(existing_value) > 1 and existing_value != "completed":
                    print(f"Field already filled with '{existing_value}', skipping")
                    continue

                # Get label text for this input to better identify the field
                field_label = self._get_label_for_input(inp)

                # Skip search boxes and non-form fields
                if field_label and any(term in field_label.lower() for term in ["search", "query", "find"]):
                    print(f"Skipping search field: {field_label}")
                    continue

                # Get various attributes to match against patterns
                identifiers = [
                    (inp.get_attribute('id') or '').lower(),
                    (inp.get_attribute('name') or '').lower(),
                    (inp.get_attribute('aria-label') or '').lower(),
                    (inp.get_attribute('placeholder') or '').lower(),
                    field_label.lower() if field_label else ''
                ]

                # Map common field names directly
                field_type = None
                field_value = None

                # First name handling
                if any("first name" in ident for ident in identifiers):
                    field_type = "first_name"
                    field_value = self.resume_data.get("personal_information", {}).get("name", "")

                # Last name handling
                elif any("last name" in ident for ident in identifiers):
                    field_type = "last_name"
                    field_value = self.resume_data.get("personal_information", {}).get("surname", "")

                # Email handling
                elif any("email" in ident for ident in identifiers):
                    field_type = "email"
                    field_value = self.resume_data.get("personal_information", {}).get("email", "")

                # Phone handling
                elif any(term in " ".join(identifiers) for term in ["phone", "mobile", "cell"]):
                    field_type = "phone"
                    field_value = self.resume_data.get("personal_information", {}).get("phone", "")
                    # Remove country code if present
                    if field_value.startswith("+"):
                        field_value = field_value.split(" ", 1)[-1]
                    if field_value.startswith("+91"):
                        field_value = field_value[3:]

                # City handling
                elif any(term in " ".join(identifiers) for term in ["city", "location"]):
                    field_type = "city"
                    field_value = self.resume_data.get("personal_information", {}).get("city", "")

                # If we found a mapping, fill the field
                if field_type and field_value:
                    try:
                        inp.clear()  # Clear any existing value
                        inp.send_keys(field_value)
                        print(f"Auto-filled {field_type}: {field_value}")
                        continue
                    except Exception as e:
                        print(f"Error filling {field_type}: {e}")

                # If no direct mapping was found, try the pattern-based mapping
                for pattern_type, patterns in LINKEDIN_FIELD_PATTERNS.items():
                    if any(pattern in identifier for pattern in patterns for identifier in identifiers):
                        pattern_value = self._map_question_to_resume_field(pattern_type)
                        if pattern_value and pattern_value != "completed":  # Avoid filling with "completed"
                            try:
                                inp.clear()
                                inp.send_keys(pattern_value)
                                print(f"Auto-filled {pattern_type}: {pattern_value}")
                                break
                            except Exception as e:
                                print(f"Error filling {pattern_type}: {e}")

        except Exception as e:
            print(f"Error in auto-fill: {e}")

    def _get_label_for_input(self, input_element):
        """Get the label text for an input element."""
        try:
            # Try to find label by "for" attribute
            input_id = input_element.get_attribute("id")
            if input_id:
                try:
                    label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                    return label.text.strip()
                except NoSuchElementException:
                    pass

            # Try to find label by proximity
            input_rect = input_element.rect
            input_y = input_rect['y']

            # Find all labels on the page
            labels = self.driver.find_elements(By.TAG_NAME, "label")

            # Find labels close to the input
            closest_label = None
            min_distance = 50  # Max distance in pixels to consider

            for label in labels:
                try:
                    label_rect = label.rect
                    distance = abs(label_rect['y'] - input_y)

                    if distance < min_distance:
                        min_distance = distance
                        closest_label = label
                except:
                    continue

            if closest_label:
                return closest_label.text.strip()

        except Exception as e:
            print(f"Error finding label: {e}")

        return ""

    def _check_linkedin_sections(self) -> bool:
        """Check if we're on a LinkedIn section page."""
        try:
            # Look for common LinkedIn section headers
            contact_info = self.driver.find_elements(By.XPATH, "//h3[contains(text(),'Contact info')]")
            resume_section = self.driver.find_elements(By.XPATH,
                                                       "//h3[contains(text(),'Resume') or contains(text(),'CV')]")
            additional_questions = self.driver.find_elements(By.XPATH, "//h3[contains(text(),'Additional questions')]")

            # Return True if any section is found
            return bool(contact_info or resume_section or additional_questions)
        except:
            return False

    def _process_question(self, elem: WebElement, txt: str) -> bool:
        """Process a single question element."""
        try:
            # Skip known search boxes or non-form fields
            if any(term in txt.lower() for term in ["search", "find jobs", "search by", "search for"]):
                print(f"Skipping search field: {txt}")
                return True  # Return true to prevent re-processing

            # Check if input is a search field by placeholder
            input_elem = self._find_input_element_for_question(elem)
            if input_elem and input_elem.get_attribute('placeholder'):
                placeholder = input_elem.get_attribute('placeholder').lower()
                if "search" in placeholder or "find" in placeholder:
                    print(f"Skipping search field with placeholder: {placeholder}")
                    return True

            # Check if this input is already filled
            if input_elem:
                existing_value = input_elem.get_attribute('value')
                if existing_value and len(existing_value) > 1 and existing_value != "completed":
                    print(f"Field '{txt}' already filled with '{existing_value}', skipping")
                    return True  # Consider it processed

            # Special case for experience questions
            if "years of experience" in txt.lower() or "years of work experience" in txt.lower():
                skill_mentioned = None
                # Check if a specific skill is mentioned
                for skill in self.resume_data.get("skills", []):
                    if skill.lower() in txt.lower():
                        skill_mentioned = skill
                        break

                if "communication" in txt.lower():
                    # Set a reasonable default for communication experience
                    answer = "1"  # Default value
                    try:
                        if input_elem and input_elem.tag_name.lower() == "input":
                            input_elem.clear()
                            input_elem.send_keys(answer)
                            print(f"Filled communication experience with: {answer} years")
                            return True
                    except Exception as e:
                        print(f"Error filling communication experience: {e}")

                if "information technology" in txt.lower() or "it experience" in txt.lower():
                    # Calculate IT experience based on resume
                    answer = self._calculate_it_experience()
                    try:
                        if input_elem and input_elem.tag_name.lower() == "input":
                            input_elem.clear()
                            input_elem.send_keys(answer)
                            print(f"Filled IT experience with: {answer} years")
                            return True
                    except Exception as e:
                        print(f"Error filling IT experience: {e}")

            # Check if we already have a user response for this question
            answer = self.user_responses.get(txt)

            # If no stored response, try to get answer from resume data
            if not answer:
                answer = self._map_question_to_resume_field(txt)

                # If mapping fails or indicates we should ask user, try Gemini
                if not answer or answer == ASK_USER_FLAG:
                    if self.gemini_model:
                        gemini_answer = self._ask_gemini(txt)
                        if gemini_answer and gemini_answer != ASK_USER_FLAG:
                            answer = gemini_answer

                # If still no answer or we should ask user, ask user
                if not answer or answer == ASK_USER_FLAG:
                    # Show a visual alert to make question obvious
                    self._show_user_prompt_alert(txt)

                    # Get user input
                    answer = self._ask_user(elem)

                    # Remove the alert
                    self._dismiss_alert()

                    # Store response for future reference
                    if answer:
                        self.user_responses[txt] = answer

            # Fill the form with the answer if we have one
            if answer == "completed" or answer == "Search by title, skill, or company":
                print(f"Skipping filling '{txt}' with '{answer}' as this is likely incorrect")
                return False

            return self._fill_form(elem, answer) if answer else False

        except Exception as e:
            print(f"Error processing question '{txt}': {e}")
            return False

    def _calculate_it_experience(self) -> str:
        """Calculate IT experience based on resume data."""
        # Check for IT-related fields of study in education
        it_education = False
        for edu in self.resume_data.get("education_details", []):
            field = edu.get("field_of_study", "").lower()
            if "computer" in field or "IT" in field or "information technology" in field or "computer science" in field:
                it_education = True
                break

        # Check for IT-related positions in experience
        it_years = 0
        for exp in self.resume_data.get("experience_details", []):
            position = exp.get("position", "").lower()
            description = exp.get("description", "").lower()
            company = exp.get("company", "").lower()

            # Check if this is an IT-related position
            if any(term in position.lower() for term in ["developer", "engineer", "software", "IT", "tech", "program",
                                                         "analyst", "data", "system", "network", "web", "computer"]):
                # Get years of experience for this position
                period = exp.get("employment_period", "")
                if period:
                    parts = period.split("–")
                    if len(parts) < 2:
                        parts = period.split("-")

                    if len(parts) == 2:
                        # Calculate years
                        try:
                            start_year = int(''.join(filter(str.isdigit, parts[0].strip()[-4:])))
                            end_part = parts[1].strip()

                            if "present" in end_part.lower() or "current" in end_part.lower():
                                end_year = 2025  # Current year
                            else:
                                end_year = int(''.join(filter(str.isdigit, end_part[-4:])))

                            years_diff = end_year - start_year
                            if years_diff >= 0:
                                it_years += years_diff
                        except Exception as e:
                            print(f"Error calculating years: {e}")

        # If we have IT education but no explicit IT experience, count at least 1 year
        if it_education and it_years == 0:
            it_years = 1

        return str(it_years)

    def _map_question_to_resume_field(self, question_text: str) -> str:
        """
        Map a question to a resume field using direct mappings.

        Args:
            question_text: The question text

        Returns:
            str: The answer from resume data, or empty string if not found
        """
        question_lower = question_text.lower()

        # Special case for location questions (e.g., "Do you live in Mumbai?")
        location_match = re.search(r"live in ([A-Za-z\s]+)", question_lower)
        if location_match:
            location = location_match.group(1).strip().rstrip('?')
            user_city = self.resume_data.get("personal_information", {}).get("city", "")
            return "Yes" if location.lower() == user_city.lower() else "No"

        # Skip photo/upload fields - these need special handling
        if question_text.lower() in ["photo", "upload"] or "upload" in question_lower:
            return ""  # These will be handled separately

        # Check each pattern in our mappings
        for pattern, mapping_info in DIRECT_FIELD_MAPPINGS.items():
            if pattern in question_lower:
                # Handle static responses
                if 'static' in mapping_info:
                    return mapping_info['static']

                # Handle custom handlers
                if 'handler' in mapping_info:
                    handler_name = mapping_info['handler']
                    handler_method = getattr(self, f"_handle_{handler_name}", None)

                    if handler_method:
                        response = handler_method(question_text, mapping_info)
                        if response and response != ASK_USER_FLAG:
                            return response

                # Handle direct path mapping
                if 'path' in mapping_info:
                    data = self._traverse_path(mapping_info['path'])
                    if data:
                        # Format data based on type
                        if isinstance(data, list):
                            if all(isinstance(item, str) for item in data):
                                return ', '.join(data)
                            elif all(isinstance(item, dict) for item in data):
                                return str(len(data))  # Return count for list of dicts
                        return str(data)

                    # If path doesn't exist but we have a default, use it
                    if 'default' in mapping_info:
                        return mapping_info['default']

                    # No data and no default, ask user
                    return ASK_USER_FLAG

        # No mapping found
        return ""

    def _traverse_path(self, path: list) -> any:
        """Follow a path in the resume data dictionary."""
        data = self.resume_data
        for key in path:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return None
        return data

    def _handle_calculate_years_of_experience(self, question_text: str, mapping_info: dict) -> str:
        """
        Calculate years of experience from resume data.

        Args:
            question_text: The question being asked
            mapping_info: The mapping information from DIRECT_FIELD_MAPPINGS

        Returns:
            str: The calculated years of experience or ASK_USER_FLAG
        """
        try:
            experience_entries = self.resume_data.get("experience_details", [])

            if not experience_entries:
                return "0"  # No experience

            # Check for specific skill mention in the question
            skill_mentioned = None
            for skill in self.resume_data.get("skills", []):
                if skill.lower() in question_text.lower():
                    skill_mentioned = skill
                    break

            total_years = 0
            current_year = 2025  # Current year

            for exp in experience_entries:
                # Skip entries not related to the skill if a skill was mentioned
                if skill_mentioned and skill_mentioned.lower() not in exp.get("position",
                                                                              "").lower() and skill_mentioned.lower() not in exp.get(
                        "description", "").lower():
                    continue

                # Check if we have employment period
                period = exp.get("employment_period", "")
                if not period:
                    continue

                # Try to parse the period format (assuming "Month Year – Month Year" or similar)
                parts = period.split("–")
                if len(parts) < 2:
                    parts = period.split("-")  # Try alternative dash

                if len(parts) == 2:
                    # Get end year (or current if still employed)
                    end_part = parts[1].strip()
                    if "present" in end_part.lower() or "current" in end_part.lower():
                        end_year = current_year
                    else:
                        # Extract year from "Month Year" format
                        end_part_words = end_part.split()
                        end_year = int(end_part_words[-1]) if end_part_words and end_part_words[
                            -1].isdigit() else current_year

                    # Get start year
                    start_part = parts[0].strip()
                    start_part_words = start_part.split()
                    start_year = int(start_part_words[-1]) if start_part_words and start_part_words[
                        -1].isdigit() else end_year

                    # Add years difference
                    years_diff = end_year - start_year
                    if years_diff >= 0:
                        total_years += years_diff

            # If we didn't find any valid experience for a skill query, ask user
            if skill_mentioned and total_years == 0:
                return ASK_USER_FLAG

            return str(total_years)

        except Exception as e:
            print(f"Error calculating years of experience: {e}")
            return ASK_USER_FLAG

    def _handle_get_highest_education(self, question_text: str, mapping_info: dict) -> str:
        """
        Get highest education level from resume data.

        Args:
            question_text: The question being asked
            mapping_info: The mapping information from DIRECT_FIELD_MAPPINGS

        Returns:
            str: The highest education level or ASK_USER_FLAG
        """
        education_entries = self.resume_data.get("education_details", [])

        if not education_entries:
            return ASK_USER_FLAG

        # Define education levels and their hierarchy
        education_hierarchy = {
            "doctorate": 6,
            "phd": 6,
            "master": 5,
            "ms": 5,
            "mba": 5,
            "bachelor": 4,
            "bs": 4,
            "ba": 4,
            "btech": 4,
            "associate": 3,
            "diploma": 2,
            "certificate": 1,
            "high school": 0,
            "secondary": 0
        }

        highest_level = None
        highest_rank = -1

        for edu in education_entries:
            level = edu.get("education_level", "").lower()

            # Find the highest matching level
            for key, rank in education_hierarchy.items():
                if key in level and rank > highest_rank:
                    highest_level = edu.get("education_level", "")
                    highest_rank = rank

        if highest_level:
            # If question asks for field of study too
            if "field" in question_text.lower() or "major" in question_text.lower():
                # Find the field for this highest education
                for edu in education_entries:
                    if edu.get("education_level", "").lower() == highest_level.lower():
                        field = edu.get("field_of_study", "")
                        if field:
                            return f"{highest_level} in {field}"

            return highest_level

        return ASK_USER_FLAG

    def _handle_get_university(self, question_text: str, mapping_info: dict) -> str:
        """Get the university/institution name from highest education."""
        education_entries = self.resume_data.get("education_details", [])
        if not education_entries:
            return ASK_USER_FLAG

        # First try to get the highest education entry
        highest_edu = self._handle_get_highest_education(question_text, mapping_info)

        # If we found a highest education, find its institution
        if highest_edu and highest_edu != ASK_USER_FLAG:
            for edu in education_entries:
                if edu.get("education_level", "") == highest_edu or highest_edu.startswith(
                        edu.get("education_level", "")):
                    if "institution" in edu:
                        return edu["institution"]

        # If no match by level, just return the most recent institution
        for edu in education_entries:
            if "institution" in edu:
                return edu["institution"]

        return ASK_USER_FLAG

    def _handle_get_field_of_study(self, question_text: str, mapping_info: dict) -> str:
        """Get the field of study/major from highest education."""
        education_entries = self.resume_data.get("education_details", [])
        if not education_entries:
            return ASK_USER_FLAG

        # First try to get the highest education entry
        highest_edu = self._handle_get_highest_education(question_text, mapping_info)

        # If we found a highest education, find its field of study
        if highest_edu and highest_edu != ASK_USER_FLAG:
            for edu in education_entries:
                if edu.get("education_level", "") == highest_edu or highest_edu.startswith(
                        edu.get("education_level", "")):
                    if "field_of_study" in edu:
                        return edu["field_of_study"]

        # If no match by level, just return the most recent field of study
        for edu in education_entries:
            if "field_of_study" in edu:
                return edu["field_of_study"]

        return ASK_USER_FLAG

    def _handle_get_degree(self, question_text: str, mapping_info: dict) -> str:
        """Get the degree type from highest education."""
        return self._handle_get_highest_education(question_text, mapping_info)

    def _handle_get_graduation_info(self, question_text: str, mapping_info: dict) -> str:
        """Get graduation year from the highest education."""
        education_entries = self.resume_data.get("education_details", [])
        if not education_entries:
            return ASK_USER_FLAG

        # Find the highest education and its graduation year
        highest_edu = self._handle_get_highest_education(question_text, mapping_info)

        if highest_edu and highest_edu != ASK_USER_FLAG:
            for edu in education_entries:
                if edu.get("education_level", "") == highest_edu or highest_edu.startswith(
                        edu.get("education_level", "")):
                    return edu.get("year_of_completion", ASK_USER_FLAG)

        # If we can't match by level, return most recent graduation year
        most_recent = None
        for edu in education_entries:
            if "year_of_completion" in edu and edu["year_of_completion"]:
                yr = edu["year_of_completion"]
                if not most_recent or yr > most_recent:
                    most_recent = yr

        return most_recent if most_recent else ASK_USER_FLAG

    def _handle_can_start_immediately(self, question_text: str, mapping_info: dict) -> str:
        """
        Determine if candidate can start immediately.

        Args:
            question_text: The question being asked
            mapping_info: The mapping information from DIRECT_FIELD_MAPPINGS

        Returns:
            str: "Yes", "No", or ASK_USER_FLAG
        """
        availability = self.resume_data.get("job_preferences", {}).get("date_availability", "")

        if not availability:
            return "Yes"  # Default to Yes if not specified

        # Check for immediate availability terms
        immediate_terms = ["immediate", "right now", "asap", "right away", "now"]

        for term in immediate_terms:
            if term in availability.lower():
                return "Yes"

        # If not immediate, but we have some availability info, return No
        return "No"

    def _handle_format_salary_expectation(self, question_text: str, mapping_info: dict) -> str:
        """
        Format salary expectation from resume data.

        Args:
            question_text: The question being asked
            mapping_info: The mapping information from DIRECT_FIELD_MAPPINGS

        Returns:
            str: Formatted salary or ASK_USER_FLAG
        """
        salary = self.resume_data.get("salary_expectations", {}).get("salary_range_usd", "")

        if not salary:
            return ASK_USER_FLAG

        # Format salary as needed
        return salary

    def _handle_check_skill(self, question_text: str, mapping_info: dict) -> str:
        """
        Check if the candidate has a specific skill.

        Args:
            question_text: The question being asked
            mapping_info: The mapping information from DIRECT_FIELD_MAPPINGS

        Returns:
            str: "Yes", "No", or skill level if known
        """
        skills = self.resume_data.get("skills", [])

        # Extract potential skill from question
        question_lower = question_text.lower()

        # Check each skill against the question
        for skill in skills:
            if skill.lower() in question_lower:
                # If question asks for rating/level, return an estimated level
                if "level" in question_lower or "rating" in question_lower or "proficiency" in question_lower:
                    # For now return a simple "Yes" - could be enhanced with skill level logic
                    return "Yes"
                return "Yes"

        # Manually check common skills that might be phrased differently
        skill_mappings = {
            "microsoft office": ["ms office", "office", "word", "excel", "powerpoint"],
            "programming": ["coding", "development", "software"],
            "customer service": ["client service", "customer support"]
        }

        for mapped_skill, variants in skill_mappings.items():
            for variant in variants:
                if variant in question_lower:
                    # Check if we have the parent skill
                    parent_found = any(mapped_skill.lower() in s.lower() for s in skills)
                    if parent_found:
                        return "Yes"

        # If nothing found, ask the user
        return ASK_USER_FLAG

    def _handle_check_skill_or_experience(self, question_text: str, mapping_info: dict) -> str:
        """
        Check if candidate has skill or experience with something.

        Args:
            question_text: The question being asked
            mapping_info: The mapping information from DIRECT_FIELD_MAPPINGS

        Returns:
            str: "Yes", "No", years of experience, or ASK_USER_FLAG
        """
        # First check skills
        skill_result = self._handle_check_skill(question_text, mapping_info)
        if skill_result != ASK_USER_FLAG:
            return skill_result

        # Then check experience descriptions for relevant keywords
        question_lower = question_text.lower()
        experience_entries = self.resume_data.get("experience_details", [])

        # Extract the thing being asked about, after keywords like "experience with"
        keywords = ["experience with", "experience in", "worked with", "familiar with"]
        topic = None

        for keyword in keywords:
            if keyword in question_lower:
                parts = question_lower.split(keyword)
                if len(parts) > 1:
                    # Get what comes after the keyword
                    topic = parts[1].strip().rstrip('?').strip()
                    break

        if not topic:
            return ASK_USER_FLAG

        # Check experience for this topic
        for exp in experience_entries:
            description = exp.get("description", "").lower()
            position = exp.get("position", "").lower()
            company = exp.get("company", "").lower()

            if topic in description or topic in position or topic in company:
                # Found relevant experience
                return "Yes"

        # If not found in experience either, ask user
        return ASK_USER_FLAG

    def _handle_get_skill_level(self, question_text: str, mapping_info: dict) -> str:
        """
        Get skill level for a specific skill.

        Args:
            question_text: The question being asked
            mapping_info: The mapping information from DIRECT_FIELD_MAPPINGS

        Returns:
            str: Skill level or ASK_USER_FLAG
        """
        skills = self.resume_data.get("skills", [])
        question_lower = question_text.lower()

        # Default levels
        default_levels = ["Beginner", "Intermediate", "Advanced", "Expert"]

        # Extract the skill being asked about
        for skill in skills:
            if skill.lower() in question_lower:
                # For now return a reasonable default
                return "Intermediate"

        return ASK_USER_FLAG

    def _handle_get_skills_list(self, question_text: str, mapping_info: dict) -> str:
        """Return a formatted list of skills."""
        skills = self.resume_data.get("skills", [])
        if not skills:
            return ASK_USER_FLAG

        # If asked for specific types of skills
        question_lower = question_text.lower()

        # Check for technical skills
        if "technical" in question_lower or "programming" in question_lower or "computer" in question_lower:
            tech_skills = []
            tech_keywords = ["python", "java", "c++", "javascript", "html", "css", "sql",
                             "react", "angular", "vue", "node", "database", "aws", "cloud",
                             "programming", "software", "development", "code"]

            for skill in skills:
                if any(kw in skill.lower() for kw in tech_keywords):
                    tech_skills.append(skill)

            if tech_skills:
                return ", ".join(tech_skills)

        # Return all skills if no specific type requested
        return ", ".join(skills)

    def _ask_gemini(self, question: str) -> str:
        """
        Asks the configured Gemini model the question, providing resume context.

        Args:
            question: The question text extracted from the form.

        Returns:
            The answer from Gemini, or the ASK_USER_FLAG if it cannot answer.
        """
        if not self.gemini_model:
            print("Error: Gemini model not configured. Asking user.")
            return ASK_USER_FLAG
        if not self.resume_data:
            print("Warning: Resume data is empty. Gemini may not be able to answer.")
            return ASK_USER_FLAG

        try:
            prompt = f"""
Context: You are an assistant filling out a web form. Answer the user's question based *only* on the information contained within the following YAML data representing a resume.

Resume Data:
```yaml
{yaml.safe_dump(self.resume_data)}
```

Question from the form: {question}

Instructions:
1. Answer the question based ONLY on the resume data provided above.
2. Keep your answer concise and directly relevant to the question.
3. If the exact information isn't in the resume data, respond with "{ASK_USER_FLAG}".
4. For multiple choice/dropdown, match your answer EXACTLY to one of the available options.
5. For yes/no questions where you don't have information, answer with "{ASK_USER_FLAG}".
6. For questions asking about years of experience with a specific skill or technology, calculate based on work history if possible.
7. When answering questions about skills, check both the skills list and experience descriptions.
8. Return *only* the answer, no explanations or additional text.
"""
            response = self.gemini_model.generate_content(prompt)
            answer = response.text.strip()
            return answer
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            print("Falling back to asking user.")
            return ASK_USER_FLAG

    def _show_user_prompt_alert(self, txt: str):
        """Show a visual alert on the page to highlight the question needing user input."""
        js = """
const d=document.createElement('div');d.id='agent-alert';d.style.cssText='position:fixed;top:20%;left:50%;transform:translateX(-50%);background:#f00;color:#fff;padding:10px;border-radius:5px;z-index:9999;';d.innerText=arguments[0];document.body.appendChild(d);
window._int=setInterval(()=>{d.style.opacity=d.style.opacity=='1'?'0.5':'1'},500);
"""
        try:
            self.driver.execute_script(js, txt)
        except Exception as e:
            print(f"Error showing alert: {e}")

    def _dismiss_alert(self):
        """Remove the visual alert from the page."""
        js = """
if(window._int)clearInterval(window._int);
const d=document.getElementById('agent-alert');if(d)d.remove();
"""
        try:
            self.driver.execute_script(js)
        except Exception as e:
            print(f"Error dismissing alert: {e}")

    def _ask_user(self, question_element: WebElement) -> str | None:
        """
        Asks the user to manually provide an answer when Gemini can't answer,
        or when the answer needs human judgment.

        Args:
            question_element: The WebElement containing the question text.

        Returns:
            The user's answer as a string, or None if input fails.
        """
        question_text = question_element.text.strip()
        print("\n" + "-" * 60)
        print(f"ASKING USER: {question_text}")
        print("-" * 60)

        options_found = []
        input_element = self._find_input_element_for_question(question_element)

        # Skip if this is a search field
        if "search" in question_text.lower() or input_element and input_element.get_attribute(
                "placeholder") and "search" in input_element.get_attribute("placeholder").lower():
            print("This appears to be a search field, skipping")
            return None

        # Special case for experience questions - offer numeric options
        if "years of experience" in question_text.lower() or "years of work experience" in question_text.lower():
            print("This is an experience question, please enter a number:")
            while True:
                try:
                    years = input("Enter number of years (0-99): ")
                    if years.isdigit() and 0 <= int(years) <= 99:
                        return years
                    else:
                        print("Please enter a valid number between 0 and 99")
                except Exception as e:
                    print(f"Error: {e}")

        # Try to get options from <select> if that's the input type
        if input_element and input_element.tag_name == 'select':
            try:
                select = Select(input_element)
                options_found = [opt.text for opt in select.options if opt.text]  # Get non-empty option text
                if options_found:
                    print("Available options:")
                    for i, opt in enumerate(options_found):
                        print(f"  [{i}] {opt}")
                    while True:
                        try:
                            idx_str = input(f"Choose option index (0-{len(options_found) - 1}): ")
                            idx = int(idx_str)
                            if 0 <= idx < len(options_found):
                                return options_found[idx]  # Return the actual option text
                            else:
                                print("Invalid index.")
                        except ValueError:
                            print("Invalid input. Please enter a number.")
                        except EOFError:
                            print("Input stream closed. Cannot get user input.")
                            return None
                else:
                    print("Select element found, but it has no options. Please type the value.")
            except Exception as e:
                print(f"Error reading select options: {e}. Please type the value.")

        # If not a select or options couldn't be read, look for radio/checkbox labels
        if not options_found:
            try:
                # Look for labels near the question or input element
                label_elements = self.driver.find_elements(By.XPATH,
                                                           "//label[normalize-space()]")  # Find all non-empty labels

                # Basic filtering: Keep labels that are reasonably close to the question element
                possible_options = []
                q_location = question_element.location['y']
                for lbl in label_elements:
                    try:
                        if abs(lbl.location['y'] - q_location) < 150:  # Arbitrary vertical pixel distance
                            possible_options.append(lbl.text.strip())
                    except:  # Handle stale elements etc.
                        continue

                if possible_options:
                    options_found = list(dict.fromkeys(possible_options))  # Remove duplicates

                    # Filter out options that are actually questions or search fields
                    options_found = [opt for opt in options_found if
                                     "search" not in opt.lower() and
                                     not opt.lower().endswith("?") and
                                     not "years of experience" in opt.lower()]

                    if options_found:
                        print("Possible options based on nearby labels:")
                        for i, opt in enumerate(options_found):
                            print(f"  [{i}] {opt}")
                        while True:
                            try:
                                idx_str = input(
                                    f"Choose option index (0-{len(options_found) - 1}), or type the answer if not listed: ")
                                # Try interpreting as index first
                                try:
                                    idx = int(idx_str)
                                    if 0 <= idx < len(options_found):
                                        return options_found[idx]  # Return the actual option text
                                    else:
                                        print("Index out of range. Treating input as literal answer.")
                                        return idx_str  # Return the typed string
                                except ValueError:
                                    # If not a valid number, assume it's the typed answer
                                    print("Input is not a number. Using it as the literal answer.")
                                    return idx_str
                            except EOFError:
                                print("Input stream closed. Cannot get user input.")
                                return None

            except Exception as e:
                print(f"Could not automatically determine options: {e}")

        # General fallback: Just ask the user to type
        # For experience questions, suggest entering a number
        if "years of experience" in question_text.lower():
            return self._ask_for_years_of_experience(question_text)

        while True:
            try:
                answer = input("Type the exact answer required for the form: ")
                if answer:  # Ensure non-empty input
                    return answer
                else:
                    print("Input cannot be empty.")
            except EOFError:
                print("Input stream closed. Cannot get user input.")
                return None

    def _ask_for_years_of_experience(self, question_text: str) -> str:
        """Special handler for experience questions to ensure numeric input."""
        print("This question asks about years of experience. Please enter a number.")
        while True:
            try:
                years = input("Enter number of years (0-99): ")
                if years.isdigit() and 0 <= int(years) <= 99:
                    return years
                else:
                    print("Please enter a valid number between 0 and 99")
            except Exception as e:
                print(f"Error: {e}")
                return "0"  # Safe fallback

    def _find_input_element_for_question(self, question_element: WebElement) -> WebElement | None:
        """
        Attempts to find the input element associated with a question element.
        Uses common patterns in web forms to locate the appropriate input field.

        Args:
            question_element: The WebElement containing the question text.

        Returns:
            The located input WebElement, or None if not found.
        """
        try:
            # Strategy 1: Check if the question element has a 'for' attribute (is a label)
            elem_id = question_element.get_attribute("for")
            if elem_id:
                try:
                    input_elem = self.driver.find_element(By.ID, elem_id)
                    print(f"Found input by label 'for' attribute: {elem_id}")
                    return input_elem
                except NoSuchElementException:
                    print(f"Label has 'for' attribute: {elem_id}, but no matching input found.")

            # Strategy 2: Try to find inputs inside the same parent container
            parent = question_element.find_element(By.XPATH, "./..")  # Direct parent
            try:
                # Look for common input elements within the parent
                for selector in ["input", "select", "textarea"]:
                    inputs = parent.find_elements(By.TAG_NAME, selector)
                    if inputs:
                        print(f"Found input in parent container: <{selector}>")
                        return inputs[0]  # Return first match
            except Exception as e:
                print(f"Error finding input in parent: {e}")

            # Strategy 3: Look for inputs that follow the question within a reasonable distance
            try:
                following_inputs = self.driver.find_elements(
                    By.XPATH,
                    f"//input[following::*[contains(., '{question_element.text[:20]}')]] | " +
                    f"//select[following::*[contains(., '{question_element.text[:20]}')]] | " +
                    f"//textarea[following::*[contains(., '{question_element.text[:20]}')]]"
                )
                if following_inputs:
                    print("Found input following the question text.")
                    return following_inputs[0]
            except Exception as e:
                print(f"Error finding input following question: {e}")

            # Strategy 4: Find nearest input by vertical distance
            try:
                all_inputs = self.driver.find_elements(By.XPATH, "//input | //select | //textarea")
                if all_inputs:
                    q_y = question_element.location['y']
                    # Find closest input that is below the question
                    candidates = [inp for inp in all_inputs if inp.location['y'] >= q_y]
                    if candidates:
                        closest = min(candidates, key=lambda inp: inp.location['y'] - q_y)
                        print("Found nearest input by vertical position.")
                        return closest
            except Exception as e:
                print(f"Error finding input by position: {e}")

            print("Warning: Could not find input element for the question.")
            return None

        except Exception as e:
            print(f"Error in find_input_element: {e}")
            return None

    def _handle_location_question(self, question_text: str, mapping_info: dict) -> str:
        """
        Handle questions about living in a specific location.

        Args:
            question_text: The question being asked
            mapping_info: The mapping information

        Returns:
            str: "Yes", "No", or ASK_USER_FLAG
        """
        # Extract the location from the question
        # Common pattern: "Do you live in X?"
        location_pattern = r"live in ([A-Za-z\s]+)"
        location_match = re.search(location_pattern, question_text, re.IGNORECASE)

        if not location_match:
            return ASK_USER_FLAG

        location = location_match.group(1).strip().rstrip('?')

        # Get the user's location from resume
        user_city = self.resume_data.get("personal_information", {}).get("city", "")
        user_country = self.resume_data.get("personal_information", {}).get("country", "")

        # Compare locations (ignore case)
        if location.lower() == user_city.lower():
            return "Yes"
        else:
            return "No"

    def _fill_form(self, question_element: WebElement, answer: str) -> bool:
        """
        Attempts to fill the form with the given answer based on input type.

        Args:
            question_element: The WebElement of the question text.
            answer: The answer string (from LLM or human).

        Returns:
            True if filling was successful or likely successful, False otherwise.
        """
        try:
            input_element = self._find_input_element_for_question(question_element)
            if not input_element:
                print(f"Error: Could not find input element for question: {question_element.text[:50]}...")
                return False

            tag = input_element.tag_name.lower()
            elem_type = input_element.get_attribute("type").lower() if tag == "input" else None

            print(f"Attempting to fill answer '{answer}' into element: <{tag}>" + (
                f" type='{elem_type}'" if elem_type else ""))

            # Handle file upload fields
            if tag == "input" and elem_type == "file":
                print("Detected file upload field - this requires manual handling")
                print("Please upload the file manually when prompted")
                # File uploads can't be automated reliably - skip and ask for manual intervention
                self._show_user_prompt_alert(f"Please upload file: {question_element.text}")
                input("Press Enter after you've uploaded the file manually...")
                self._dismiss_alert()
                return True

            # Handle image upload - special case
            if question_element.text.strip().lower() == "photo" or question_element.text.strip().lower() == "upload":
                print("Detected photo upload request - this requires manual handling")
                self._show_user_prompt_alert("Please upload your photo manually")
                input("Press Enter after you've uploaded your photo...")
                self._dismiss_alert()
                return True

            # 1. Dropdown (<select>)
            if tag == "select":
                try:
                    sel = Select(input_element)
                    sel.select_by_visible_text(answer)
                    print(f"Selected dropdown option by text: '{answer}'")
                    return True
                except NoSuchElementException:
                    try:
                        # Fallback: Try selecting by value if text match failed
                        sel.select_by_value(answer)
                        print(f"Selected dropdown option by value: '{answer}'")
                        return True
                    except NoSuchElementException:
                        # Try to find a close match
                        options = [opt.text for opt in sel.options]
                        for option in options:
                            if answer.lower() in option.lower():
                                sel.select_by_visible_text(option)
                                print(f"Selected dropdown option by partial match: '{option}'")
                                return True

                        # For yes/no questions
                        if answer.lower() == "yes":
                            # Look for affirmative options
                            yes_options = ["yes", "true", "1", "affirmative", "agree"]
                            for option in options:
                                if any(yes_opt in option.lower() for yes_opt in yes_options):
                                    sel.select_by_visible_text(option)
                                    print(f"Selected 'yes' option: '{option}'")
                                    return True
                        elif answer.lower() == "no":
                            # Look for negative options
                            no_options = ["no", "false", "0", "negative", "disagree"]
                            for option in options:
                                if any(no_opt in option.lower() for no_opt in no_options):
                                    sel.select_by_visible_text(option)
                                    print(f"Selected 'no' option: '{option}'")
                                    return True

                        print(f"Error: Option '{answer}' not found in dropdown and no match found.")
                        return False
                except Exception as e:
                    print(f"Error interacting with select: {e}")
                    return False

            # 2. Radio button or Checkbox (<input type="radio/checkbox">)
            elif tag == "input" and (elem_type == "radio" or elem_type == "checkbox"):
                # Handle Yes/No radio buttons directly - common case
                if answer.lower() == "yes" or answer.lower() == "no":
                    # Try to find all radio buttons in the form group
                    container = question_element
                    for _ in range(5):
                        try:
                            container = container.find_element(By.XPATH, "./..")
                            if container.tag_name.lower() in ["form", "fieldset", "div"]:
                                break
                        except:
                            break

                    # Look for all radio buttons and labels
                    radio_labels = container.find_elements(By.CSS_SELECTOR, "label")
                    for label in radio_labels:
                        label_text = label.text.strip().lower()
                        if (answer.lower() == "yes" and label_text == "yes") or \
                                (answer.lower() == "no" and label_text == "no"):
                            try:
                                label.click()
                                print(f"Clicked '{label_text}' radio button")
                                return True
                            except:
                                # If clicking label fails, try the input
                                try:
                                    for_id = label.get_attribute("for")
                                    if for_id:
                                        radio = self.driver.find_element(By.ID, for_id)
                                        radio.click()
                                        print(f"Clicked radio button with id '{for_id}' via label")
                                        return True
                                except:
                                    pass

                # If special handling didn't work, fallback to general approach
                try:
                    # First, let's try to find by label text
                    # Find the form or fieldset this input belongs to
                    container = input_element
                    for _ in range(5):  # Go up to 5 levels up
                        try:
                            container = container.find_element(By.XPATH, "./..")
                            if container.tag_name.lower() in ["form", "fieldset", "div"]:
                                break
                        except:
                            break

                    # Look for labels containing the answer text
                    xpath_query = f".//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{answer.lower()}')]"
                    labels = container.find_elements(By.XPATH, xpath_query)

                    if labels:
                        try:
                            # Try clicking the label directly first
                            labels[0].click()
                            print(f"Clicked label with text containing '{answer}'")
                            return True
                        except:
                            # If that fails, try to find the input through the 'for' attribute
                            for_id = labels[0].get_attribute("for")
                            if for_id:
                                try:
                                    radio = self.driver.find_element(By.ID, for_id)
                                    radio.click()
                                    print(f"Clicked radio/checkbox with id '{for_id}' via label")
                                    return True
                                except:
                                    pass

                    # If no matching label found, try finding radios/checkboxes with matching value
                    inputs = container.find_elements(By.XPATH, f".//input[@type='{elem_type}']")

                    for inp in inputs:
                        inp_value = inp.get_attribute("value").lower()
                        if inp_value == answer.lower():
                            inp.click()
                            print(f"Clicked {elem_type} with matching value: '{answer}'")
                            return True

                    # Special handling for yes/no questions
                    if answer.lower() in ["yes", "no"]:
                        # Find all inputs of this type in the container
                        all_inputs = container.find_elements(By.XPATH, f".//input[@type='{elem_type}']")

                        # For yes/no with exactly 2 options, first is usually "yes" and second is "no"
                        if len(all_inputs) == 2:
                            index = 0 if answer.lower() == "yes" else 1
                            try:
                                all_inputs[index].click()
                                print(f"Clicked {index + 1} of 2 {elem_type}s for '{answer}'")
                                return True
                            except:
                                # If clicking the input fails, try to find its label
                                inp_id = all_inputs[index].get_attribute("id")
                                if inp_id:
                                    try:
                                        label = self.driver.find_element(By.XPATH, f"//label[@for='{inp_id}']")
                                        label.click()
                                        print(f"Clicked label for {index + 1} of 2 {elem_type}s")
                                        return True
                                    except:
                                        pass

                    print(f"Could not find a way to select {elem_type} for answer: '{answer}'")
                    return False

                except Exception as e:
                    print(f"Error handling {elem_type}: {e}")
                    return False

            # 3. Text input or Textarea (<input type="text/email/etc.">, <textarea>)
            elif tag == "textarea" or (
                    tag == "input" and elem_type not in ["radio", "checkbox", "submit", "button", "hidden", "file",
                                                         "image"]):
                try:
                    input_element.clear()
                    input_element.send_keys(answer)
                    print(f"Typed '{answer}' into {tag} field.")
                    return True
                except Exception as e:
                    print(f"Error interacting with text input/textarea: {e}")
                    return False

            else:
                print(f"Warning: Unhandled input element type: <{tag}> type='{elem_type}'")
                return False  # Indicate we didn't handle it

        except Exception as e:
            print(f"An unexpected error occurred during form filling: {e}")
            return False

    def answer_next(self) -> bool:
        """
        Process the form questions on the current page and click next.

        Returns:
            True if a question was found and answered, False otherwise.
        """
        success = self.process_page_questions()
        if success:
            print("Clicking 'Next' button...")
            next_clicked = click_next_button(self.driver)
            if not next_clicked:
                print("Warning: Could not click Next/Continue button.")
                return False
            print("Waiting for next page to load...")
            time.sleep(2)  # Wait for page transition
            return True
        else:
            print("Did not click Next button due to form filling failure.")
            return False

    def handle_specific_question(self, question_text: str) -> bool:
        """
        Handle a specific question by text.

        Args:
            question_text: The text of the question to answer

        Returns:
            bool: True if successfully handled, False otherwise
        """
        try:
            # Try to find the question element
            question_element = None
            try:
                # Try to locate the element containing this text
                question_element = self.driver.find_element(
                    By.XPATH,
                    f"//*[contains(text(), '{question_text[:30]}')]"
                )
            except NoSuchElementException:
                print(f"Could not find element for question: {question_text[:50]}")
                # Create a dummy element for processing
                from selenium.webdriver.remote.webelement import WebElement
                class DummyElement:
                    def __init__(self, text):
                        self.text = text

                    def get_attribute(self, attr):
                        return None

                question_element = DummyElement(question_text)

            # Process the question
            return self._process_question(question_element, question_text)

        except Exception as e:
            print(f"Error in handle_specific_question: {e}")
            return False