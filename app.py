import csv
import os
import io
import re
import sqlite3
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'rahul_god_mode_2026'

# --- FILE CONFIGURATION ---
PRESENT_FILE = 'present_data.csv'
ASSET_FOLDER = 'static/assets'
SLIDER_FOLDER = 'static/slider'
DB_FILE = 'admin.db'

os.makedirs(ASSET_FOLDER, exist_ok=True)
os.makedirs(SLIDER_FOLDER, exist_ok=True)

BATCH_TARGETS = {
    'Batch 1': 32, 'Batch 2': 32, 'Batch 3': 32, 'Batch 4': 32, 
    'Batch 5': 32, 'Batch 6': 32, 'Batch 7': 32, 'Batch 8': 32, 
    'Batch 9': 32, 'Batch 10': 32, 'Batch 11': 32, 'Batch 12': 28
}

DISTRICT_MAPPING = {
    "sas nagar": "MOHALI", "s.a.s nagar": "MOHALI", "mohali": "MOHALI",
    "sri muktsar sahib": "MUKTSAR", "muktsar": "MUKTSAR",
    "shahid bhagat singh nagar": "NAWANSHAHR", "sbs nagar": "NAWANSHAHR",
    "taran taran": "TARN TARAN", "firozpur": "FEROZEPUR", "ferozepur": "FEROZEPUR",
    "fatehgarh sahib": "FATEHGARH SAHIB", "rupnagar": "RUPNAGAR", "ropar": "RUPNAGAR"
}

# --- LIVE DATABASE CONFIG ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS admin (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, val TEXT)')
    
    defaults = [
        ('site_title', 'Teachers Training in ICT & Digital Initiatives'),
        ('sub_title', 'Two Days Training Programme at NIELIT Ropar'),
        ('collab_text', 'In Collaboration with SCERT Punjab'),
        ('theme_color', '#4f46e5'),
        ('logo_left', '/static/scert_logo.png'),
        ('logo_right', '/static/edu_logo.png'),
        ('map_height', '520')
    ]
    for k, v in defaults:
        c.execute('INSERT OR IGNORE INTO settings (key, val) VALUES (?, ?)', (k, v))
    conn.commit()
    conn.close()

init_db()

def get_settings():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT key, val FROM settings')
    config = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return config

# --- BULLETPROOF DATA PARSER ---
def normalize_text(text): return ' '.join(str(text).strip().upper().split()) if text else "N/A"

def standardize_date(raw_date):
    if not raw_date: return 'Missing Date'
    date_str = str(raw_date).replace('"', '').replace(',', '-').replace(' ', '').strip()
    parts = date_str.split('-')
    if len(parts) >= 3:
        d, m, y = parts[0], parts[1], parts[2]
        month_map = {'JAN':'01', 'FEB':'02', 'MAR':'03', 'APR':'04', 'MAY':'05', 'JUN':'06', 'JUL':'07', 'AUG':'08', 'SEP':'09', 'OCT':'10', 'NOV':'11', 'DEC':'12'}
        if m.upper() in month_map: m = month_map[m.upper()]
        if len(y) == 2: y = "20" + y
        return f"{d.zfill(2)}-{m.zfill(2)}-{y}"
    return 'Missing Date'

def get_present_data():
    teachers = []
    if not os.path.exists(PRESENT_FILE): return teachers
    try:
        with open(PRESENT_FILE, mode='r', encoding='utf-8-sig') as file: raw_text = file.read()
        raw_text = raw_text.replace('",,,,\r\n', '\n').replace('",,,,\n', '\n').replace('",,,,', '')
        raw_text = re.sub(r'^"|(?<=\n)"', '', raw_text)
        raw_text = raw_text.replace('""', '"')

        reader = csv.DictReader(io.StringIO(raw_text))
        known_keys = ['batch no', 'district', 'start date', 'date', 'school name', 'school', 'name', 'teacher name', 'designation', 'udise code', 'udise', 's.no']
        
        for idx, row in enumerate(reader):
            clean_row = {k.strip().lower(): str(v).strip() for k, v in row.items() if k}
            dist_val = clean_row.get('district', '')
            mapped_dist = DISTRICT_MAPPING.get(dist_val.lower(), dist_val.upper())
            batch_val = clean_row.get('batch no', 'Unknown')
            if batch_val.lower().startswith('batch'): batch_val = 'Batch ' + batch_val.lower().replace('batch', '').strip()
            
            if mapped_dist:
                teacher_data = {
                    "row_id": str(idx), "Batch": batch_val, "Date": standardize_date(clean_row.get('start date', clean_row.get('date', ''))),
                    "District": normalize_text(mapped_dist),
                    "School Name": normalize_text(clean_row.get('school name', clean_row.get('school', 'N/A'))),
                    "Name": normalize_text(clean_row.get('name', clean_row.get('teacher name', 'UNKNOWN'))),
                    "Designation": normalize_text(clean_row.get('designation', 'TEACHER')),
                    "Udise Code": clean_row.get('udise code', clean_row.get('udise', 'N/A'))
                }
                for k, v in row.items():
                    if k and k.strip().lower() not in known_keys: teacher_data[k.strip().title()] = str(v).strip()
                teachers.append(teacher_data)
    except Exception as e: print(f"Error: {e}")
    return teachers

# --- LIVE WEBSITE ROUTE ---
@app.route('/')
def home():
    is_admin = session.get('admin_logged_in', False)
    return render_template('index.html', is_admin=is_admin, **get_settings())

# --- LIVE EDIT APIs ---
@app.route('/api/save_live_edits', methods=['POST'])
def save_live_edits():
    if not session.get('admin_logged_in'): return jsonify({"success": False, "error": "Unauthorized"}), 403
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for key, val in data.items():
        c.execute('UPDATE settings SET val=? WHERE key=?', (str(val), str(key)))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/upload_asset', methods=['POST'])
def upload_asset():
    if not session.get('admin_logged_in'): return jsonify({"success": False, "error": "Unauthorized"}), 403
    asset_key = request.form.get('asset_key')
    file = request.files.get('file')
    if file and asset_key:
        filename = secure_filename(file.filename)
        filepath = os.path.join(ASSET_FOLDER, filename)
        file.save(filepath)
        
        file_url = f"/{filepath}"
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('UPDATE settings SET val=? WHERE key=?', (file_url, asset_key))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "url": file_url})
    return jsonify({"success": False}), 400

@app.route('/api/upload_csv', methods=['POST'])
def api_upload_csv():
    if not session.get('admin_logged_in'): return jsonify({"success": False}), 403
    file = request.files.get('file')
    if file and file.filename.endswith('.csv'):
        file.save(PRESENT_FILE)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid format"}), 400

# --- AUTH ROUTES ---
LOGIN_HTML = """
<!DOCTYPE html><html><body style="background:#0f172a; color:white; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
<div style="background:#1e293b; padding:40px; border-radius:12px; text-align:center; box-shadow:0 10px 30px rgba(0,0,0,0.5);">
    <h2 style="color:#38bdf8;">{% if setup %}Create Admin{% else %}God Mode Login{% endif %}</h2>
    <form method="POST" action="{% if setup %}/admin/setup{% else %}/admin/login{% endif %}">
        <input type="text" name="username" value="rahulrai-02" readonly style="width:100%; padding:10px; margin-bottom:10px; background:#0f172a; color:gray; border:none; border-radius:6px; text-align:center;">
        <input type="password" name="password" placeholder="Password" required style="width:100%; padding:10px; margin-bottom:20px; border-radius:6px; border:none; text-align:center;">
        <button style="width:100%; padding:12px; background:#10b981; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:bold;">Enter Command Center</button>
    </form>
</div></body></html>
"""

@app.route('/admin')
def admin_login_page():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM admin WHERE username="rahulrai-02"')
    admin_exists = c.fetchone()
    conn.close()
    if not admin_exists: return render_template_string(LOGIN_HTML, setup=True)
    if session.get('admin_logged_in'): return redirect('/') # Redirect to live page with powers!
    return render_template_string(LOGIN_HTML, setup=False)

@app.route('/admin/setup', methods=['POST'])
def admin_setup():
    hashed_pw = generate_password_hash(request.form['password'])
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO admin (username, password) VALUES (?, ?)', ('rahulrai-02', hashed_pw))
    conn.commit()
    conn.close()
    session['admin_logged_in'] = True
    return redirect('/')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT password FROM admin WHERE username=?', (request.form['username'],))
    row = c.fetchone()
    conn.close()
    if row and check_password_hash(row[0], request.form['password']):
        session['admin_logged_in'] = True
        return redirect('/')
    return "Invalid password. Go back."

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/')

# --- STANDARD API ROUTES (unchanged) ---
@app.route('/api/slider_images')
def get_slider_images():
    images = []
    if os.path.exists(SLIDER_FOLDER):
        images = [f"/{SLIDER_FOLDER}/{f}" for f in os.listdir(SLIDER_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    return jsonify(images)

@app.route('/api/dates')
def get_dates(): return jsonify(list(BATCH_TARGETS.keys()))

@app.route('/api/stats')
def get_stats():
    sel_batch = request.args.get('batch', 'All')
    data = get_present_data()
    arrived, total_arrived, gender_stats, designation_stats = {}, 0, {"Male": 0, "Female": 0, "Not Specified": 0}, {}
    for t in data:
        if sel_batch == 'All' or t.get('Batch') == sel_batch:
            d = t['District']
            arrived[d] = arrived.get(d, 0) + 1
            total_arrived += 1
            gender_raw = str(t.get('Gender', '')).strip().upper()
            if gender_raw in ['M', 'MALE']: gender_stats['Male'] += 1
            elif gender_raw in ['F', 'FEMALE']: gender_stats['Female'] += 1
            elif gender_raw != '': gender_stats['Not Specified'] += 1
            desig = t.get('Designation', 'TEACHER')
            if desig not in ['N/A', '']: designation_stats[desig] = designation_stats.get(desig, 0) + 1
            
    expected = sum(BATCH_TARGETS.values()) if sel_batch == 'All' else BATCH_TARGETS.get(sel_batch, 32)
    top_desigs = dict(sorted(designation_stats.items(), key=lambda item: item[1], reverse=True)[:5])
    return jsonify({"arrived": arrived, "total_arrived": total_arrived, "expected_total": expected, "gender_stats": gender_stats, "designation_stats": top_desigs})

@app.route('/api/teachers/<district_name>')
def get_district_teachers(district_name):
    sel_batch = request.args.get('batch', 'All')
    search_query = request.args.get('search', '').lower()
    data = get_present_data()
    target = district_name.upper()
    match = []
    for t in data:
        if (target == 'ALL' or t['District'] == target):
            if search_query and not any(search_query in str(val).lower() for val in t.values()): continue
            if sel_batch == 'All' or t.get('Batch') == sel_batch: match.append(t)
    return jsonify(match)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
