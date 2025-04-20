from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time


def handle_required_fields(driver):
    """
    Find and fill any required fields that are empty.
    This is a basic implementation to be used when the SmartAgent is not available.

    Args:
        driver: Selenium WebDriver instance
    """
    try:
        # Common selectors for required fields (these may need adjustment for your forms)
        required_field_selectors = [
            # LinkedIn specific selectors
            "//div[contains(@class, 'artdeco-text-input--error')]/input",
            "//div[contains(@class, 'artdeco-dropdown--error')]/select",
            # General required field selectors
            "//input[@required and not(@type='hidden') and not(@type='file')]",
            "//select[@required]",
            "//textarea[@required]"
        ]

        required_fields = []
        for selector in required_field_selectors:
            fields = driver.find_elements(By.XPATH, selector)
            for field in fields:
                # Skip if already filled
                if field.get_attribute("value"):
                    continue
                required_fields.append(field)

        if not required_fields:
            print("No empty required fields found.")
            return

        print(f"Found {len(required_fields)} required fields that need filling.")

        for field in required_fields:
            tag_name = field.tag_name.lower()

            # Handle Select dropdown
            if tag_name == "select":
                select = Select(field)
                # Select first non-empty option (usually the second one, skipping the default)
                options = select.options
                if len(options) > 1:  # If there's more than just the default option
                    for i, option in enumerate(options):
                        if option.text and i > 0:  # Skip first option
                            select.select_by_index(i)
                            print(f"Selected option '{option.text}' for required dropdown")
                            break

            # Handle Text Input
            elif tag_name == "input":
                input_type = field.get_attribute("type")
                # Text inputs
                if input_type in ["text", "email", "tel", "number"]:
                    # Find associated label if possible
                    field_id = field.get_attribute("id")
                    label_text = "Unknown Field"
                    if field_id:
                        try:
                            label = driver.find_element(By.XPATH, f"//label[@for='{field_id}']")
                            label_text = label.text
                        except:
                            pass

                    print(f"Need to fill required field: {label_text}")
                    # Get user input for this field
                    user_input = input(f"Enter value for '{label_text}': ")
                    if user_input:
                        field.clear()
                        field.send_keys(user_input)
                        print(f"Filled '{label_text}' with user input")

                # Checkboxes (usually select "Yes" or checked)
                elif input_type == "checkbox" and not field.is_selected():
                    field.click()
                    print("Checked required checkbox")

                # Radio buttons
                elif input_type == "radio" and not field.is_selected():
                    # Usually select "Yes" for radio buttons
                    field.click()
                    print("Selected required radio button")

            # Handle Textarea
            elif tag_name == "textarea":
                # Find associated label if possible
                field_id = field.get_attribute("id")
                label_text = "Text Area"
                if field_id:
                    try:
                        label = driver.find_element(By.XPATH, f"//label[@for='{field_id}']")
                        label_text = label.text
                    except:
                        pass

                print(f"Need to fill required textarea: {label_text}")
                user_input = input(f"Enter text for '{label_text}': ")
                if user_input:
                    field.clear()
                    field.send_keys(user_input)
                    print(f"Filled '{label_text}' textarea")

    except Exception as e:
        print(f"Error handling required fields: {e}")