/* Select Home Center — model photo lightbox */
(function () {
  'use strict';
  var grid = document.querySelector('.gal-grid');
  if (!grid) return;
  var thumbs = [].slice.call(grid.querySelectorAll('.gphoto'));
  var photos = thumbs.map(function (a) { return a.getAttribute('href'); });
  if (!photos.length) return;

  var lb = document.createElement('div');
  lb.className = 'lb';
  lb.innerHTML =
    '<button class="lb-close" aria-label="Close">&times;</button>' +
    '<button class="lb-nav lb-prev" aria-label="Previous">&#8249;</button>' +
    '<img alt="Home photo">' +
    '<button class="lb-nav lb-next" aria-label="Next">&#8250;</button>' +
    '<div class="lb-count"></div>';
  document.body.appendChild(lb);

  var img = lb.querySelector('img');
  var count = lb.querySelector('.lb-count');
  var idx = 0;

  function show(i) {
    idx = (i + photos.length) % photos.length;
    img.src = photos[idx];
    count.textContent = (idx + 1) + ' / ' + photos.length;
  }
  function open(i) { show(i); lb.classList.add('open'); document.body.style.overflow = 'hidden'; }
  function close() { lb.classList.remove('open'); document.body.style.overflow = ''; }

  thumbs.forEach(function (a, i) {
    a.addEventListener('click', function (e) { e.preventDefault(); open(i); });
  });
  lb.querySelector('.lb-close').addEventListener('click', close);
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
