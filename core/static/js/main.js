// =========================================================
// अपना घर वृद्ध आश्रम — main.js
// Shared behaviour across all public pages
// =========================================================

document.addEventListener('DOMContentLoaded', function () {

  /* ---------- Highlight active nav link ---------- */
  var path = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.navbar-ag .nav-link[data-page]').forEach(function (link) {
    if (link.getAttribute('data-page') === path) {
      link.classList.add('active');
    }
  });

  /* ---------- Animated counters (Home page stats) ---------- */
  var counters = document.querySelectorAll('.stat-num[data-count]');
  if (counters.length) {
    var animated = false;
    var runCounters = function () {
      if (animated) return;
      animated = true;
      counters.forEach(function (el) {
        var target = parseInt(el.getAttribute('data-count'), 10) || 0;
        var suffix = el.getAttribute('data-suffix') || '';
        var duration = 1200;
        var startTime = null;
        function step(ts) {
          if (!startTime) startTime = ts;
          var progress = Math.min((ts - startTime) / duration, 1);
          var value = Math.floor(progress * target);
          el.textContent = value.toLocaleString('en-IN') + suffix;
          if (progress < 1) requestAnimationFrame(step);
          else el.textContent = target.toLocaleString('en-IN') + suffix;
        }
        requestAnimationFrame(step);
      });
    };
    var statsSection = document.querySelector('.stats-strip');
    if (statsSection && 'IntersectionObserver' in window) {
      var obs = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) runCounters();
        });
      }, { threshold: 0.4 });
      obs.observe(statsSection);
    } else {
      runCounters();
    }
  }

  /* ---------- Lightbox (used on Gallery page) ---------- */
  var lightbox = document.getElementById('lightbox');
  if (lightbox) {
    var lbImg = lightbox.querySelector('img');
    var lbCaption = lightbox.querySelector('.lightbox-caption');
    var items = Array.prototype.slice.call(document.querySelectorAll('.gallery-item'));
    var currentIndex = 0;

    function openLightbox(index) {
      currentIndex = index;
      var img = items[index].querySelector('img');
      lbImg.src = img.src;
      lbImg.alt = img.alt;
      lbCaption.textContent = img.getAttribute('data-caption') || img.alt || '';
      lightbox.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
    function closeLightbox() {
      lightbox.classList.remove('active');
      document.body.style.overflow = '';
    }
    function showNext(delta) {
      currentIndex = (currentIndex + delta + items.length) % items.length;
      openLightbox(currentIndex);
    }

    items.forEach(function (item, index) {
      item.addEventListener('click', function () { openLightbox(index); });
      item.setAttribute('tabindex', '0');
      item.setAttribute('role', 'button');
      item.setAttribute('aria-label', 'Open image in full screen');
      item.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openLightbox(index); }
      });
    });

    var closeBtn = lightbox.querySelector('.lightbox-close');
    var prevBtn = lightbox.querySelector('.lightbox-prev');
    var nextBtn = lightbox.querySelector('.lightbox-next');
    if (closeBtn) closeBtn.addEventListener('click', closeLightbox);
    if (prevBtn) prevBtn.addEventListener('click', function () { showNext(-1); });
    if (nextBtn) nextBtn.addEventListener('click', function () { showNext(1); });
    lightbox.addEventListener('click', function (e) {
      if (e.target === lightbox) closeLightbox();
    });
    document.addEventListener('keydown', function (e) {
      if (!lightbox.classList.contains('active')) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft') showNext(-1);
      if (e.key === 'ArrowRight') showNext(1);
    });
  }

  /* ---------- Donation amount selector (Donate page) ---------- */
  var donateTiles = document.querySelectorAll('.donate-tile[data-amount]');
  var customInput = document.getElementById('customAmount');
  var selectedAmountDisplay = document.getElementById('selectedAmountDisplay');

  function setSelectedAmount(amount) {
    if (selectedAmountDisplay) {
      selectedAmountDisplay.textContent = '₹' + Number(amount).toLocaleString('en-IN');
    }
  }

  donateTiles.forEach(function (tile) {
    tile.addEventListener('click', function () {
      donateTiles.forEach(function (t) { t.classList.remove('selected'); });
      tile.classList.add('selected');
      var amount = tile.getAttribute('data-amount');
      if (amount === 'custom') {
        if (customInput) { customInput.focus(); }
      } else {
        if (customInput) customInput.value = '';
        setSelectedAmount(amount);
      }
    });
  });
  if (customInput) {
    customInput.addEventListener('input', function () {
      if (this.value) {
        donateTiles.forEach(function (t) { t.classList.remove('selected'); });
        var customTile = document.querySelector('.donate-tile[data-amount="custom"]');
        if (customTile) customTile.classList.add('selected');
        setSelectedAmount(this.value);
      }
    });
  }

  var donateForm = document.getElementById('donateForm');
  if (donateForm) {
    donateForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = document.getElementById('donorName');
      var msgBox = document.getElementById('donateConfirmMsg');
      if (msgBox) {
        msgBox.classList.remove('d-none');
        msgBox.textContent = 'धन्यवाद' + (name && name.value ? ', ' + name.value : '') +
          '! Please complete your payment using the QR code or bank details below, and share the payment screenshot on WhatsApp so we can send your receipt.';
        msgBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  }

  /* ---------- Contact form (posts to /contact/submit/) ---------- */
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

  var contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      var msgBox = document.getElementById('contactConfirmMsg');
      var submitBtn = contactForm.querySelector('button[type="submit"]');
      if (submitBtn) submitBtn.disabled = true;

      try {
        var res = await fetch('/contact/submit/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: JSON.stringify({
            name: document.getElementById('cName').value.trim(),
            mobile: document.getElementById('cMobile').value.trim(),
            subject: document.getElementById('cSubject').value,
            message: document.getElementById('cMessage').value.trim()
          })
        });
        var data = await res.json();

        if (!res.ok) {
          alert(data.error || 'Could not send your message. Please try again.');
          return;
        }

        if (msgBox) {
          msgBox.classList.remove('d-none');
          contactForm.reset();
          msgBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      } catch (err) {
        alert('Could not send your message. Please check your connection and try again.');
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  /* ---------- Back-to-top / mobile nav auto-close ---------- */
  var navLinks = document.querySelectorAll('.navbar-ag .nav-link, .navbar-ag .btn-donate-nav');
  var navCollapse = document.getElementById('mainNav');
  if (navCollapse) {
    navLinks.forEach(function (link) {
      link.addEventListener('click', function () {
        if (navCollapse.classList.contains('show')) {
          var bsCollapse = bootstrap.Collapse.getOrCreateInstance(navCollapse);
          bsCollapse.hide();
        }
      });
    });
  }
});
