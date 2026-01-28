import requests, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

CLOUD_URL = "https://college-rank-list-with-sgpa.onrender.com/submit_result"

def parse(html, usn):
    soup = BeautifulSoup(html,"html.parser")

    data = {
        "usn": usn,
        "name": "Unknown",
        "total_marks": 0
    }

    texts = list(soup.stripped_strings)
    for i,t in enumerate(texts):
        if "Student Name" in t:
            data["name"] = texts[i+2]
            break

    total = 0
    rows = soup.find_all("div", class_="divTableRow")
    for r in rows:
        cells = r.find_all("div", class_="divTableCell")
        if len(cells)>=6:
            try:
                total += int(cells[4].text.strip())
            except: pass

    data["total_marks"] = total
    return data


options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)
driver.get("https://results.vtu.ac.in/D25J26Ecbcs/index.php")

usn = input("Enter USN: ")
captcha = input("Enter CAPTCHA shown in browser: ")

driver.find_element(By.NAME,"lns").send_keys(usn)
driver.find_element(By.NAME,"captchacode").send_keys(captcha)
driver.find_element(By.XPATH,"//input[@type='submit']").click()

time.sleep(3)

html = driver.page_source
result = parse(html, usn)

print("Uploading:", result)

resp = requests.post(CLOUD_URL, json=result)
print(resp.text)

driver.quit()
