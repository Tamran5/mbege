// State Lokal
let localData = [];

// Helper: Warna & Icon berdasarkan Kategori
function getCategoryMeta(type) {
    switch(type) {
        case 'SD': return { color: 'bg-orange', icon: 'fa-school', label: 'SD' };
        case 'SMP': return { color: 'bg-info', icon: 'fa-user-graduate', label: 'SMP' };
        case 'SMA': return { color: 'bg-primary', icon: 'fa-university', label: 'SMA' };
        case 'Balita': return { color: 'bg-green', icon: 'fa-baby', label: 'Balita' };
        case 'Ibu Hamil': return { color: 'bg-red', icon: 'fa-person-pregnant', label: 'Bumil' };
        case 'Lansia': return { color: 'bg-purple', icon: 'fa-blind', label: 'Lansia' };
        default: return { color: 'bg-default', icon: 'fa-users', label: 'Umum' };
    }
}

// 1. FETCH DATA (LOAD)
async function loadData() {
    try {
        const response = await fetch('/api/penerima');
        localData = await response.json();
        renderTable(localData);
        updateStats(localData);
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// 2. RENDER TABLE (UPDATED STRUKTUR)
function renderTable(data) {
    const tbody = document.getElementById('penerimaTableBody');
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    
    tbody.innerHTML = '';

    const filtered = data.filter(item => 
        item.name.toLowerCase().includes(searchTerm) || 
        item.location.toLowerCase().includes(searchTerm)
    );

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4">Data tidak ditemukan</td></tr>`;
        return;
    }

    filtered.forEach(item => {
        const meta = getCategoryMeta(item.category);
        
        // --- LOGIKA PIC & WHATSAPP (Disatukan) ---
        let contactHtml = `<div class="d-flex flex-column align-items-start">`;
        
        // Nama PIC
        contactHtml += `
            <div class="text-muted text-xs font-weight-bold mb-2">
                <i class="fas fa-user mr-1"></i> ${item.pic || '-'}
            </div>
        `;
        
        // Tombol WA
        if (item.phone) {
            let waNum = item.phone.replace(/^0/, '62').replace(/[^0-9]/g, '');
            contactHtml += `
            <a href="https://wa.me/${waNum}" target="_blank" class="badge badge-pill badge-success wa-btn shadow-sm" title="Chat via WhatsApp">
                <i class="fab fa-whatsapp mr-1"></i> ${item.phone}
            </a>
            `;
        }
        contactHtml += `</div>`;
        // ------------------------------------------

        const html = `
        <tr class="fade-in">
            <th scope="row">
                <div class="media align-items-center">
                    <div class="avatar-icon ${meta.color} shadow-sm">
                        ${item.name.substring(0,1).toUpperCase()}
                    </div>
                    <div class="media-body">
                        <span class="mb-0 text-sm font-weight-bold text-dark">${item.name}</span>
                        <div class="text-xs text-muted address-wrap">
                            <i class="fas fa-map-marker-alt mr-1"></i>${item.location}
                        </div>
                    </div>
                </div>
            </th>

            <td>
                <span class="badge badge-dot mr-4">
                    <i class="${meta.color}"></i> <span class="status">${meta.label}</span>
                </span>
            </td>

            <td class="text-center">
                <span class="h4 font-weight-bold mb-0 text-dark">${item.count}</span>
                <span class="text-xs text-muted d-block">Porsi</span>
            </td>

            <td>
                ${contactHtml}
            </td>

            <td class="text-right">
                <button class="btn btn-sm btn-icon-only text-primary" onclick="editData(${item.id})" title="Edit">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-icon-only text-danger" onclick="deleteData(${item.id})" title="Hapus">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
        `;
        tbody.insertAdjacentHTML('beforeend', html);
    });
}

// 3. UPDATE STATS
function updateStats(data) {
    const total = data.length;
    const sekolah = data.filter(d => ['SD','SMP','SMA'].includes(d.category)).length;
    const rentan = data.filter(d => ['Balita','Ibu Hamil','Lansia'].includes(d.category)).length;
    const porsi = data.reduce((acc, curr) => acc + curr.count, 0);

    document.getElementById('stat-total').innerText = total;
    document.getElementById('stat-sekolah').innerText = sekolah;
    document.getElementById('stat-rentan').innerText = rentan;
    document.getElementById('stat-porsi').innerText = porsi.toLocaleString();
}

// 4. SUBMIT FORM
const form = document.getElementById('penerimaForm');

form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const idStr = document.getElementById('editId').value;
    const formData = {
        category: document.getElementById('inputCategory').value,
        name: document.getElementById('inputName').value,
        location: document.getElementById('inputLocation').value,
        count: parseInt(document.getElementById('inputCount').value) || 0,
        pic: document.getElementById('inputPIC').value,
        phone: document.getElementById('inputPhone').value
    };

    let url = '/api/penerima';
    let method = 'POST';

    if (idStr) {
        url = `/api/penerima/${idStr}`;
        method = 'PUT';
    }

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (res.ok) {
            resetForm();
            loadData();
        }
    } catch (err) {
        console.error("Gagal menyimpan:", err);
    }
});

// 5. ACTIONS
function editData(id) {
    const item = localData.find(d => d.id === id);
    if (!item) return;

    document.getElementById('editId').value = item.id;
    document.getElementById('inputCategory').value = item.category;
    document.getElementById('inputName').value = item.name;
    document.getElementById('inputLocation').value = item.location;
    document.getElementById('inputCount').value = item.count;
    document.getElementById('inputPIC').value = item.pic;
    document.getElementById('inputPhone').value = item.phone || '';

    document.getElementById('formTitle').innerText = "Edit Data";
    
    if(window.innerWidth < 1200) {
        document.querySelector('.order-xl-2').scrollIntoView({behavior: 'smooth'});
    }
}

async function deleteData(id) {
    if(confirm('Hapus data ini secara permanen?')) {
        try {
            await fetch(`/api/penerima/${id}`, { method: 'DELETE' });
            loadData();
        } catch (err) {
            console.error("Gagal menghapus:", err);
        }
    }
}

function resetForm() {
    form.reset();
    document.getElementById('editId').value = "";
    document.getElementById('formTitle').innerText = "Form Penerima";
}

document.getElementById('searchInput').addEventListener('input', () => renderTable(localData));
document.addEventListener('DOMContentLoaded', loadData);