let chartInstance = null;
let allReviews = [];

document.addEventListener('DOMContentLoaded', function() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById("filterTanggal").value = today;
    updateDashboard();
});

async function updateDashboard() {
    const selectedDate = document.getElementById("filterTanggal").value;
    
    try {
        // Endpoint disesuaikan dengan struktur statistik baru
        const response = await fetch(`/api/ulasan-stats?tanggal=${selectedDate}`);
        const data = await response.json();

        allReviews = data.reviews;

        // 1. Update Card Statistik
        document.getElementById("valTotal").innerText = data.total;
        document.getElementById("valNegative").innerText = data.negative_count;
        document.getElementById("valSatisfaction").innerText = data.satisfaction;
        
        const progressBar = document.getElementById("progressBarSat");
        progressBar.style.width = data.satisfaction;
        
        const percent = parseInt(data.satisfaction);
        progressBar.className = percent < 50 ? "progress-bar bg-danger" : 
                                (percent < 80 ? "progress-bar bg-warning" : "progress-bar bg-success");

        // 2. Update Grafik Doughnut
        updateChart(data.chart_data);

        // 3. Render Tabel Detail
        renderTabel();

    } catch (error) {
        console.error("Gagal memuat data AI:", error);
    }
}

function updateChart(chartData) {
    const ctx = document.getElementById("sentimenChart");
    const emptyMsg = document.getElementById("chartEmpty");
    
    if (chartInstance) chartInstance.destroy();

    if (!chartData || chartData.every(val => val === 0)) {
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
        tbody.innerHTML = "<tr><td colspan='3' class='text-center py-4 text-muted'>Tidak ada ulasan masuk</td></tr>";
        return;
    }

    filteredData.forEach(item => {
        // --- LOGIKA BINTANG (Rating 1-5 dari Flutter) ---
        let starHtml = '';
        for (let i = 1; i <= 5; i++) {
            starHtml += `<i class="fas fa-star ${i <= item.rating ? 'text-warning' : 'text-lighter'}" style="font-size: 11px;"></i>`;
        }

        // --- LOGIKA TAGS (Pilihan Cepat dari Flutter) ---
        let tagsHtml = '';
        if (item.tags && item.tags.length > 0) {
            tagsHtml = item.tags.map(tag => 
                `<span class="badge badge-pill badge-secondary mr-1" style="font-size: 9px; text-transform: none;">${tag}</span>`
            ).join('');
        }

        let badgeClass = item.status === 'positif' ? 'st-pos' : (item.status === 'negatif' ? 'st-neg' : 'st-neu');
        
        tbody.innerHTML += `
            <tr>
                <td>
                    <div class="font-weight-bold text-dark">${item.penerima}</div>
                    <div class="mt-1">${starHtml}</div>
                </td>
                <td class="text-wrap" style="max-width: 350px;">
                    <div class="mb-2">${tagsHtml}</div>
                    <span class="text-sm text-muted">"${item.text || 'Tidak ada komentar'}"</span>
                </td>
                <td class="text-right">
                    <span class="status-badge ${badgeClass}">${item.status}</span>
                </td>
            </tr>
        `;
    });
    setInterval(updateDashboard, 10000);
}