from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import json
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)
COLLEGE_APPLICATION_NUMBERS_FILE = "college_application_numbers.json"
try:
    driver.get("https://student.naviance.com/colleges/scattergram")
    college_dropdown_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "checkbox_2"))
    )
    college_dropdown = Select(college_dropdown_element)
    all_colleges_applied = [i.text for i in college_dropdown.options]
    colleges_map = {}
    pattern = r"(.*?)\((?P<number>\d+).*\)"
    for college in all_colleges_applied:
        if college == "N/A":
            continue
        match = re.search(pattern, college)
        assert match, f"Failed to match pattern for college: {college}"
        colleges_map[match.group(1).strip()] = int(match.group("number"))
    colleges_map = dict(sorted(colleges_map.items(), key=lambda x: x[1], reverse=True))
    with open(COLLEGE_APPLICATION_NUMBERS_FILE, "w") as f:
        json.dump(colleges_map, f, indent=2)
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    driver.quit()