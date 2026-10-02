// Главная: появление при прокрутке, витрина скриншотов, вкладки установки, копирование команд.
(function () {
  var reveal = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: .08 });
    reveal.forEach(function (el) { io.observe(el); });
  } else reveal.forEach(function (el) { el.classList.add('in'); });

  // Витрина: вкладки и смена раз в несколько секунд, пока человек сам не выбрал.
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.tabs button'));
  var img = document.getElementById('shot-img'), dark = document.getElementById('shot-dark'), cap = document.getElementById('shot-cap');
  var cur = 0, auto = true, timer = null;
  tabs.forEach(function (t) { var i = new Image(); i.src = '/assets/img/framed/' + t.dataset.shot + '-light.webp'; var j = new Image(); j.src = '/assets/img/framed/' + t.dataset.shot + '-dark.webp'; });
  function show(i) {
    cur = i;
    var t = tabs[i];
    tabs.forEach(function (b, k) { b.classList.toggle('on', k === i); b.setAttribute('aria-selected', k === i); });
    img.classList.add('fade');
    setTimeout(function () {
      img.src = '/assets/img/framed/' + t.dataset.shot + '-light.webp';
      dark.srcset = '/assets/img/framed/' + t.dataset.shot + '-dark.webp';
      img.alt = t.textContent;
      cap.textContent = t.dataset.cap;
      img.classList.remove('fade');
    }, 220);
  }
  tabs.forEach(function (t, i) { t.addEventListener('click', function () { auto = false; show(i); }); });
  var frame = document.querySelector('.framed');
  if (frame && 'IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        clearInterval(timer);
        if (e.isIntersecting) timer = setInterval(function () { if (auto) show((cur + 1) % tabs.length); }, 4500);
      });
    }, { threshold: .4 }).observe(frame);
  }

  // Вкладки установки.
  var it = document.querySelectorAll('.itabs button');
  it.forEach(function (b) {
    b.addEventListener('click', function () {
      it.forEach(function (x) { x.classList.toggle('on', x === b); });
      document.querySelectorAll('.ipane').forEach(function (p) { p.classList.toggle('on', p.id === b.dataset.i); });
    });
  });
  document.querySelectorAll('.cp').forEach(function (b) {
    b.addEventListener('click', function () {
      var txt = b.parentNode.querySelector('code').innerText;
      navigator.clipboard.writeText(txt).then(function () { b.textContent = 'Скопировано'; setTimeout(function () { b.textContent = 'Скопировать'; }, 1500); });
    });
  });
})();
