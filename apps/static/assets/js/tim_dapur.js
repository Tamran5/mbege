// ==========================================
// VARIABLE STATE GLOBAL
// ==========================================
let staffData = [];
let currentFilter = 'all'; // 'all' atau 'Hadir'
let searchQuery = '';

// Default: Hari Ini (Format: YYYY-MM-DD)
let selectedDate = new Date().toISOString().split('T')[0];

const MAX_WORK_DAYS = 26; 

// ==========================================
// 1. LOAD DATA DARI SERVER
// ==========================================
async function loadData() {
    try {
        // Kirim tanggal yang dipilih ke API
        const response = await fetch(`/api/staff?date=${selectedDate}`);
        if (!response.ok) throw new Error("Gagal mengambil data");
        
        staffData = await response.json();
        renderTable();
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// Helper: Warna Badge Role
function getRoleBadge(role) {
    let cls = 'badge-role-helper';
    const r = role.toLowerCase();
    if(r.includes('chef')) cls = 'badge-role-chef';
    else if(r.includes('cook')) cls = 'badge-role-cook';
    else if(r.includes('packer')) cls = 'badge-role-packer';
    else if(r.includes('driver')) cls = 'badge-role-driver';
    return `<span class="badge ${cls}">${role}</span>`;
}

// ==========================================
// 2. RENDER TABLE
// ==========================================
function renderTable() {
    const tbody = document.getElementById('staffTableBody');
    tbody.innerHTML = '';

    // Cek apakah user melihat Hari Ini atau Masa Lalu
    const todayStr = new Date().toISOString().split('T')[0];
    const isToday = (selectedDate === todayStr);

    // Filter Logic
    const filtered = staffData.filter(item => {
        let matchStatus = true;
        if (currentFilter === 'Hadir') {
            // Tampilkan yg Hadir atau Pulang (yg ada record absennya)
            matchStatus = (item.status === 'Hadir' || item.status === 'Pulang');
        }
        
        const lowerName = item.name.toLowerCase();
        const lowerRole = item.role.toLowerCase();
        const query = searchQuery.toLowerCase();
        const matchSearch = lowerName.includes(query) || lowerRole.includes(query);

        return matchStatus && matchSearch;
    });

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center py-5 text-muted">
            <i class="fas fa-folder-open fa-2x mb-3"></i><br>Tidak ada data pada tanggal ini
        </td></tr>`;
        updateStats();
        return;
    }

    filtered.forEach(item => {
        // Progress Bar (Hadir / 26 Hari)
        let percent = Math.round((item.attendance / MAX_WORK_DAYS) * 100);
        if(percent > 100) percent = 100;
        let progressColor = percent >= 90 ? 'bg-success' : (percent < 60 ? 'bg-warning' : 'bg-primary');

        // Logic UI Tombol Absensi
        let attendanceBtn = '';
        
        if (!isToday) {
            // MODE HISTORY (READ ONLY) - Tidak bisa klik tombol
            if (item.status === 'Hadir' || item.status === 'Pulang') {
                attendanceBtn = `<span class="badge badge-success px-2">IN: ${item.check_in_time}</span>`;
                if(item.check_out_time) {
                    attendanceBtn += `<br><span class="badge badge-warning mt-1 px-2">OUT: ${item.check_out_time}</span>`;
                } else {
                    attendanceBtn += `<br><span class="badge badge-default mt-1">Lupa Out</span>`;
                }
            } else {
                attendanceBtn = `<span class="badge badge-secondary">Tidak Masuk / Off</span>`;
            }
        } 
        else {
            // MODE HARI INI (AKTIF) - Bisa klik tombol
            if (item.status === 'Hadir') {
                // Sedang Kerja -> Tombol Check Out
                attendanceBtn = `
                <button class="btn btn-sm btn-attendance btn-check-out shadow-sm" onclick="toggleAttendance(${item.id})">
                    <i class="fas fa-sign-out-alt"></i> Kerja
                </button>
                <div class="text-xs text-muted mt-1">Masuk: ${item.check_in_time || '-'}</div>`;
            } 
            else if (item.status === 'Pulang') {
                // Sudah Pulang -> Disable
                attendanceBtn = `
                <button class="btn btn-sm btn-attendance btn-done" disabled>
                    <i class="fas fa-check-double"></i> Selesai
                </button>
                <div class="text-xs text-muted mt-1">Plg: ${item.check_out_time || '-'}</div>`;
            } 
            else {
                // Belum Masuk -> Tombol Masuk
                attendanceBtn = `
                <button class="btn btn-sm btn-attendance btn-check-in" onclick="toggleAttendance(${item.id})">
                    <i class="fas fa-fingerprint"></i> Masuk
                </button>`;
            }
        }

        const row = `
        <tr class="fade-in">
            <th scope="row">
                <div class="media align-items-center">
                    <img alt="Image" src="${item.img}" class="avatar-table mr-3">
                    <div class="media-body">
                        <span class="mb-0 text-sm font-weight-bold text-dark d-block">${item.name}</span>
                        ${getRoleBadge(item.role)}
                        <span class="text-xs text-muted ml-2"><i class="fas fa-phone"></i> ${item.phone}</span>
                    </div>
                </div>
            </th>
            
            <td style="vertical-align: middle;">
                <div class="d-flex align-items-center">
                    <span class="mr-2 text-sm font-weight-bold">${percent}%</span>
                    <div>
                        <div class="progress" style="width: 100px; height: 6px;">
                            <div class="progress-bar ${progressColor}" role="progressbar" style="width: ${percent}%;"></div>
                        </div>
                        <small class="text-muted">${item.attendance} Hari (Bulan Terpilih)</small>
                    </div>
                </div>
            </td>

            <td class="text-center" style="vertical-align: middle;">
                ${attendanceBtn}
            </td>

            <td class="text-right" style="vertical-align: middle;">
                ${isToday ? `
                <div class="dropdown">
                    <a class="btn btn-sm btn-icon-only text-light" href="#" role="button" data-toggle="dropdown">
                      <i class="fas fa-ellipsis-v"></i>
                    </a>
                    <div class="dropdown-menu dropdown-menu-right dropdown-menu-arrow">
                        <a class="dropdown-item" href="#" onclick="prepEditData(${item.id})">Edit Profil</a>
                        <a class="dropdown-item text-danger" href="#" onclick="deleteData(${item.id})">Hapus Pegawai</a>
                    </div>
                </div>` : '<small class="text-muted font-italic">History</small>'}
            </td>
        </tr>
        `;
        tbody.insertAdjacentHTML('beforeend', row);
    });

    updateStats();
}

// ==========================================
// 3. API ACTIONS
// ==========================================

// Check In / Check Out
async function toggleAttendance(id) {
    try {
        const res = await fetch(`/api/staff/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'attendance' })
        });
        await res.json();
        loadData(); // Refresh table
    } catch (err) { console.error(err); }
}

// Tambah / Edit Staff
const form = document.getElementById('staffForm');
form.addEventListener('submit', async function(e) {
    e.preventDefault();
    const idStr = document.getElementById('editId').value;
    const payload = {
        name: document.getElementById('inputName').value,
        role: document.getElementById('inputRole').value,
        phone: document.getElementById('inputPhone').value
    };

    try {
        if (idStr) {
            await fetch(`/api/staff/${idStr}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            await fetch('/api/staff', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }
        resetForm();
        loadData();
    } catch (err) { console.error(err); }
});

// Hapus Staff
async function deleteData(id) {
    if(confirm('Hapus pegawai ini beserta riwayat absensinya?')) {
        try {
            await fetch(`/api/staff/${id}`, { method: 'DELETE' });
            loadData();
        } catch (err) { console.error(err); }
    }
}

// Edit Form Helper
function prepEditData(id) {
    const item = staffData.find(d => d.id === id);
    if (!item) return;

    document.getElementById('editId').value = item.id;
    document.getElementById('inputName').value = item.name;
    document.getElementById('inputRole').value = item.role;
    document.getElementById('inputPhone').value = item.phone;
    document.getElementById('formTitle').innerText = "Edit Data Staff";
    
    if(window.innerWidth < 1200) {
        document.querySelector('.order-xl-2').scrollIntoView({behavior: 'smooth'});
    }
}

// ==========================================
// 4. STATISTIK & EVENT LISTENERS
// ==========================================

function updateStats() {
    const total = staffData.length;
    // Hadir = Sedang Kerja + Sudah Pulang
    const present = staffData.filter(d => d.status === 'Hadir' || d.status === 'Pulang').length;
    const absent = total - present;

    document.getElementById('stat-total').innerText = total;
    document.getElementById('stat-present').innerText = present;
    document.getElementById('stat-absent').innerText = absent;
}

function setFilter(status) {
    currentFilter = status;
    renderTable();
}

// Search Listeners
['searchInput', 'searchInputMobile'].forEach(id => {
    const el = document.getElementById(id);
    if(el) el.addEventListener('keyup', (e) => {
        searchQuery = e.target.value;
        renderTable();
    });
});

// Date Picker Listener
const dateInput = document.getElementById('filterDate');
if(dateInput) {
    dateInput.value = selectedDate; // Set default value
    dateInput.addEventListener('change', (e) => {
        selectedDate = e.target.value;
        loadData(); // Reload data sesuai tanggal baru
    });
}

function resetForm() {
    form.reset();
    document.getElementById('editId').value = "";
    document.getElementById('formTitle').innerText = "Tambah Staff Baru";
}

// INIT
document.addEventListener('DOMContentLoaded', () => {
    loadData();
});