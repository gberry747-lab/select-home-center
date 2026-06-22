/* Select Home Center — site interactions */
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

  // Lead form — graceful UX. Works once a real Formspree ID is set.
  var form = document.getElementById('leadForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      var action = form.getAttribute('action') || '';
      if (action.indexOf('YOUR_FORM_ID') !== -1) {
        // Not configured yet — prevent broken submit, guide to call.
        e.preventDefault();
        alert('Thanks! Online form setup is being finalized.\n\nFor the fastest response, please call or text us at 912-208-6065.');
        return;
      }
      var btn = form.querySelector('button[type="submit"]');
      if (btn) { btn.textContent = 'Sending…'; btn.disabled = true; }
    });
  }
})();
