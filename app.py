import csv
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# --- FILE CONFIGURATION ---
PRESENT_FILE = 'present_data.csv'  

# The official State-Wide targets
BATCH_TARGETS = {
    '09-03-2026': 32, '10-03-2026': 32, '11-03-2026': 32,
    '12-03-2026': 32, '13-03-2026': 32, '16-03-2026': 32,
    '17-03-2026': 32, '18-03-2026': 32, '19-03-2026': 32,
    '24-03-2026': 32, '27-03-2026': 32, '01-04-2026': 28
}

DISTRICT_MAPPING = {
    "sahibzada ajit singh nagar": "MOHALI", "s.a.s. nagar": "MOHALI", 
    "sas nagar": "MOHALI", "s. a. s. nagar": "MOHALI", "mohali": "MOHALI",
    "sri muktsar sahib": "MUKTSAR", "muktsar sahib": "MUKTSAR", "muktsar": "MUKTSAR",
    "rupnagar": "RUPNAGAR", "ropar": "RUPNAGAR",
    "shahid bhagat singh nagar": "NAWANSHAHR", "sbs nagar": "NAWANSHAHR", "nawanshahr": "NAWANSHAHR",
    "taran taran": "TARN TARAN", "firozpur": "FEROZEPUR", "ferozepur": "FEROZEPUR",
    "fatehgarh sahib": "FATEHGARH SAHIB", "fatehgarh": "FATEHGARH SAHIB"
}

def normalize_text(text):
    if not text: return "N/A"
    return ' '.join(str(text).strip().upper().split())

def standardize_date(raw_date):
    if not raw_date: return 'Missing Date'
    date_str = str(raw_date).strip()
    if date_str.startswith(','): date_str = date_str[1:]
    date_str = date_str.split(' ')[0] 
    
    try:
        dt = datetime.strptime(date_str, '%d-%b-%Y')
        return dt.strftime('%d-%m-%Y')
    except ValueError: pass
        
    try:
        dt = datetime.strptime(date_str, '%d-%m-%Y')
        return dt.strftime('%d-%m-%Y')
    except ValueError: pass
        
    return 'Missing Date'

def get_present_data():
    teachers = []
    if os.path.exists(PRESENT_FILE):
        try:
            with open(PRESENT_FILE, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                
                # Dynamically find Date and District columns
                date_col = next((col for col in reader.fieldnames if col and ('date' in col.lower() or 'time' in col.lower())), 'Date')
                dist_col = next((col for col in reader.fieldnames if col and 'district' in col.lower()), 'District')
                
                for idx, row in enumerate(reader):
                    
                    school_val = 'N/A'
                    name_val = 'UNKNOWN'
                    
                    for key, val in row.items():
                        if not key: continue
                        k_lower = key.lower().strip()
                        
                        # --- BULLETPROOF SCHOOL AND NAME DETECTOR ---
                        # Explicitly looks for "school's name" first!
                        if "school's name" in k_lower or 'school' in k_lower:
                            school_val = val
                        elif 'teacher' in k_lower or ('name' in k_lower and 'school' not in k_lower and 'district' not in k_lower):
                            name_val = val

                    # Process District
                    dist_val = row.get(dist_col, '')
                    mapped_dist = DISTRICT_MAPPING.get(dist_val.strip().lower(), dist_val)
                    
                    # Process Date
                    raw_date = row.get(date_col, '')
                    clean_date = standardize_date(raw_date)
                    
                    if clean_date != 'Missing Date':
                        teacher = {
                            "row_id": str(idx),
                            "Date": clean_date,
                            "District": mapped_dist,
                            "School Name": normalize_text(school_val),
                            "Teacher Name": normalize_text(name_val),
                        }
                        teachers.append(teacher)
        except Exception as e:
            print(f"Error reading {PRESENT_FILE}: {e}")
    return teachers

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/dates')
def get_dates():
    dates = list(BATCH_TARGETS.keys())
    return jsonify(dates)

@app.route('/api/stats')
def get_stats():
    sel_date = request.args.get('date', 'All')
    data = get_present_data()
    
    arrived = {}
    total_arrived = 0
    
    for t in data:
        d = t.get('District', '').strip().upper()
        if not d: continue

        if sel_date == 'All' or t.get('Date') == sel_date:
            arrived[d] = arrived.get(d, 0) + 1
            total_arrived += 1
            
    if sel_date == 'All':
        expected_total = sum(BATCH_TARGETS.values()) 
    else:
        expected_total = BATCH_TARGETS.get(sel_date, 32)

    return jsonify({"arrived": arrived, "total_arrived": total_arrived, "expected_total": expected_total})

@app.route('/api/teachers/<district_name>')
def get_district_teachers(district_name):
    sel_date = request.args.get('date', 'All')
    search_query = request.args.get('search', '').lower() 
    
    data = get_present_data()
    clean = district_name.strip().lower()
    
    if clean == 'all':
        target = 'ALL'
    else:
        target = DISTRICT_MAPPING.get(clean, clean.upper())
        if "muktsar" in clean: target = "MUKTSAR"
        if "ajit singh" in clean or "sas nagar" in clean: target = "MOHALI"

    match = []
    for t in data:
        if target == 'ALL' or t.get('District', '').strip().upper() == target:
            if search_query:
                # Search across Teacher Name OR School Name
                name_match = search_query in t.get('Teacher Name', '').lower()
                school_match = search_query in t.get('School Name', '').lower()
                
                if not (name_match or school_match):
                    continue
            
            if sel_date == 'All' or t.get('Date') == sel_date:
                match.append(t)
                
    return jsonify(match)

if __name__ == '__main__':
    # Setting host to '0.0.0.0' makes the server reachable by other devices
    app.run(host='0.0.0.0', port=5000, debug=True)