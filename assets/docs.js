// Документация: поиск по разделам (docs/search.json), текущий раздел в оглавлении, копирование кода.
(function () {
  var q = document.getElementById('q'), box = document.getElementById('results');
  var idx = null, sel = -1;
  function load() {
    if (idx) return Promise.resolve(idx);
    return fetch('/docs/search.json').then(function (r) { return r.json(); }).then(function (j) { idx = j; return j; });
  }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function mark(text, words) {
    var out = esc(text);
    words.forEach(function (w) { if (w) out = out.replace(new RegExp('(' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig'), '<mark>$1</mark>'); });
    return out;
  }
  function snippet(x, w) {
    var i = x.toLowerCase().indexOf(w);
    var s = Math.max(0, i - 50);
    return (s > 0 ? '…' : '') + x.slice(s, s + 150) + (x.length > s + 150 ? '…' : '');
  }
  function search() {
    var v = q.value.trim().toLowerCase();
    if (v.length < 2) { box.hidden = true; return; }
    load().then(function (items) {
      var words = v.split(/\s+/);
      var hits = items.map(function (it) {
        var hay = (it.t + ' ' + it.h + ' ' + it.x).toLowerCase(), score = 0;
        for (var i = 0; i < words.length; i++) {
          if (hay.indexOf(words[i]) < 0) return null;
          if (it.h.toLowerCase().indexOf(words[i]) >= 0) score += 5;
          if (it.t.toLowerCase().indexOf(words[i]) >= 0) score += 2;
        }
        return { it: it, s: score };
      }).filter(Boolean).sort(function (a, b) { return b.s - a.s; }).slice(0, 12);
      sel = -1;
      box.innerHTML = hits.length ? hits.map(function (h) {
        var it = h.it;
        return '<a href="/docs/' + it.p + '/' + (it.a ? '#' + it.a : '') + '"><b>' + mark(it.h, words) +
          (it.h !== it.t ? ' <span>· ' + esc(it.t) + '</span>' : '') +
          '</b><small>' + mark(snippet(it.x, words[0]), words) + '</small></a>';
      }).join('') : '<div class="none">Ничего не нашлось</div>';
      box.hidden = false;
    });
  }
  if (q) {
    q.addEventListener('input', search);
    q.addEventListener('focus', function () { load(); if (q.value.trim().length > 1) search(); });
    q.addEventListener('keydown', function (e) {
      var links = box.querySelectorAll('a');
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        sel = Math.max(0, Math.min(links.length - 1, sel + (e.key === 'ArrowDown' ? 1 : -1)));
        links.forEach(function (a, i) { a.classList.toggle('sel', i === sel); });
      } else if (e.key === 'Enter' && links[sel >= 0 ? sel : 0]) {
        location.href = links[sel >= 0 ? sel : 0].href;
      } else if (e.key === 'Escape') { box.hidden = true; q.blur(); }
    });
    document.addEventListener('click', function (e) { if (!e.target.closest('.search')) box.hidden = true; });
    document.addEventListener('keydown', function (e) {
      if (e.key === '/' && document.activeElement !== q) { e.preventDefault(); q.focus(); }
    });
  }
  // Текущий раздел страницы в оглавлении справа.
  var toc = Array.prototype.slice.call(document.querySelectorAll('.toc a'));
  if (toc.length && 'IntersectionObserver' in window) {
    var map = {};
    toc.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
    var obs = new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        if (en.isIntersecting) { toc.forEach(function (a) { a.classList.remove('on'); }); var a = map[en.target.id]; if (a) a.classList.add('on'); }
      });
    }, { rootMargin: '-80px 0px -70% 0px' });
    Object.keys(map).forEach(function (id) { var h = document.getElementById(id); if (h) obs.observe(h); });
  }
  // Кнопка «копировать» у блоков кода.
  document.querySelectorAll('.md pre').forEach(function (pre) {
    var b = document.createElement('button');
    b.className = 'copy'; b.textContent = 'копировать';
    b.onclick = function () {
      navigator.clipboard.writeText((pre.querySelector('code') || pre).innerText.trim()).then(function () {
        b.textContent = 'скопировано'; setTimeout(function () { b.textContent = 'копировать'; }, 1400);
      });
    };
    pre.appendChild(b);
  });
  document.querySelectorAll('.side a').forEach(function (a) { a.addEventListener('click', function () { document.body.classList.remove('nav-open'); }); });
})();
