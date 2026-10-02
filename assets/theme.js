// Тема сайта — как у Andromeda: data-theme="dark" и класс dark на <html>. Выбор человека хранится
// в localStorage (splify2-theme); без него — тема системы, и смена темы системы применяется сразу.
// Подключается в <head> без defer: тема ставится до первой отрисовки, без вспышки светлой.
(function () {
  var KEY = 'splify2-theme', root = document.documentElement;
  var mq = window.matchMedia ? matchMedia('(prefers-color-scheme: dark)') : null;
  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function sync() {
    var dark = root.classList.contains('dark');
    document.querySelectorAll('.theme').forEach(function (b) { b.setAttribute('aria-pressed', dark ? 'true' : 'false'); });
  }
  function apply(dark) {
    if (dark) { root.setAttribute('data-theme', 'dark'); root.classList.add('dark'); }
    else { root.removeAttribute('data-theme'); root.classList.remove('dark'); }
    sync();
    document.dispatchEvent(new CustomEvent('themechange', { detail: { dark: dark } }));
  }
  var s = stored();
  apply(s ? s === 'dark' : !!(mq && mq.matches));
  if (mq) {
    var f = function (e) { if (!stored()) apply(e.matches); };
    if (mq.addEventListener) mq.addEventListener('change', f); else if (mq.addListener) mq.addListener(f);
  }
  document.addEventListener('DOMContentLoaded', sync);
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.theme');
    if (!b) return;
    var dark = !root.classList.contains('dark');
    try { localStorage.setItem(KEY, dark ? 'dark' : 'light'); } catch (err) { /* без хранилища — до перезагрузки */ }
    apply(dark);
  });
})();
