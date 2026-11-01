document.addEventListener('DOMContentLoaded', function () {
  var btn = document.getElementById('feed-btn');
  if (!btn) return;
  btn.addEventListener('click', function () {
    var firstCow = document.getElementById('first-cow');
    var thankYouCow = document.getElementById('thank-you-cow');
    if (!firstCow || !thankYouCow) return;
    // Replace the first cow's text content with the pre-rendered thank-you cowsay output,
    // keeping the green grass span intact.
    var grassSpan = firstCow.querySelector('span');
    firstCow.textContent = thankYouCow.textContent;
    if (grassSpan) {
      firstCow.appendChild(grassSpan);
    }
  });
});
