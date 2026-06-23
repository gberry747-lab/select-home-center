/* Select Home Center - site interactions */
(function () {
  'use strict';

  // Sticky header background on scroll
  var header = document.getElementById('header');
  function onScroll() {
    if (window.scrollY > 40) header.classList.add('scrolled');
    else header.classList.remove('scrolled');
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Mobile menu toggle
  var burger = document.getElementById('hamburger');
  var links = document.getElementById('navLinks');
  if (burger && links) {
    burger.addEventListener('click', function () {
      links.classList.toggle('open');
    });
    links.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { links.classList.remove('open'); });
    });
  }

  // Lead form - AJAX submit to Formspree with an inline success message (no page redirect).
  var form = document.getElementById('leadForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var action = form.getAttribute('action') || '';
      if (action.indexOf('YOUR_FORM_ID') !== -1) {
        alert('Thanks! Please call or text us at 912-208-6065. Our online form is being finalized.');
        return;
      }
      var btn = form.querySelector('button[type="submit"]');
      var orig = btn ? btn.textContent : '';
      if (btn) { btn.textContent = 'Sending…'; btn.disabled = true; }
      fetch(action, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } })
        .then(function (r) {
          if (!r.ok) throw new Error('bad response');
          form.innerHTML = '<div style="text-align:center;padding:24px 8px">' +
            '<h3 style="color:var(--navy);font-family:Montserrat,sans-serif;font-size:1.5rem;margin-bottom:10px">Thank you! &#127881;</h3>' +
            '<p style="color:var(--gray);font-size:1.02rem">We\'ve got your request and will reach out within one business day.<br>Prefer to talk now? Call or text <a href="tel:9122086065" style="color:var(--navy);font-weight:700">912-208-6065</a>.</p></div>';
        })
        .catch(function () {
          if (btn) { btn.textContent = orig; btn.disabled = false; }
          alert('Sorry, something went wrong sending your request. Please call or text 912-208-6065 and we\'ll help right away.');
        });
    });
  }
})();
