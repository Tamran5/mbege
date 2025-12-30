/* monitoring.js - Logic Dashboard Dapur MBG
 * Fitur: Validasi Ketat Waktu Masak, Kamera Watermark, Timer Distribusi
 */

// --- 1. KONFIGURASI ATURAN ---
const MBG_RULES = {
    COOK_START: 2,  // Jam 02:00 Mulai Masak
    COOK_END: 4,    // Jam 04:00 Selesai Masak
    DIST_LIMIT: 30  // Batas 30 Menit untuk Distribusi
};

let stream = null; // Variabel global untuk kamera

// --- 2. INISIALISASI ---
document.addEventListener("DOMContentLoaded", () => {
    runSystemClock();
});

// --- 3. JAM SISTEM & LOGIKA STATUS ---
function runSystemClock() {
    setInterval(() => {
        const now = new Date();
        const h = now.getHours();
        
        // A. Update Jam Besar (Dashboard)
        const clockEl = document.getElementById('clockDisplay');
        if(clockEl) {
            clockEl.innerText = now.toLocaleTimeString('id-ID', {hour12: false});
        }

        // B. Update Jam Input Form (Agar user sadar ini jam real-time)
        const inputClock = document.getElementById('autoTimeInput');
        if(inputClock) {
            inputClock.value = now.toLocaleTimeString('id-ID', {
                hour: '2-digit', minute: '2-digit', second: '2-digit'
            }).replace('.', ':');
        }
        
        // C. Update Warna Status Bar
        updateAlertBar(now, h);

    }, 1000);
}

function updateAlertBar(now, h) {
    const title = document.getElementById('statusTitle');
    const desc = document.getElementById('statusDesc');
    const icon = document.getElementById('statusIcon');
    const iconBg = document.getElementById('statusIconBg');
    const bar = document.getElementById('statusBar');

    if(!title) return;

    // Cek Mode Distribusi (Hitung Mundur)
    const lastCook = localStorage.getItem('lastCookTime');
    const isDistributing = lastCook && !localStorage.getItem('distributionDone');

    // Reset Icon Style
    iconBg.className = 'icon icon-shape rounded-circle shadow mr-3 text-white';

    if (isDistributing) {
        // --- LOGIKA DISTRIBUSI ---
        const diffMins = Math.floor((now - new Date(lastCook)) / 60000);
        const remaining = MBG_RULES.DIST_LIMIT - diffMins;
        const percent = Math.max(0, (remaining / MBG_RULES.DIST_LIMIT) * 100);

        title.innerText = "TAHAP DISTRIBUSI";
        icon.className = "fas fa-truck";
        
        if(remaining > 10) {
            iconBg.classList.add('bg-gradient-success');
            desc.innerText = `Aman. Sisa: ${remaining} menit.`;
            bar.className = "progress-bar bg-success";
        } else if (remaining > 0) {
            iconBg.classList.add('bg-gradient-warning');
            desc.innerText = `SEGERA KIRIM! Sisa: ${remaining} menit.`;
            bar.className = "progress-bar bg-warning";
        } else {
            iconBg.classList.add('bg-gradient-danger');
            desc.innerText = `BAHAYA: Waktu habis!`;
            bar.className = "progress-bar bg-danger";
        }
        bar.style.width = `${percent}%`;

    } else {
        // --- LOGIKA JADWAL HARIAN ---
        bar.style.width = '0%';
        
        if (h >= 22 || h === 23) {
            iconBg.classList.add('bg-gradient-danger');
            title.innerText = "DILARANG MEMASAK";
            title.className = "mb-0 text-danger text-uppercase";
            desc.innerText = "Belum pergantian hari. Tunggu 00:00.";
            icon.className = "fas fa-ban";
        } else if (h >= 0 && h < 2) {
            iconBg.classList.add('bg-gradient-warning');
            title.innerText = "BELUM WAKTUNYA";
            title.className = "mb-0 text-warning text-uppercase";
            desc.innerText = "Persiapan boleh. Masak mulai 02:00.";
            icon.className = "fas fa-hourglass-start";
        } else if (h >= 2 && h < 4) {
            iconBg.classList.add('bg-gradient-success');
            title.innerText = "OPERASIONAL AKTIF";
            title.className = "mb-0 text-success text-uppercase";
            desc.innerText = "Golden Time (02:00 - 04:00).";
            icon.className = "fas fa-utensils";
        } else if (h >= 4 && h < 6) {
            iconBg.classList.add('bg-gradient-danger');
            title.innerText = "TERLAMBAT";
            title.className = "mb-0 text-danger text-uppercase";
            desc.innerText = "Sudah lewat batas masak.";
            icon.className = "fas fa-exclamation-triangle";
        } else {
            iconBg.classList.add('bg-gradient-primary');
            title.innerText = "OPERASIONAL SELESAI";
            title.className = "mb-0 text-primary text-uppercase";
            desc.innerText = "Menunggu jadwal besok.";
            icon.className = "fas fa-check";
        }
    }
}

// --- 4. KAMERA ---
async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        const video = document.getElementById('videoElement');
        video.srcObject = stream;
        video.style.display = 'block'; 
        
        document.getElementById('cameraControls').style.display = 'flex';
        document.getElementById('cameraBox').classList.add('camera-active');
    } catch (err) { alert("Gagal akses kamera: " + err); }
}

function takePhoto() {
    const video = document.getElementById('videoElement');
    const canvas = document.getElementById('canvasElement');
    const preview = document.getElementById('photoPreview');
    
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    // Watermark Tanggal Merah
    ctx.font = "bold 30px Arial"; ctx.fillStyle = "red";
    ctx.fillText(new Date().toLocaleString('id-ID'), 20, 50);

    const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
    video.style.display = 'none';
    preview.src = dataUrl; 
    preview.style.display = 'block';
    
    document.getElementById('photoData').value = dataUrl;
    if(stream) stream.getTracks().forEach(t => t.stop());
}

function resetCamera() {
    document.getElementById('photoPreview').style.display = 'none';
    document.getElementById('photoData').value = '';
    startCamera();
}

// --- 5. HANDLE SUBMIT FORM (DENGAN VALIDASI KETAT) ---
const kitchenForm = document.getElementById('kitchenForm');

if(kitchenForm) {
    kitchenForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const process = document.getElementById('processInput').value;
        const photo = document.getElementById('photoData').value;
        const now = new Date();
        const h = now.getHours();

        // 1. Cek Foto
        if (!photo) { alert("Wajib ambil foto bukti!"); return; }

        let statusBadge = '';
        let actionButton = '';

        // 2. LOGIKA MEMASAK (VALIDASI KETAT JAM)
        if (process.includes("Memasak")) {
            
            // A. Jika Jam 22:00 - 23:59 (Malam Sebelumnya) -> BLOKIR MUTLAK
            if (h >= 22) { 
                alert("DILARANG: Belum pergantian hari! Tunggu jam 00:00."); 
                return; 
            }

            // B. Jika Jam 04:00 - 21:59 (Siang/Sore) -> BLOKIR MUTLAK
            if (h >= 4 && h < 22) { 
                alert("DILARANG: Waktu memasak (02:00 - 04:00) sudah lewat/belum mulai!"); 
                return; 
            }

            // C. Jika Jam 00:00 - 01:59 (Dini Hari) -> PERINGATAN
            if (h < 2) { 
                if(!confirm("Masih terlalu dini (< 02:00). Yakin ingin mulai masak?")) return; 
            }

            // D. Jika Lolos (Jam 02:00 - 03:59) atau User Konfirmasi Dini Hari
            localStorage.setItem('cookingStartTime', now.getTime());
            localStorage.removeItem('cookingDoneTime');

            statusBadge = '<span class="badge badge-warning status-cell">SEDANG DIMASAK...</span>';
            actionButton = `<button class="btn btn-sm btn-success shadow-sm action-btn" onclick="finishCooking(this)">
                                <i class="fas fa-check"></i> Selesai
                            </button>`;
        } 
        // 3. LOGIKA DISTRIBUSI
        else if (process.includes("Distribusi")) {
             const lastCook = localStorage.getItem('lastCookTime');
             if(lastCook) {
                 const diff = (now - new Date(lastCook)) / 60000;
                 if(diff > MBG_RULES.DIST_LIMIT) {
                     alert("TELAT DISTRIBUSI!");
                     statusBadge = '<span class="badge badge-danger">TELAT</span>';
                 } else {
                     statusBadge = '<span class="badge badge-success">AMAN</span>';
                 }
                 localStorage.setItem('distributionDone', 'true');
             } else {
                 statusBadge = '<span class="badge badge-info">Dikirim</span>';
             }
             actionButton = '-';
        } 
        // 4. LOGIKA LAINNYA (Persiapan, QC, dll)
        else {
            statusBadge = '<span class="badge badge-primary">Selesai</span>';
            actionButton = '-';
        }

        // --- UPDATE TABEL ---
        const table = document.getElementById('historyTable');
        const row = table.insertRow(0);
        row.className = 'new-row';
        row.innerHTML = `
            <td>${now.toLocaleTimeString('id-ID', {hour:'2-digit', minute:'2-digit'})}</td>
            <td class="font-weight-bold text-dark">${process}</td>
            <td><img src="${photo}" style="height:40px; width:60px; object-fit:cover; border-radius:4px; cursor:pointer;" onclick="window.open(this.src)"></td>
            <td class="status-col">${statusBadge}</td>
            <td class="text-right action-col">${actionButton}</td>
        `;
        
        // Update Card Statistik
        const lastActionEl = document.getElementById('lastAction');
        if(lastActionEl) {
            lastActionEl.innerText = process;
            lastActionEl.title = process;
        }

        // --- KIRIM KE BACKEND (AJAX) ---
        // Uncomment kode di bawah jika backend API sudah siap
        /*
        fetch('/api/submit-activity', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ process: process, photo: photo })
        }).then(res => res.json()).then(data => console.log(data));
        */

        // RESET FORM
        this.reset();
        document.getElementById('photoData').value = '';
        document.getElementById('photoPreview').style.display = 'none';
        document.getElementById('cameraControls').style.display = 'none';
        document.getElementById('cameraBox').classList.remove('camera-active');
        document.getElementById('videoElement').style.display = 'none';
        
        // Reset Placeholder Kamera
        document.getElementById('cameraPlaceholder').style.display = 'flex'; 

        if(stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    });
}

// --- 6. FUNGSI TOMBOL "SELESAI MASAK" ---
function finishCooking(btn) {
    if(!confirm("Masakan sudah matang?")) return;

    const row = btn.closest('tr');
    const statusCol = row.querySelector('.status-col');
    const actionCol = row.querySelector('.action-col');
    const now = new Date();

    // Hitung Durasi Masak
    const startTime = localStorage.getItem('cookingStartTime');
    let durationStr = "";
    if(startTime) {
        const diffMins = Math.floor((now.getTime() - parseInt(startTime)) / 60000);
        const hrs = Math.floor(diffMins / 60);
        const mins = diffMins % 60;
        durationStr = `<br><small class="text-muted">Durasi: ${hrs}j ${mins}m</small>`;
        
        // Simpan Waktu Matang (Pemicu Timer Distribusi)
        localStorage.setItem('lastCookTime', now.toISOString());
        
        // Kirim Update ke Backend (Opsional)
        // fetch('/api/finish-activity/' + activityId ... )
    }

    // Update Tampilan Tabel
    statusCol.innerHTML = `<span class="badge badge-success">MATANG</span>${durationStr}`;
    actionCol.innerHTML = '<i class="fas fa-check-circle text-success fa-lg"></i>';
}