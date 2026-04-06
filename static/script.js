const map = L.map('map', {
    zoomControl: false,
    dragging: false,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    attributionControl: false
});

function triggerReset() {
    const pass = prompt("Enter Admin Password to Wipe ALL Attendance Data:");
    if (!pass) return;

    if (confirm("Are you ABSOLUTELY sure? This will mark every teacher in the CSV as 'Pending' again.")) {
        fetch('/api/reset_all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: pass })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert("System Reset Successful!");
                location.reload();
            } else {
                alert("Error: " + data.error);
            }
        });
    }
}

// --- NEW DATA RESOLVER FUNCTION ---
// This ensures map boundaries perfectly match your database names
function resolve(n) { 
    if(!n) return ""; 
    let c = n.trim().toLowerCase(); 
    if(c.includes("sas") || c.includes("mohali") || c.includes("sahibzada")) return "MOHALI"; 
    if(c.includes("muktsar")) return "MUKTSAR"; 
    if(c.includes("rupnagar") || c.includes("ropar")) return "RUPNAGAR"; 
    if(c.includes("bhagat") || c.includes("nawanshahr") || c.includes("sbs")) return "NAWANSHAHR"; 
    if(c.includes("taran") || c.includes("tarn")) return "TARN TARAN"; 
    if(c.includes("firozpur") || c.includes("ferozepur")) return "FEROZEPUR"; 
    if(c.includes("fatehgarh")) return "FATEHGARH SAHIB"; 
    return c.toUpperCase(); 
}

fetch('/api/district_counts')
    .then(response => response.json())
    .then(districtCounts => {
        fetch('/static/punjab_districts.geojson')
            .then(response => response.json())
            .then(geojsonData => {
                
                const punjabLayer = L.geoJSON(geojsonData, {
                    style: function (feature) {
                        return {
                            color: "#ffffff",
                            weight: 2,
                            fillColor: "#ff9933",
                            fillOpacity: 1
                        };
                    },
                    onEachFeature: function (feature, layer) {
                        const rawMapName = feature.properties.dtname;
                        
                        // Pass the raw map name through the resolver to match the backend
                        const resolvedName = resolve(rawMapName); 
                        const count = districtCounts[resolvedName] || 0;

                        // Display the raw map name to the user, but use the correct count
                        layer.bindTooltip(`<b>${rawMapName}</b><br>Total Teachers: ${count}`);

                        layer.on('click', function () {
                            // Use the resolved name to fetch data from the backend
                            fetch(`/api/teachers/${resolvedName}`)
                                .then(res => res.json())
                                .then(teachers => {
                                    const container = document.getElementById('table-container');
                                    let html = `<h4>Teachers in ${rawMapName}</h4>`;

                                    if (teachers.length === 0) {
                                        html += `<p>No data available.</p>`;
                                    } else {
                                        html += `<table>
                                                    <tr>
                                                        <th>Name</th>
                                                        <th>Subject</th>
                                                        <th>School</th>
                                                    </tr>`;
                                        teachers.forEach(t => {
                                            html += `<tr>
                                                        <td>${t.TeacherName}</td>
                                                        <td>${t.Subject}</td>
                                                        <td>${t.School}</td>
                                                     </tr>`;
                                        });
                                        html += `</table>`;
                                    }
                                    container.innerHTML = html;
                                });
                        });
                    }
                }).addTo(map);

                map.fitBounds(punjabLayer.getBounds());
            });
    });
