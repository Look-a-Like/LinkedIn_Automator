from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

upload_xpath = "//input[@type='file']"

try:
    wait = WebDriverWait(driver, 10)
    upload_field = wait.until(EC.presence_of_element_located((By.XPATH, upload_xpath)))
    print("✅ Upload field found!")

    # Check if the input is visible
    if not upload_field.is_displayed():
        print("⚠️ Upload field is hidden! Making it visible.")
        driver.execute_script("arguments[0].style.display = 'block';", upload_field)

    # Upload file
    upload_field.send_keys(r"D:\Academics\Sem6\Software labproject\resume_parser\kashish_resume (3).pdf")
    print("✅ Resume uploaded successfully!")

except Exception as e:
    print(f"❌ Error finding upload field: {e}")
