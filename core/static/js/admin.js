// =========================================================
// अपना घर वृद्ध आश्रम — admin.js
// Front-end data layer for the Admin / Volunteer panel.
//
// Milestone 3: the data layer below talks to the Django+MySQL API under
// /admin/api/ (see clothingbank/views.py) instead of localStorage.
// Milestone 4 adds Contact Enquiries (view/mark-handled) and an optional
// Reports date-range filter on top of that same data layer.
// =========================================================

(function () {

  /* =========================================================
     DATA LAYER (Django + MySQL API under /admin/api/)
     ========================================================= */
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  var db = { donors: [], inventory: [], issues: [], enquiries: [] };

  async function apiPost(url, payload) {
    var res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(payload)
    });
    var data = await res.json();
    if (!res.ok) {
      var err = new Error(data.error || 'Request failed');
      err.data = data;
      throw err;
    }
    return data;
  }

  async function loadDB() {
    var res = await fetch('/admin/api/data/');
    var data = await res.json();
    db.donors = data.donors;
    db.inventory = data.inventory;
    db.issues = data.issues;
    db.enquiries = data.enquiries;
    return db;
  }

  // Reports-only date-range fetch — deliberately does NOT touch the shared
  // `db` object, so Dashboard/Donor/Inventory/Issue tables never get
  // filtered by a Reports date range (additive, not a replacement).
  async function fetchReportsRange(fromDate, toDate) {
    var params = new URLSearchParams();
    if (fromDate) params.set('from', fromDate);
    if (toDate) params.set('to', toDate);
    var qs = params.toString();
    var res = await fetch('/admin/api/data/' + (qs ? '?' + qs : ''));
    return res.json();
  }

  async function addDonor(entry) {
    var created = await apiPost('/admin/api/donors/', entry);
    db.donors.unshift(created);
    return created;
  }

  async function upsertInventory(entry) {
    var saved = await apiPost('/admin/api/inventory/', entry);
    var existing = db.inventory.find(function (i) { return i.shelf.toUpperCase() === saved.shelf.toUpperCase(); });
    if (existing) {
      Object.assign(existing, saved);
    } else {
      db.inventory.unshift(saved);
    }
    return saved;
  }

  // Issuing clothes can deduct from several shelves at once (server-side,
  // inside a locked transaction) — reload the full dataset afterwards so
  // inventory quantities shown here stay correct.
  async function addIssue(entry) {
    await apiPost('/admin/api/issues/', entry);
    await loadDB();
  }

  async function markEnquiryHandled(id) {
    var updated = await apiPost('/admin/api/enquiries/' + id + '/handle/', {});
    var idx = db.enquiries.findIndex(function (e) { return e.id == id; });
    if (idx !== -1) db.enquiries[idx] = updated;
    return updated;
  }

  // Site Content (Super Admin only) — separate from `db` since it's only
  // ever fetched/rendered when the section exists in the DOM at all.
  var siteImages = [];

  async function loadSiteImages() {
    var res = await fetch('/admin/api/site-images/');
    var data = await res.json();
    siteImages = data.site_images || [];
    return siteImages;
  }

  async function uploadSiteImage(key, file) {
    var formData = new FormData();
    formData.append('image', file);
    var res = await fetch('/admin/api/site-images/' + key + '/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
      body: formData
    });
    var data = await res.json();
    if (!res.ok) {
      var err = new Error(data.error || 'Upload failed');
      err.data = data;
      throw err;
    }
    return data;
  }

  /* =========================================================
     HELPERS
     ========================================================= */
  function sum(arr, key) { return arr.reduce(function (s, i) { return s + Number(i[key] || 0); }, 0); }
  function isToday(dateStr) { return dateStr === new Date().toISOString().slice(0, 10); }
  function isThisMonth(dateStr) {
    if (!dateStr) return false;
    var d = new Date(dateStr), now = new Date();
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth();
  }
  function escapeHtml(str) {
    return String(str == null ? '' : str).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function statusBadge(status) {
    var cls = status === 'Available' ? 'badge-status-available' : status === 'Given' ? 'badge-status-given' : 'badge-status-damaged';
    return '<span class="badge ' + cls + '">' + status + '</span>';
  }
  function downloadCsv(filename, rows) {
    var csv = rows.map(function (row) {
      return row.map(function (cell) {
        var v = String(cell == null ? '' : cell);
        if (v.indexOf(',') !== -1 || v.indexOf('"') !== -1 || v.indexOf('\n') !== -1) {
          v = '"' + v.replace(/"/g, '""') + '"';
        }
        return v;
      }).join(',');
    }).join('\r\n');
    var blob = new Blob(["\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  /* =========================================================
     RENDER FUNCTIONS
     ========================================================= */
  function renderDashboard() {
    document.getElementById('kpiReceived').textContent = sum(db.donors, 'count').toLocaleString('en-IN');
    document.getElementById('kpiGiven').textContent = sum(db.issues, 'count').toLocaleString('en-IN');
    var available = sum(db.inventory.filter(function (i) { return i.status === 'Available'; }), 'qty');
    document.getElementById('kpiAvailable').textContent = available.toLocaleString('en-IN');
    document.getElementById('kpiDonors').textContent = db.donors.length.toLocaleString('en-IN');

    var recentDonations = db.donors.slice(0, 6).map(function (d) {
      return '<tr><td>' + escapeHtml(d.name) + '</td><td>' + d.category + '</td><td>' + d.count + '</td><td>' + d.date + '</td></tr>';
    }).join('') || '<tr><td colspan="4" class="text-muted text-center py-3">No donations yet</td></tr>';
    document.getElementById('recentDonationsBody').innerHTML = recentDonations;

    var recentIssues = db.issues.slice(0, 6).map(function (i) {
      return '<tr><td>' + escapeHtml(i.name) + '</td><td>' + i.category + '</td><td>' + i.count + '</td><td>' + i.date + '</td></tr>';
    }).join('') || '<tr><td colspan="4" class="text-muted text-center py-3">No distributions yet</td></tr>';
    document.getElementById('recentIssuesBody').innerHTML = recentIssues;
  }

  function renderDonors() {
    document.getElementById('donorsBody').innerHTML = db.donors.map(function (d) {
      return '<tr><td>' + escapeHtml(d.name) + '</td><td>' + escapeHtml(d.mobile) + '</td><td>' + d.category +
        '</td><td>' + d.count + '</td><td>' + d.date + '</td><td>' + escapeHtml(d.remarks) + '</td></tr>';
    }).join('') || '<tr><td colspan="6" class="text-muted text-center py-3">No donors yet — add the first one!</td></tr>';
  }

  function renderInventory() {
    document.getElementById('inventoryBody').innerHTML = db.inventory.map(function (i) {
      return '<tr><td><strong>' + escapeHtml(i.shelf) + '</strong></td><td>' + i.category + '</td><td>' + escapeHtml(i.size) +
        '</td><td>' + i.qty + '</td><td>' + statusBadge(i.status) + '</td>' +
        '<td><button class="btn btn-sm btn-outline-secondary edit-shelf-btn" data-id="' + i.id + '"><i class="bi bi-pencil"></i></button></td></tr>';
    }).join('') || '<tr><td colspan="6" class="text-muted text-center py-3">No shelves added yet</td></tr>';

    document.querySelectorAll('.edit-shelf-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var item = db.inventory.find(function (i) { return i.id == btn.getAttribute('data-id'); });
        if (!item) return;
        document.getElementById('iCategory').value = item.category;
        document.getElementById('iSize').value = item.size;
        document.getElementById('iShelf').value = item.shelf;
        document.getElementById('iQty').value = item.qty;
        document.getElementById('iStatus').value = item.status;
        document.getElementById('iShelf').focus();
      });
    });
  }

  function renderIssues() {
    document.getElementById('issuesBody').innerHTML = db.issues.map(function (i) {
      return '<tr><td>' + escapeHtml(i.name) + '</td><td>' + escapeHtml(i.mobile) + '</td><td>' + i.category +
        '</td><td>' + i.count + '</td><td>' + i.date + '</td></tr>';
    }).join('') || '<tr><td colspan="5" class="text-muted text-center py-3">No clothes issued yet</td></tr>';
  }

  // reportsFilteredData is null when no Reports date range is active, in
  // which case Reports behaves exactly as before (computed from the full,
  // shared `db`). When a range is applied it holds { donors, issues } for
  // just that range — Dashboard/Donor/Inventory/Issue sections keep using
  // the full `db` regardless, since the filter is additive to Reports only.
  var reportsFilteredData = null;

  function renderReports() {
    var source = reportsFilteredData || db;
    var todayDonations = sum(source.donors.filter(function (d) { return isToday(d.date); }), 'count');
    var todayIssues = sum(source.issues.filter(function (i) { return isToday(i.date); }), 'count');
    var monthDonations = sum(source.donors.filter(function (d) { return isThisMonth(d.date); }), 'count');
    var stock = sum(db.inventory.filter(function (i) { return i.status === 'Available'; }), 'qty');

    document.getElementById('repToday').textContent = todayDonations;
    document.getElementById('repTodayGiven').textContent = todayIssues;
    document.getElementById('repMonth').textContent = monthDonations;
    document.getElementById('repStock').textContent = stock;

    var logRows = [];
    source.donors.forEach(function (d) { logRows.push({ type: 'Donation', name: d.name, category: d.category, qty: d.count, date: d.date }); });
    source.issues.forEach(function (i) { logRows.push({ type: 'Distribution', name: i.name, category: i.category, qty: i.count, date: i.date }); });
    logRows.sort(function (a, b) { return (b.date || '').localeCompare(a.date || ''); });

    document.getElementById('activityLogBody').innerHTML = logRows.map(function (r) {
      var badge = r.type === 'Donation'
        ? '<span class="badge" style="background:var(--terracotta);">Donation</span>'
        : '<span class="badge" style="background:var(--mustard);">Distribution</span>';
      return '<tr><td>' + badge + '</td><td>' + escapeHtml(r.name) + '</td><td>' + r.category + '</td><td>' + r.qty + '</td><td>' + r.date + '</td></tr>';
    }).join('') || '<tr><td colspan="5" class="text-muted text-center py-3">No activity yet</td></tr>';
  }

  function renderEnquiries() {
    document.getElementById('enquiriesBody').innerHTML = db.enquiries.map(function (e) {
      var action = e.status === 'New'
        ? '<button class="btn btn-sm btn-ag-outline-dark mark-handled-btn" data-id="' + e.id + '"><i class="bi bi-check2"></i> Mark Handled</button>'
        : '<span class="text-muted small">' + (e.handled_by ? 'by ' + escapeHtml(e.handled_by) : '') + '</span>';
      var badgeCls = e.status === 'Handled' ? 'badge-status-available' : 'badge-status-given';
      return '<tr><td>' + escapeHtml(e.name) + '</td><td>' + escapeHtml(e.mobile) + '</td><td>' + escapeHtml(e.subject) +
        '</td><td>' + escapeHtml(e.message) + '</td><td>' + e.submitted_at.slice(0, 10) +
        '</td><td><span class="badge ' + badgeCls + '">' + e.status + '</span></td><td>' + action + '</td></tr>';
    }).join('') || '<tr><td colspan="7" class="text-muted text-center py-3">No enquiries yet</td></tr>';

    document.querySelectorAll('.mark-handled-btn').forEach(function (btn) {
      btn.addEventListener('click', async function () {
        btn.disabled = true;
        try {
          await markEnquiryHandled(btn.getAttribute('data-id'));
          renderEnquiries();
        } catch (err) {
          alert(err.message || 'Could not mark this enquiry as handled.');
          btn.disabled = false;
        }
      });
    });
  }

  function renderSiteImages() {
    var grid = document.getElementById('siteImagesGrid');
    if (!grid) return; // not rendered in the DOM at all for non-superusers

    grid.innerHTML = siteImages.map(function (s) {
      var thumb = s.image_url
        ? '<img src="' + s.image_url + '" alt="' + escapeHtml(s.alt_text || s.label) + '" style="width:100%;height:140px;object-fit:cover;border-radius:10px;margin-bottom:10px;">'
        : '<div class="d-flex align-items-center justify-content-center text-muted small text-center" style="width:100%;height:140px;border-radius:10px;background:var(--terracotta-pale);margin-bottom:10px;"><span><i class="bi bi-image me-1"></i>Default illustration</span></div>';
      return '<div class="col-md-4 col-6">' +
        '<div class="admin-card p-3 text-center mb-0 h-100">' + thumb +
        '<div class="fw-bold small mb-1">' + escapeHtml(s.label) + '</div>' +
        '<div class="text-muted small mb-2">' + escapeHtml(s.key) + '</div>' +
        '<input type="file" accept="image/*" class="d-none site-image-input" data-key="' + escapeHtml(s.key) + '">' +
        '<button type="button" class="btn btn-sm btn-ag-outline-dark site-image-upload-btn" data-key="' + escapeHtml(s.key) + '"><i class="bi bi-upload me-1"></i>Upload / Replace</button>' +
        '</div></div>';
    }).join('') || '<p class="text-muted">No image slots found.</p>';

    grid.querySelectorAll('.site-image-upload-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var key = btn.getAttribute('data-key');
        grid.querySelector('.site-image-input[data-key="' + key + '"]').click();
      });
    });
    grid.querySelectorAll('.site-image-input').forEach(function (input) {
      input.addEventListener('change', async function () {
        var key = input.getAttribute('data-key');
        var file = input.files[0];
        if (!file) return;
        try {
          await uploadSiteImage(key, file);
          await loadSiteImages();
          renderSiteImages();
        } catch (err) {
          alert(err.message || 'Could not upload this image.');
          input.value = '';
        }
      });
    });
  }

  function renderAll() {
    renderDashboard();
    renderDonors();
    renderInventory();
    renderIssues();
    renderEnquiries();
    renderReports();
  }

  /* =========================================================
     SIDEBAR NAVIGATION
     ========================================================= */
  var sectionTitles = {
    dashboard: 'Dashboard Overview',
    donor: 'Donor Entry',
    inventory: 'Shelf Inventory',
    issue: 'Issue Clothes',
    enquiries: 'Contact Enquiries',
    reports: 'Reports',
    'site-content': 'Site Content'
  };

  document.querySelectorAll('.nav-section-link').forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      var target = link.getAttribute('data-section');
      document.querySelectorAll('.nav-section-link').forEach(function (l) { l.classList.remove('active'); });
      link.classList.add('active');
      // 'site-content' only exists in the DOM for superusers — guard the
      // lookup so this loop is a no-op for everyone else instead of throwing.
      ['dashboard', 'donor', 'inventory', 'issue', 'enquiries', 'reports', 'site-content'].forEach(function (s) {
        var el = document.getElementById('sec-' + s);
        if (el) el.classList.toggle('d-none', s !== target);
      });
      document.getElementById('pageHeading').textContent = sectionTitles[target];
      var sidebar = document.getElementById('adminSidebar');
      if (window.innerWidth < 992) sidebar.classList.remove('show-mobile');
    });
  });

  var sidebarToggle = document.getElementById('sidebarToggle');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function () {
      document.getElementById('adminSidebar').classList.toggle('show-mobile');
    });
  }

  /* =========================================================
     FORM HANDLERS
     ========================================================= */
  var donorForm = document.getElementById('donorForm');
  if (donorForm) {
    document.getElementById('dDate').value = new Date().toISOString().slice(0, 10);
    donorForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      try {
        await addDonor({
          name: document.getElementById('dName').value.trim(),
          mobile: document.getElementById('dMobile').value.trim(),
          whatsapp: document.getElementById('dWhatsapp').value.trim(),
          address: document.getElementById('dAddress').value.trim(),
          date: document.getElementById('dDate').value,
          category: document.getElementById('dCategory').value,
          count: parseInt(document.getElementById('dCount').value, 10) || 0,
          remarks: document.getElementById('dRemarks').value.trim()
        });
        donorForm.reset();
        document.getElementById('dDate').value = new Date().toISOString().slice(0, 10);
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not save donor.');
      }
    });
  }

  var inventoryForm = document.getElementById('inventoryForm');
  if (inventoryForm) {
    inventoryForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      try {
        await upsertInventory({
          category: document.getElementById('iCategory').value,
          size: document.getElementById('iSize').value,
          shelf: document.getElementById('iShelf').value.trim().toUpperCase(),
          qty: parseInt(document.getElementById('iQty').value, 10) || 0,
          status: document.getElementById('iStatus').value
        });
        inventoryForm.reset();
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not save shelf.');
      }
    });
  }

  var issueForm = document.getElementById('issueForm');
  if (issueForm) {
    document.getElementById('pDate').value = new Date().toISOString().slice(0, 10);
    issueForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      var category = document.getElementById('pCategory').value;
      var count = parseInt(document.getElementById('pCount').value, 10) || 0;
      var errBox = document.getElementById('issueError');
      errBox.classList.add('d-none');

      try {
        await addIssue({
          name: document.getElementById('pName').value.trim(),
          mobile: document.getElementById('pMobile').value.trim(),
          address: document.getElementById('pAddress').value.trim(),
          category: category,
          count: count,
          date: document.getElementById('pDate').value
        });
        issueForm.reset();
        document.getElementById('pDate').value = new Date().toISOString().slice(0, 10);
        renderAll();
      } catch (err) {
        errBox.textContent = (err.data && err.data.error) ||
          'Not enough stock available in "' + category + '" category. Please check Inventory.';
        errBox.classList.remove('d-none');
      }
    });
  }

  /* =========================================================
     REPORTS DATE FILTER
     ========================================================= */
  var repApplyFilterBtn = document.getElementById('repApplyFilterBtn');
  var repClearFilterBtn = document.getElementById('repClearFilterBtn');

  if (repApplyFilterBtn) {
    repApplyFilterBtn.addEventListener('click', async function () {
      var fromDate = document.getElementById('repFromDate').value;
      var toDate = document.getElementById('repToDate').value;
      if (!fromDate && !toDate) {
        reportsFilteredData = null;
        renderReports();
        return;
      }
      try {
        var data = await fetchReportsRange(fromDate, toDate);
        reportsFilteredData = { donors: data.donors, issues: data.issues };
        renderReports();
      } catch (err) {
        alert('Could not load report data for that date range.');
      }
    });
  }

  if (repClearFilterBtn) {
    repClearFilterBtn.addEventListener('click', function () {
      document.getElementById('repFromDate').value = '';
      document.getElementById('repToDate').value = '';
      reportsFilteredData = null;
      renderReports();
    });
  }

  /* =========================================================
     EXPORTS
     ========================================================= */
  function bind(id, fn) { var el = document.getElementById(id); if (el) el.addEventListener('click', fn); }

  bind('exportDonorsBtn', function () {
    var rows = [['Name', 'Mobile', 'WhatsApp', 'Address', 'Date', 'Category', 'Quantity', 'Remarks']];
    db.donors.forEach(function (d) { rows.push([d.name, d.mobile, d.whatsapp, d.address, d.date, d.category, d.count, d.remarks]); });
    downloadCsv('donors.csv', rows);
  });

  bind('exportInventoryBtn', function () {
    var rows = [['Shelf', 'Category', 'Size', 'Quantity', 'Status']];
    db.inventory.forEach(function (i) { rows.push([i.shelf, i.category, i.size, i.qty, i.status]); });
    downloadCsv('inventory.csv', rows);
  });

  bind('exportIssuesBtn', function () {
    var rows = [['Name', 'Mobile', 'Address', 'Category', 'Quantity', 'Date']];
    db.issues.forEach(function (i) { rows.push([i.name, i.mobile, i.address, i.category, i.count, i.date]); });
    downloadCsv('distributions.csv', rows);
  });

  bind('exportDonationsReportBtn', function () {
    var rows = [['Name', 'Mobile', 'Category', 'Quantity', 'Date', 'Remarks']];
    db.donors.forEach(function (d) { rows.push([d.name, d.mobile, d.category, d.count, d.date, d.remarks]); });
    downloadCsv('donations_report.csv', rows);
  });

  bind('exportIssuesReportBtn', function () {
    var rows = [['Name', 'Mobile', 'Category', 'Quantity', 'Date']];
    db.issues.forEach(function (i) { rows.push([i.name, i.mobile, i.category, i.count, i.date]); });
    downloadCsv('distribution_report.csv', rows);
  });

  bind('exportStockReportBtn', function () {
    var rows = [['Shelf', 'Category', 'Size', 'Quantity', 'Status']];
    db.inventory.forEach(function (i) { rows.push([i.shelf, i.category, i.size, i.qty, i.status]); });
    downloadCsv('stock_report.csv', rows);
  });

  /* Initial load + render (data now comes from the server) */
  loadDB().then(renderAll).catch(function (err) {
    console.error('Failed to load clothing bank data', err);
  });

  // Site Content is only in the DOM for superusers — skip the fetch
  // entirely for everyone else rather than hitting an endpoint that will
  // just 403.
  if (document.getElementById('siteImagesGrid')) {
    loadSiteImages().then(renderSiteImages).catch(function (err) {
      console.error('Failed to load site images', err);
    });
  }

})();
