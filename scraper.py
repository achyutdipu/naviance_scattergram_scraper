from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import json
import pandas as pd
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)
COLLEGE_APPLICATION_NUMBERS_FILE = "college_application_numbers.json"
all_colleges_applied = []
colleges_map = {}
college_dropdown_options = []
try:
    driver.get("https://student.naviance.com/colleges/scattergram")
    driver.implicitly_wait(5)
    college_dropdown_element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[id^='checkbox_']"))
    )
    college_dropdown = Select(college_dropdown_element)
    college_dropdown_options = college_dropdown.options
    all_colleges_applied = [i.text for i in college_dropdown_options]
    pattern = r"(.*?)\((?P<number>\d+).*\)"
    new_all_colleges_applied = []
    for college in all_colleges_applied:
        if college == "N/A":
            continue
        match = re.search(pattern, college)
        assert match, f"Failed to match pattern for college: {college}"
        new_all_colleges_applied.append(match.group(1).strip())
        colleges_map[match.group(1).strip()] = int(match.group("number"))
    all_colleges_applied = new_all_colleges_applied
    colleges_map = dict(sorted(colleges_map.items(), key=lambda x: x[1], reverse=True))
    with open(COLLEGE_APPLICATION_NUMBERS_FILE, "w") as f:
        json.dump(colleges_map, f, indent=2)
except Exception as e:
    driver.quit()
    raise e
detailed_college_names = {"College": [], "Accepted": [], "Accept (%)": [], "Rejected": [], "Reject (%)": [], "Waitlisted": [], "Waitlist (%)": []}
print(college_dropdown_options)
college_dropdown_options = [opt for opt in college_dropdown_options if opt.text != "N/A"]
print(college_dropdown_options)
for i in range(len(college_dropdown_options)):
    original = driver.current_window_handle
    college_dropdown_element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[id^='checkbox_']"))
    )
    college_dropdown = Select(college_dropdown_element)
    college_dropdown.select_by_visible_text(college_dropdown_options[i].text)
    submit_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//*[text()='View Scattergram']"))
    )
    submit_button.click()
    try:
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) == 2)
    except Exception as e:
        print(f"Failed for college {all_colleges_applied[i]} because of error {e}")
        continue
    try:
        driver.switch_to.window(driver.window_handles[1])
        scattergram = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "rechartsScattergram"))
        )
        driver.implicitly_wait(1)
        scattergram_svg = scattergram.find_element(
            By.XPATH, ".//*[local-name()='svg' and contains(@class, 'recharts-surface')]"
        )
        accepted = len(scattergram_svg.find_elements(By.XPATH, ".//*[local-name()='path' and @stroke='#009900']"))
        rejected = len(scattergram_svg.find_elements(By.XPATH, ".//*[local-name()='path' and @stroke='#990000']"))
        waitlisted = colleges_map[all_colleges_applied[i]]-accepted-rejected
        detailed_college_names["College"].append(all_colleges_applied[i])
        detailed_college_names["Accepted"].append(accepted)
        detailed_college_names["Accept (%)"].append(accepted/colleges_map[all_colleges_applied[i]]*100)
        detailed_college_names["Rejected"].append(rejected)
        detailed_college_names["Reject (%)"].append(rejected/colleges_map[all_colleges_applied[i]]*100)
        detailed_college_names["Waitlisted"].append(waitlisted)
        detailed_college_names["Waitlist (%)"].append(waitlisted/colleges_map[all_colleges_applied[i]]*100)
    except Exception as e:
        print(f"Failed for college {all_colleges_applied[i]} because of error {e}")
    finally:
        driver.close()
        driver.switch_to.window(original)
driver.quit()
df = pd.DataFrame(detailed_college_names)
df.to_csv("college_detailed_statistics.csv", index=False, float_format='%.2f')
print("Success")