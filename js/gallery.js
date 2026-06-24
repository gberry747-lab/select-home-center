/* Select Home Center - model photo lightbox (accessible) */
(function () {
  'use strict';
  var grid = document.querySelector('.gal-grid');
  if (!grid) return;
  var thumbs = [].slice.call(grid.querySelectorAll('.gphoto'));
  var photos = thumbs.map(function (a) { return a.getAttribute('href'); });
  if (!photos.length) return;

  var lb = document.createElement('div');
  lb.className = 'lb';
  lb.setAttribute('role', 'dialog');
  lb.setAttribute('aria-modal', 'true');
  lb.setAttribute('aria-label', 'Photo viewer');
  lb.innerHTML =
    '<button class="lb-close" type="button" aria-label="Close photo viewer">&times;</button>' +
    '<button class="lb-nav lb-prev" type="button" aria-label="Previous photo">&#8249;</button>' +
    '<img alt="Home photo">' +
    '<button class="lb-nav lb-next" type="button" aria-label="Next photo">&#8250;</button>' +
    '<div class="lb-count" aria-live="polite"></div>';
  document.body.appendChild(lb);

  var img = lb.querySelector('img');
  var count = lb.querySelector('.lb-count');
  var closeBtn = lb.querySelector('.lb-close');
  var idx = 0;
  var lastFocus = null;

  function show(i) {
    idx = (i + photos.length) % photos.length;
    img.src = photos[idx];
    count.textContent = 'Photo ' + (idx + 1) + ' of ' + photos.length;
  }
  function open(i) {
    lastFocus = document.activeElement;
    show(i);
    lb.classList.add('open');
    document.body.style.overflow = 'hidden';
    closeBtn.focus();
  }
  function close() {
    lb.classList.remove('open');
    document.body.style.overflow = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  thumbs.forEach(function (a, i) {
    a.addEventListener('click', function (e) { e.preventDefault(); open(i); });
  });
  closeBtn.addEventListener('click', close);
  lb.querySelector('.lb-prev').addEventListener('click', function () { show(idx - 1); });
  lb.querySelector('.lb-next').addEventListener('click', function () { show(idx + 1); });
  lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
  document.addEventListener('keydown', function (e) {
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') show(idx - 1);
    else if (e.key === 'ArrowRight') show(idx + 1);
  });
})();
