const map = L.map('map', {
    zoomControl: false,
    dragging: false,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    attributionControl: false
});function triggerReset() {
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
                        const districtName = feature.properties.dtname;
                        const count = districtCounts[districtName] || 0;

                        layer.bindTooltip(`<b>${districtName}</b><br>Total Teachers: ${count}`);

                        layer.on('click', function () {
                            fetch(`/api/teachers/${districtName}`)
                                .then(res => res.json())
                                .then(teachers => {
                                    const container = document.getElementById('table-container');
                                    let html = `<h4>Teachers in ${districtName}</h4>`;

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