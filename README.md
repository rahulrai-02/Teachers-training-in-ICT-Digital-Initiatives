# Teachers Training in ICT & Digital Initiatives

A live dashboard application for tracking and managing teacher attendance across ICT training programs in Punjab.

**Live Demo:** https://nielitscert.onrender.com/

## 🎯 Overview

This application provides real-time analytics and visualization of teachers trained in ICT initiatives across 23 districts of Punjab. It features an interactive map, comprehensive statistics, and detailed attendance records.

## ✨ Features

- **Interactive Punjab Map** - Visual representation of teacher distribution across districts
- **Live Statistics** - Real-time count of trained teachers, districts, schools, and batches
- **Batch Management** - Track attendance across 12 training batches (333 teachers)
- **District Filtering** - Filter data by district and batch for detailed analysis
- **Gender Demographics** - Visualize gender distribution among participants
- **Designation Analytics** - Top designations among trained teachers
- **Photo Gallery** - Browse training session photos by batch
- **Data Export** - Export attendance records to CSV
- **Responsive Design** - Works seamlessly on desktop and mobile devices

## 🛠️ Technology Stack

- **Backend:** Flask 3.0.3, Python 3.x
- **Frontend:** HTML5, CSS3, JavaScript (ES6+)
- **Maps:** Leaflet.js with GeoJSON
- **Charts:** Chart.js
- **Data Parsing:** PapaParse (CSV)

## 📊 Dataset

- **23 Districts** across Punjab
- **12 Training Batches** (380 target, 333 trained)
- **333 Teachers** from various schools and designations
- Comprehensive metadata: UDISE codes, designations, dates, gender


## 📁 Project Structure

```
Teachers-training-in-ICT-Digital-Initiatives/
├── app.py                        # Flask backend & APIs
├── requirements.txt              # Python dependencies
├── static/
│   ├── present_data.csv          # Teacher attendance records
│   ├── punjab_districts.geojson  # Map boundaries & geometry
│   ├── script.js                 # Main JavaScript logic
│   ├── scert_logo.png            # SCERT logo
│   └── edu_logo.png              # NIELIT logo
├── templates/
│   ├── index.html                # Main dashboard
│   └── gallery.html              # Photo gallery
└── Photo_Gallery/                # Training session photos (by batch)
```

## 🎨 Dashboard Features

### Statistics Panel
- Total trained teachers count
- Number of active batches
- Districts covered
- Schools represented

### Interactive Map
- Color-coded districts by attendance
- Click on a district to filter data
- Hover tooltips showing exact counts
- Zoom and pan controls

### Analytics Charts
- District-wise headcount bar chart
- Gender demographics pie chart
- Top designations visualization
- Target vs achieved progress

### Data Table
- Detailed teacher records with search
- Filter by district and batch
- Export to CSV
- Print-friendly format

### Photo Gallery
- Carousel view of batch photos
- Navigate with previous/next buttons
- Keyboard navigation support (arrow keys)

## ⚙️ Configuration

Edit `app.py` to customize:
- `GITHUB_CSV_URL` - Remote CSV file URL
- `BATCH_TARGETS` - Expected teachers per batch
- `DISTRICT_MAPPING` - District name standardization

## 🔍 API Endpoints

- `GET /` - Main dashboard
- `GET /gallery` - Photo gallery page
- `GET /api/dates` - List of batches
- `GET /api/stats` - Statistics data
- `GET /api/gallery` - Available photos
- `GET /api/teachers/<district>` - Teachers by district

## 👥 Built By

**WBL Department**  
National Institute of Electronics & Information Technology (NIELIT) Ropar  
Ministry of Electronics & IT, Government of India

For more information: https://nielit.gov.in/ropar/

## 📄 License

All rights reserved © 2026 WBL Department, NIELIT Ropar

---

**Last Updated:** April 2026  
**Database:** 333 Teachers | 23 Districts | 12 Batches
