import csv
import os
import io
import re
import urllib.request
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# --- CONFIGURATION ---
# Replace this with the "Raw" URL of your CSV file on GitHub.
# Example: 'https://raw.githubusercontent.com/username/repo/main/present_data.csv'
GITHUB_CSV_URL = '' 
LOCAL_CSV_FILE = 'present_data.csv'

BATCH_TARGETS = {
    'Batch 1': 32, 'Batch 2': 32, 'Batch 3': 32, 'Batch 4': 32, 
    'Batch 5': 32, 'Batch 6': 32, 'Batch 7': 32, 'Batch 8': 32, 
    'Batch 9': 32, 'Batch 10': 32, 'Batch 11': 32, 'Batch 12': 28
}

# Add any typos you find in the terminal to this dictionary!
DISTRICT_MAPPING = {
    "sas nagar": "S.A.S. NAGAR", "s.a.s nagar": "S.A.S. NAGAR", "mohali": "S.A.S. NAGAR", "SAS NAGAR": "S.A.S. NAGAR", 
    "S.A.S NAGAR": "S.A.S. NAGAR", 
    "S.A.S. NAGAR": "S.A.S. NAGAR",
    "MOHALI": "S.A.S. NAGAR",
    "sri muktsar sahib": "MUKTSAR", "muktsar": "MUKTSAR",
    "shahid bhagat singh nagar": "NAWANSHAHR", "sbs nagar": "NAWANSHAHR",
    "taran taran": "TARN TARAN", "firozpur": "FEROZEPUR", "ferozepur": "FEROZEPUR",
    "fatehgarh sahib": "FATEHGARH SAHIB", "rupnagar": "RUPNAGAR", "ropar": "RUPNAGAR",
    # Examples of typos to catch (update these based on what prints in your terminal)
    "jalandher": "JALANDHAR", 
    "pathankote": "PATHANKOT",
    "ludhina": "LUDHIANA"
}

# --- BULLETPROOF DATA PARSER ---
def normalize_text(text): 
    return ' '.join(str(text).strip().upper().split()) if text else "N/A"

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
    raw_text = ""

    # 1. Try fetching live data directly from GitHub URL
    try:
        if GITHUB_CSV_URL and GITHUB_CSV_URL.startswith('http'):
            req = urllib.request.Request(GITHUB_CSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                raw_text = response.read().decode('utf-8-sig')
    except Exception as e:
        print(f"GitHub fetch failed, falling back to local file: {e}")

    # 2. Fallback to local file if GitHub fails or URL is empty
    if not raw_text and os.path.exists(LOCAL_CSV_FILE):
        try:
            with open(LOCAL_CSV_FILE, mode='r', encoding='utf-8-sig') as file:
                raw_text = file.read()
        except Exception as e:
            print(f"Error reading local CSV: {e}")

    if not raw_text:
        return teachers  # Return empty if both fail

    # 3. Clean and parse the CSV text
    try:
        raw_text = raw_text.replace('",,,,\r\n', '\n').replace('",,,,\n', '\n').replace('",,,,', '')
        raw_text = re.sub(r'^"|(?<=\n)"', '', raw_text)
        raw_text = raw_text.replace('""', '"')

        reader = csv.DictReader(io.StringIO(raw_text))
        known_keys = ['batch no', 'district', 'start date', 'date', 'school name', 'school', 'name', 'teacher name', 'designation', 'udise code', 'udise', 's.no']
        
        for idx, row in enumerate(reader):
            clean_row = {k.strip().lower(): str(v).strip() for k, v in row.items() if k}
            
            # --- FIX APPLIED HERE: Stripped invisible spaces (.strip()) ---
            dist_val = clean_row.get('district', '').strip()
            mapped_dist = DISTRICT_MAPPING.get(dist_val.lower(), dist_val.upper())
            
            batch_val = clean_row.get('batch no', 'Unknown')
            if batch_val.lower().startswith('batch'): 
                batch_val = 'Batch ' + batch_val.lower().replace('batch', '').strip()
            
            if mapped_dist:
                teacher_data = {
                    "row_id": str(idx), 
                    "Batch": batch_val, 
                    "Date": standardize_date(clean_row.get('start date', clean_row.get('date', ''))),
                    "District": normalize_text(mapped_dist),
                    "School Name": normalize_text(clean_row.get('school name', clean_row.get('school', 'N/A'))),
                    "Name": normalize_text(clean_row.get('name', clean_row.get('teacher name', 'UNKNOWN'))),
                    "Designation": normalize_text(clean_row.get('designation', 'TEACHER')),
                    "Udise Code": clean_row.get('udise code', clean_row.get('udise', 'N/A'))
                }
                # Grab any extra unknown columns dynamically
                for k, v in row.items():
                    if k and k.strip().lower() not in known_keys: 
                        teacher_data[k.strip().title()] = str(v).strip()
                teachers.append(teacher_data)
    except Exception as e: 
        print(f"Parsing Error: {e}")
        
    return teachers

# --- ROUTES ---

@app.route('/')
def home():
    # Admin removed. Just serving the clean HTML.
    return render_template('index.html')

@app.route('/api/dates')
def get_dates(): 
    return jsonify(list(BATCH_TARGETS.keys()))

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
            if desig not in ['N/A', '']: 
                designation_stats[desig] = designation_stats.get(desig, 0) + 1
            
    # --- FIX APPLIED HERE: Prints exactly which districts are rendering ---
    print("\n" + "="*50)
    print(f"🔍 CURRENT DISTRICTS IN SYSTEM (Total: {len(arrived)})")
    print(list(arrived.keys()))
    print("="*50 + "\n")

    expected = sum(BATCH_TARGETS.values()) if sel_batch == 'All' else BATCH_TARGETS.get(sel_batch, 32)
    top_desigs = dict(sorted(designation_stats.items(), key=lambda item: item[1], reverse=True)[:5])
    
    return jsonify({
        "arrived": arrived, 
        "total_arrived": total_arrived, 
        "expected_total": expected, 
        "gender_stats": gender_stats, 
        "designation_stats": top_desigs
    })

@app.route('/api/teachers/<district_name>')
def get_district_teachers(district_name):
    sel_batch = request.args.get('batch', 'All')
    search_query = request.args.get('search', '').lower()
    data = get_present_data()
    target = district_name.upper()
    match = []
    
    for t in data:
        if (target == 'ALL' or t['District'] == target):
            if search_query and not any(search_query in str(val).lower() for val in t.values()): 
                continue
            if sel_batch == 'All' or t.get('Batch') == sel_batch: 
                match.append(t)
                
    return jsonify(match)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
