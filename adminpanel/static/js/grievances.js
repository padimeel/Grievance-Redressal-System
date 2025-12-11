/* grievances.js - fixes for select/text contrast, layout and behavior */

/* CSRF helper */
function getCookie(name) {
  if (!document.cookie) return null;
  const cookies = document.cookie.split(';').map(c => c.trim());
  for (let c of cookies) {
    const parts = c.split('=');
    if (parts[0] === name) return decodeURIComponent(parts.slice(1).join('='));
  }
  return null;
}
const CSRF_TOKEN = getCookie('csrftoken');

/* fetch wrapper */
async function fetchJSON(url, opts = {}) {
  opts.credentials = opts.credentials || 'same-origin';
  opts.headers = Object.assign({'Accept': 'application/json'}, opts.headers || {});
  const method = (opts.method || 'GET').toUpperCase();

  if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData)) {
    if (!opts.headers['Content-Type']) opts.headers['Content-Type'] = 'application/json';
    if (opts.headers['Content-Type'] === 'application/json') opts.body = JSON.stringify(opts.body);
  }

  if (['POST','PUT','PATCH','DELETE'].includes(method) && CSRF_TOKEN) {
    opts.headers['X-CSRFToken'] = CSRF_TOKEN;
  }

  const res = await fetch(url, opts);
  if (res.status === 204) return null;
  const ct = res.headers.get('content-type') || '';
  const text = await res.text();

  if (!res.ok) {
    let parsed;
    try { parsed = ct.includes('application/json') ? JSON.parse(text) : text; } catch(e) { parsed = text; }
    const err = new Error('API error ' + res.status);
    err.status = res.status; err.body = parsed;
    throw err;
  }

  if (ct.includes('application/json')) return JSON.parse(text);
  return text;
}

/* UI & state */
const API_BASE = '/adminpanel/api/';
let currentPage = 1;
let pageSize = parseInt(document.getElementById('page-size')?.value || 25);

/* helpers */
function qstring(params) {
  const parts = Object.entries(params)
    .filter(([k,v]) => v !== undefined && v !== null && String(v) !== '')
    .map(([k,v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`);
  return parts.length ? ('?' + parts.join('&')) : '';
}
function escapeHtml(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;'); }

/* Loading skeleton */
function showLoadingSkeleton() {
  const tbody = document.getElementById('grievanceTable');
  if (!tbody) return;
  let html = '';
  for (let i=0;i<5;i++){
    html += `<tr class="animate-pulse"><td colspan="9" class="px-6 py-6"><div class="h-4 bg-white/6 rounded w-3/4"></div></td></tr>`;
  }
  tbody.innerHTML = html;
}

/* load and populate filters (analytics & users) */
async function loadFilters() {
  try {
    const analytics = await fetchJSON(API_BASE + 'analytics/');
    const catSelect = document.getElementById('filter-category');
    if (catSelect && analytics && analytics.by_category) {
      Array.from(catSelect.querySelectorAll('option[data-dyn]')).forEach(n=>n.remove());
      analytics.by_category.forEach(c => {
        const opt = document.createElement('option'); opt.value = c.id || c.name; opt.textContent = c.name; opt.setAttribute('data-dyn','1'); catSelect.appendChild(opt);
      });
    }
  } catch(e) {
    console.warn('analytics error', e);
  }

  try {
    const users = await fetchJSON(API_BASE + 'user-status/');
    const offSelect = document.getElementById('filter-officer');
    if (offSelect && users && users.officers) {
      offSelect.innerHTML = '<option value="">Any officer</option>';
      users.officers.forEach(o => {
        const opt = document.createElement('option'); opt.value = o.id; opt.textContent = o.username || o.id;
        offSelect.appendChild(opt);
      });
    }
  } catch(e) { console.warn('user-status error', e); }
}

/* main: load grievances with filters & pagination */
async function loadGrievances(page=1) {
  currentPage = page;
  pageSize = parseInt(document.getElementById('page-size')?.value || 25);
  const params = {
    page, page_size: pageSize,
    status: document.getElementById('filter-status')?.value,
    category: document.getElementById('filter-category')?.value,
    assigned_officer: document.getElementById('filter-officer')?.value,
    date_from: document.getElementById('date-from')?.value,
    date_to: document.getElementById('date-to')?.value,
    search: document.getElementById('searchTop')?.value,
    ordering: '-created_at'
  };

  const qs = qstring(params);
  showLoadingSkeleton();
  try {
    const data = await fetchJSON(API_BASE + 'grievances/' + qs);
    renderTable(data);
  } catch(err) {
    console.error('Failed to load grievances', err);
    const tbody = document.getElementById('grievanceTable');
    if (tbody) tbody.innerHTML = `<tr><td colspan="9" class="px-6 py-12 text-center text-slate-300">Failed to load. Check console.</td></tr>`;
  }
}

/* render table rows + wire actions */
function renderTable(data) {
  const rows = Array.isArray(data) ? data : (data.results || []);
  const tbody = document.getElementById('grievanceTable'); tbody.innerHTML = '';
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="px-6 py-12 text-center text-slate-300">No grievances found.</td></tr>`;
    document.getElementById('total-count').textContent = data.count ?? 0;
    return;
  }

  rows.forEach(g => {
    const tr = document.createElement('tr');
    const statusBadge = (() => {
      if (g.status === 'new') return `<span class="badge badge-new">New</span>`;
      if (g.status === 'in_progress') return `<span class="badge badge-in">In progress</span>`;
      if (g.status === 'resolved') return `<span class="badge badge-resolved">Resolved</span>`;
      if (g.status === 'escalated') return `<span class="badge badge-escalated">Escalated</span>`;
      return `<span class="badge" style="background:rgba(255,255,255,0.04)">${g.status||''}</span>`;
    })();

    tr.innerHTML = `
      <td class="px-4 py-4">${g.id}</td>
      <td class="px-4 py-4">${g.tracking_id || '-'}</td>
      <td class="px-4 py-4"><a href="#" class="grv-link hover:underline" data-id="${g.id}">${escapeHtml(g.title)}</a></td>
      <td class="px-4 py-4">${g.user?.username || '-'}</td>
      <td class="px-4 py-4">${g.category?.name || '-'}</td>
      <td class="px-4 py-4">${g.assigned_officer?.username || '-'}</td>
      <td class="px-4 py-4">${statusBadge}</td>
      <td class="px-4 py-4">${g.created_at ? new Date(g.created_at).toLocaleString() : '-'}</td>
      <td class="px-4 py-4">
        <select data-id="${g.id}" class="status-select select-readable text-sm inline-block" aria-label="Change status">
          <option value="">Change</option>
          <option value="new">New</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="escalated">Escalated</option>
        </select>
        <button data-assign="${g.id}" class="ml-2 px-2 py-1 rounded bg-indigo-600 text-white text-sm">Assign</button>
        <button data-remark="${g.id}" class="ml-2 px-2 py-1 rounded bg-white/4 text-sm">Remark</button>
      </td>`;
    tbody.appendChild(tr);
  });

  // wire events
  document.querySelectorAll('.status-select').forEach(sel => sel.addEventListener('change', async (e) => {
    const id = e.target.getAttribute('data-id'); const status = e.target.value;
    if (!status) return;
    try {
      await fetchJSON(API_BASE + `grievances/${id}/`, { method: 'PATCH', body: { status }});
      await loadGrievances(currentPage);
    } catch(err) { alert('Failed to update status'); console.error(err); }
  }));

  document.querySelectorAll('button[data-assign]').forEach(btn => btn.addEventListener('click', async (e) => {
    const id = e.target.getAttribute('data-assign');
    let uid = document.getElementById('filter-officer')?.value;
    if (!uid) {
      uid = prompt('Enter officer id to assign:');
      if (!uid) return;
    }
    try {
      await fetchJSON(API_BASE + `grievances/${id}/assign/`, { method:'POST', body: { assigned_officer: parseInt(uid) }});
      await loadGrievances(currentPage);
    } catch(err) { alert('Assign failed'); console.error(err); }
  }));

  document.querySelectorAll('button[data-remark]').forEach(btn => btn.addEventListener('click', (e) => {
    const id = e.target.getAttribute('data-remark'); openRemarkModal(id);
  }));

  document.querySelectorAll('.grv-link').forEach(a => a.addEventListener('click', (e) => {
    e.preventDefault(); const id = a.getAttribute('data-id'); openDetailDrawer(id);
  }));

  document.getElementById('total-count').textContent = data.count ?? rows.length;
  document.getElementById('page-info').textContent = `Page ${currentPage} • ${data.count ?? rows.length} total`;
}

/* detail drawer */
async function openDetailDrawer(id) {
  const drawer = document.getElementById('detailDrawer');
  const header = document.getElementById('detailTitle');
  const sub = document.getElementById('detailSub');
  const body = document.getElementById('detailBody');

  header.textContent = 'Loading...';
  sub.textContent = '';
  body.innerHTML = '<div class="animate-pulse"><div class="h-4 bg-white/6 rounded w-1/2 mb-3"></div><div class="h-3 bg-white/6 rounded w-full"></div></div>';
  drawer.classList.remove('hidden');

  try {
    const data = await fetchJSON(API_BASE + `grievances/${id}/`);
    header.textContent = data.title || `#${data.id}`;
    sub.textContent = data.tracking_id || '';
    let html = `<div class="text-sm text-slate-300 mb-2"><strong>Submitted by:</strong> ${data.user?.username || '-'}</div>`;
    html += `<div class="text-sm mb-3">${escapeHtml(data.description || '')}</div>`;
    html += `<div class="space-y-2 text-sm text-slate-300">`;
    html += `<div><strong>Category:</strong> ${data.category?.name || '-'}</div>`;
    html += `<div><strong>Department:</strong> ${data.department?.name || '-'}</div>`;
    html += `<div><strong>Assigned:</strong> ${data.assigned_officer?.username || '-'}</div>`;
    html += `<div><strong>Status:</strong> ${data.status}</div>`;
    html += `</div>`;
    if (data.remarks && data.remarks.length) {
      html += `<hr class="my-3 border-white/6">`;
      html += `<div class="text-sm"><strong>Remarks</strong>`;
      data.remarks.slice(-5).reverse().forEach(r => {
        html += `<div class="mt-2 text-slate-200"><em>${r.officer?.username || 'Officer'}</em> — <span class="text-slate-300">${r.created_at}</span><div class="mt-1 text-sm">${escapeHtml(r.remark)}</div></div>`;
      });
      html += `</div>`;
    }
    body.innerHTML = html;
  } catch(err) {
    body.innerHTML = `<div class="text-sm text-red-400">Failed to load details.</div>`;
    console.error(err);
  }
}
document.getElementById('closeDrawer')?.addEventListener('click', ()=> {
  document.getElementById('detailDrawer').classList.add('hidden');
});

/* remark modal */
let currentRemarkTarget = null;
function openRemarkModal(id) {
  currentRemarkTarget = id;
  document.getElementById('remarkInfo').textContent = `Grievance #${id}`;
  document.getElementById('remarkText').value = '';
  const modal = document.getElementById('remarkModal');
  modal.classList.remove('hidden'); modal.classList.add('flex');
}
document.getElementById('remarkCancel')?.addEventListener('click', ()=> {
  const modal = document.getElementById('remarkModal'); modal.classList.add('hidden'); modal.classList.remove('flex');
});
document.getElementById('remarkClose')?.addEventListener('click', ()=> {
  const modal = document.getElementById('remarkModal'); modal.classList.add('hidden'); modal.classList.remove('flex');
});
document.getElementById('remarkSave')?.addEventListener('click', async ()=> {
  const text = document.getElementById('remarkText').value.trim();
  if (!text) return alert('Please write a remark');
  try {
    await fetchJSON(API_BASE + `grievances/${currentRemarkTarget}/remarks/`, { method:'POST', body: { remark: text }});
    const modal = document.getElementById('remarkModal'); modal.classList.add('hidden'); modal.classList.remove('flex');
    await loadGrievances(currentPage);
  } catch(err) { alert('Failed to save remark'); console.error(err); }
});

/* export CSV */
document.getElementById('exportCsv')?.addEventListener('click', async ()=> {
  const params = {
    page: currentPage, page_size: pageSize,
    status: document.getElementById('filter-status')?.value,
    category: document.getElementById('filter-category')?.value,
    assigned_officer: document.getElementById('filter-officer')?.value,
    date_from: document.getElementById('date-from')?.value,
    date_to: document.getElementById('date-to')?.value
  };
  const qs = qstring(params);
  try {
    const data = await fetchJSON(API_BASE + 'grievances/' + qs);
    const rows = (Array.isArray(data) ? data : data.results || []).map(i => ({id:i.id, tracking_id:i.tracking_id, title:i.title, user:i.user?.username||'', category:i.category?.name||'', assigned_officer:i.assigned_officer?.username||'', status:i.status, created_at:i.created_at}));
    if (!rows.length) return alert('No data to export');
    const keys = Object.keys(rows[0]);
    const csv = [keys.join(',')].concat(rows.map(r => keys.map(k => `"${String(r[k]||'').replace(/"/g,'""')}"`).join(','))).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'grievances.csv'; a.click(); URL.revokeObjectURL(url);
  } catch(e) { alert('Export failed'); console.error(e); }
});

/* pagination & filters */
document.getElementById('applyFilters')?.addEventListener('click', ()=> loadGrievances(1));
document.getElementById('resetFilters')?.addEventListener('click', ()=> {
  document.getElementById('searchTop').value = '';
  document.getElementById('filter-status').value = '';
  document.getElementById('filter-category').value = '';
  document.getElementById('filter-officer').value = '';
  document.getElementById('date-from').value = '';
  document.getElementById('date-to').value = '';
  loadGrievances(1);
});
document.getElementById('nextPage')?.addEventListener('click', ()=> loadGrievances(currentPage + 1));
document.getElementById('prevPage')?.addEventListener('click', ()=> { if (currentPage > 1) loadGrievances(currentPage - 1); });
document.getElementById('page-size')?.addEventListener('change', ()=> loadGrievances(1));

/* search debounce */
function debounce(fn, wait = 400) {
  let t = null;
  return function(...args) { clearTimeout(t); t = setTimeout(()=> fn.apply(this, args), wait); };
}
const searchTop = document.getElementById('searchTop');
if (searchTop) {
  searchTop.addEventListener('keydown', (e)=> { if (e.key === 'Enter') { e.preventDefault(); loadGrievances(1); }});
  searchTop.addEventListener('input', debounce(()=> loadGrievances(1), 500));
  document.getElementById('searchBtn')?.addEventListener('click', (e)=> { e.preventDefault(); loadGrievances(1); });
}

/* init */
(async function init(){
  await loadFilters();
  await loadGrievances(1);
})();



