let chartInstance = null;
let allReviews = [];

document.addEventListener('DOMContentLoaded', function() {
    // Set default tanggal hari ini di input
    const today = new Date().toISOString().split('T')[0];
    document.getElementById("filterTanggal").value = today;
    updateDashboard();
});

async function updateDashboard() {
    const selectedDate = document.getElementById("filterTanggal").value;
    
    try {
        // Mengambil data real-time dari API Flask (IndoBERT)
        const response = await fetch(`/api/ulasan-stats?tanggal=${selectedDate}`);
        const data = await response.json();

        allReviews = data.reviews;

        // 1. Update Card Statistik
        document.getElementById("valTotal").innerText = data.total;
        document.getElementById("valNegative").innerText = data.negative_count;
        document.getElementById("valSatisfaction").innerText = data.satisfaction;
        
        const progressBar = document.getElementById("progressBarSat");
        progressBar.style.width = data.satisfaction;
        
        // Warna bar dinamis
        const percent = parseInt(data.satisfaction);
        progressBar.className = percent < 50 ? "progress-bar bg-danger" : 
                                (percent < 80 ? "progress-bar bg-warning" : "progress-bar bg-success");

        // 2. Update Grafik Doughnut
        updateChart(data.chart_data);

        // 3. Render Baris Tabel
        renderTabel();

    } catch (error) {
        console.error("Gagal memuat data AI:", error);
    }
}

function updateChart(chartData) {
    const ctx = document.getElementById("sentimenChart");
    const emptyMsg = document.getElementById("chartEmpty");
    
    if (chartInstance) chartInstance.destroy();

    if (chartData.every(val => val === 0)) {
        ctx.style.display = 'none';
        emptyMsg.style.display = 'block';
    } else {
        ctx.style.display = 'block';
        emptyMsg.style.display = 'none';
        
        chartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Positif', 'Netral', 'Negatif'],
                datasets: [{
                    data: chartData,
                    backgroundColor: ['#2dce89', '#adb5bd', '#f5365c'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false, cutout: '70%',
                plugins: { 
                    legend: { position: 'bottom', labels: { usePointStyle: true, padding: 20 } } 
                }
            }
        });
    }
}

function renderTabel() {
    const filterJenis = document.getElementById("filterSentimen").value;
    const tbody = document.getElementById("tabelUlasan");
    tbody.innerHTML = "";

    const filteredData = allReviews.filter(item => filterJenis === "all" || item.status === filterJenis);

    if (filteredData.length === 0) {
        tbody.innerHTML = "<tr><td colspan='3' class='text-center py-4 text-muted'>Tidak ada ulasan</td></tr>";
        return;
    }

    filteredData.forEach(item => {
        let badgeClass = item.status === 'positif' ? 'st-pos' : (item.status === 'negatif' ? 'st-neg' : 'st-neu');
        
        tbody.innerHTML += `
            <tr>
                <td>
                    <div class="font-weight-bold text-dark">${item.penerima}</div>
                    <span class="badge badge-secondary" style="font-size: 10px;">Penerima MBG</span>
                </td>
                <td class="text-wrap" style="max-width: 350px;">
                    <span class="text-sm">"${item.text}"</span>
                </td>
                <td class="text-right">
                    <span class="status-badge ${badgeClass}">${item.status}</span>
                </td>
            </tr>
        `;
    });
}