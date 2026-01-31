import os
import time
import tempfile
import subprocess
from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CLEANUP ---
try:
    subprocess.run(["pkill", "-f", "chromedriver"], check=False)
except: 
    pass

app = Flask(__name__)
app.secret_key = 'vtu_final_secret'

# --- DATABASE CONNECTION ---
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://127.0.0.1:27017/')

db = None
students_col = None
db_connected = False

def connect_db():
    """Attempt to connect to MongoDB with robust error handling"""
    global db, students_col, db_connected
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        db = client['university_db']
        students_col = db['students']
        db_connected = True
        print("✅ Database Connected Successfully!")
        return True
    except Exception as e:
        db_connected = False
        print(f"❌ DATABASE CONNECTION FAILED: {str(e)}")
        return False

# Attempt connection on startup
connect_db()

# --- BROWSER INITIALIZATION ---
driver = None

def init_driver():
    """Initialize Headless Chrome with Popup Permissions"""
    global driver
    if driver is None:
        print("🔵 Initializing Invisible Browser...")
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # FIX: Force Allow Popups via Preferences
        prefs = {"profile.default_content_setting_values.popups": 1}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--disable-popup-blocking")
        
        # Handle Binary Location for Render
        if os.environ.get('CHROME_BIN'):
            chrome_options.binary_location = os.environ.get('CHROME_BIN')
        else:
            chrome_options.binary_location = "/usr/bin/chromium"
        
        user_data_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            print("✅ Browser Started Successfully")
        except Exception as e:
            print(f"❌ Browser Error: {e}")
            # Fallback for local testing if system chrome is available
            chrome_options.binary_location = None
            driver = webdriver.Chrome(options=chrome_options)

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_captcha')
def get_captcha():
    global driver
    try:
        if driver is None: init_driver()
        
        # Retry logic for page load
        try:
            driver.get("https://results.vtu.ac.in/D25J26Ecbcs/index.php")
        except:
            if driver: 
                try: driver.quit()
                except: pass
            driver = None
            init_driver()
            driver.get("https://results.vtu.ac.in/D25J26Ecbcs/index.php")

        wait = WebDriverWait(driver, 15)
        captcha_img = wait.until(EC.presence_of_element_located((By.XPATH, "//img[contains(@src, 'captcha')]")))
        
        # Scroll into view to ensure clean screenshot
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", captcha_img)
        time.sleep(0.5)
        
        return captcha_img.screenshot_as_png, 200, {'Content-Type': 'image/png'}
    except Exception as e:
        return "Browser Error", 500

@app.route('/leaderboard')
def get_leaderboard():
    """Return Leaderboard with Sorting Options"""
    global students_col, db_connected
    
    if not db_connected or students_col is None:
        if not connect_db():
            return jsonify({'status': 'error', 'message': 'Database Unavailable'})
    
    # Get sort parameters
    sort_by = request.args.get('sort', 'total_marks')
    order = request.args.get('order', 'desc')

    try:
        # 1. Fetch All Students
        all_students = list(students_col.find(
            {}, 
            {'_id': 0, 'usn': 1, 'name': 1, 'total_marks': 1, 'sgpa': 1, 'sgpa_float': 1, 'percentage': 1}
        ))
        
        # 2. Assign Merit Ranks (Always based on Marks Descending)
        all_students.sort(key=lambda x: x.get('total_marks', 0), reverse=True)
        for index, student in enumerate(all_students):
            student['rank'] = index + 1
            if 'percentage' not in student: student['percentage'] = "N/A"

        # 3. Apply User Sort Preference
        reverse_order = True if order == 'desc' else False
        
        if sort_by == 'sgpa':
            all_students.sort(key=lambda x: x.get('sgpa_float', 0.0), reverse=reverse_order)
        elif sort_by == 'total_marks':
            all_students.sort(key=lambda x: x.get('total_marks', 0), reverse=reverse_order)
        elif sort_by == 'rank':
            all_students.sort(key=lambda x: x.get('rank', 9999), reverse=reverse_order)

        # 4. Limit to top 100 of current view
        return jsonify({'status': 'success', 'data': all_students[:100]})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/fetch_result', methods=['POST'])
def fetch_result():
    """Fetch Result, Calculate Percentage, Save to DB"""
    global students_col, db_connected
    
    if not db_connected: connect_db()
    
    usn = request.form['usn'].strip().upper()
    captcha_text = request.form['captcha'].strip()
    
    # DBIT Restriction
    if not (usn.startswith('1DB23CS') or usn.startswith('1DB24CS')):
        return jsonify({'status': 'error', 'message': 'Invalid USN! Only 1DB23CS... allowed'})
    
    if len(usn) != 10:
        return jsonify({'status': 'error', 'message': 'Invalid USN Length (Must be 10)'})
    
    try:
        if not driver: init_driver()
        
        # Ensure we are on the right page
        if "results.vtu.ac.in" not in driver.current_url:
            driver.get("https://results.vtu.ac.in/D25J26Ecbcs/index.php")
        
        wait = WebDriverWait(driver, 15)
        
        # Fill Form
        wait.until(EC.presence_of_element_located((By.NAME, "lns"))).send_keys(usn)
        wait.until(EC.presence_of_element_located((By.NAME, "captchacode"))).send_keys(captcha_text)
        
        # JS Click (Bypasses overlays)
        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']")))
        driver.execute_script("arguments[0].click();", submit_btn)
        
        # Handle Alerts (Invalid Captcha)
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            txt = alert.text
            alert.accept()
            return jsonify({'status': 'error', 'message': f"VTU Says: {txt}"})
        except: pass

        # Handle Result Window
        try:
            WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
            driver.switch_to.window(driver.window_handles[-1])
        except:
            return jsonify({'status': 'error', 'message': 'Result Window did not open. Reload Captcha.'})

        # Parse and Save
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        student_data = parse_result_page(soup, usn)
        
        if student_data['name'] != "Unknown":
            if db_connected:
                students_col.update_one({'usn': usn}, {'$set': student_data}, upsert=True)
                
                # Calculate live rank stats
                my_total = student_data.get('total_marks', 0)
                uni_rank = students_col.count_documents({'total_marks': {'$gt': my_total}}) + 1
            else:
                uni_rank = "N/A"

            # Close popup
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            
            return jsonify({
                'status': 'success', 
                'data': student_data, 
                'ranks': {'uni_rank': uni_rank, 'coll_rank': "N/A"}
            })
        else:
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            return jsonify({'status': 'error', 'message': 'Could not parse result.'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'System Error: {str(e)}'})

# --- HELPERS ---
def get_credits_2022_cs_5th(sub_code):
    code = sub_code.upper().strip()
    if "BCS501" in code: return 3  
    if "BCS502" in code: return 4  
    if "BCS503" in code: return 4  
    if "BCSL504" in code: return 1 
    if "BCS515" in code or "BCS505" in code: return 3 
    if "BCS586" in code: return 2  
    if "BRMK557" in code: return 3 
    if "BESK508" in code or "BCS508" in code: return 1 
    return 0 

def calculate_grade_point(marks):
    try:
        m = int(marks)
        if 90 <= m <= 100: return 10
        if 80 <= m < 90: return 9
        if 70 <= m < 80: return 8
        if 60 <= m < 70: return 7
        if 55 <= m < 60: return 6
        if 50 <= m < 55: return 5
        if 40 <= m < 50: return 4
        return 0 
    except: return 0

def parse_result_page(soup, usn):
    data = {'usn': usn, 'name': "Unknown", 'sgpa': "0.00", 'sgpa_float': 0.0, 'percentage': "0.00%", 'total_marks': 0, 'subjects': []}
    try:
        # Extract Name
        all_text = list(soup.stripped_strings)
        for i, text in enumerate(all_text):
            if "Student Name" in text and i+3 < len(all_text):
                data['name'] = all_text[i+2].replace(":", "").strip()
                break
        
        # Extract Marks
        div_rows = soup.find_all('div', class_='divTableRow')
        total_credits = 0
        total_gp = 0
        running_total_marks = 0 
        
        for row in div_rows:
            cells = row.find_all('div', class_='divTableCell')
            if len(cells) >= 6:
                try:
                    code = cells[0].text.strip()
                    marks = cells[4].text.strip()
                    credits = get_credits_2022_cs_5th(code)
                    gp = calculate_grade_point(marks)
                    
                    if credits > 0:
                        total_credits += credits
                        total_gp += (credits * gp)
                    
                    running_total_marks += int(marks)
                    data['subjects'].append({
                        'code': code, 'name': cells[1].text.strip(), 
                        'total': marks, 'result': cells[5].text.strip()
                    })
                except: continue
        
        data['total_marks'] = running_total_marks
        
        # Calculate SGPA & Percentage
        if total_credits > 0:
            sgpa_val = total_gp / total_credits
            data['sgpa'] = "{:.2f}".format(sgpa_val)
            data['sgpa_float'] = float(sgpa_val)
            
            # --- UPDATED PERCENTAGE LOGIC ---
            # Formula: (Obtained Marks / 900) * 100
            try:
                perc = (running_total_marks / 900) * 100
                data['percentage'] = "{:.2f}%".format(perc)
            except:
                data['percentage'] = "0.00%"
            
    except Exception as e: print(e)
    return data

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)