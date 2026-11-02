(function () {
  var STEP = 20;
  var offset = 0;

  function clamp(offset, max) {
    return Math.min(Math.max(offset, 0), max);
  }

  function maxOffset() {
    return Math.max(0, cow.parentElement.clientWidth - cow.offsetWidth);
  }

  function apply(newOffset) {
    offset = newOffset;
    cow.style.left = offset + 'px';
    cow.dataset.offset = String(offset);
  }

  var cow = document.getElementById('first-cow');
  var btnLeft = document.getElementById('move-left');
  var btnRight = document.getElementById('move-right');

  if (!cow || !btnLeft || !btnRight) {
    return;
  }

  btnRight.addEventListener('click', function () {
    apply(clamp(offset + STEP, maxOffset()));
  });

  btnLeft.addEventListener('click', function () {
    apply(clamp(offset - STEP, maxOffset()));
  });
})();
