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
  // Кадр — в теме сайта (data-theme на <html>, assets/theme.js).
  var img = document.getElementById('shot-img'), cap = document.getElementById('shot-cap');
  var cur = 0, auto = true, timer = null;
  function src(shot) { return '/assets/img/framed/' + shot + (document.documentElement.classList.contains('dark') ? '-dark' : '-light') + '.webp'; }
  if (img && tabs.length) img.src = src(tabs[0].dataset.shot);
  document.addEventListener('themechange', function () { if (img && tabs[cur]) img.src = src(tabs[cur].dataset.shot); });
  tabs.forEach(function (t) { var i = new Image(); i.src = '/assets/img/framed/' + t.dataset.shot + '-light.webp'; var j = new Image(); j.src = '/assets/img/framed/' + t.dataset.shot + '-dark.webp'; });
  function show(i) {
    cur = i;
    var t = tabs[i];
    tabs.forEach(function (b, k) { b.classList.toggle('on', k === i); b.setAttribute('aria-selected', k === i); });
    img.classList.add('fade');
    setTimeout(function () {
      img.src = src(t.dataset.shot);
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
  // Счётчик живых роутеров и карта: сводка приёмника откликов (раз в 23 часа с каждого роутера),
  // а если она недоступна — снимок, сделанный при сборке сайта, не старше двух суток.
  var live = document.getElementById('live');
  var mapSec = document.getElementById('map');
  if (live && mapSec && window.fetch) {
    var API = 'https://dns.yo1nk.app/api/public';
    var get = function (url) {
      var ctl = window.AbortController ? new AbortController() : null;
      if (ctl) setTimeout(function () { ctl.abort(); }, 5000);
      return fetch(url, ctl ? { signal: ctl.signal } : {}).then(function (r) { if (!r.ok) throw r; return r.json(); });
    };
    var fresh = function (d) { return d && d.routers > 0 && Date.now() - Date.parse(d.updated) < 2 * 864e5 ? d : Promise.reject(); };
    var stats = get(API).then(fresh).catch(function () { return get('/assets/live.json').then(fresh); });
    stats.then(function (d) {
      var n = d.more_than || d.routers;
      var word = !d.more_than && n % 10 === 1 && n % 100 !== 11 ? 'роутере' : 'роутерах';
      live.textContent = 'Работает ' + (d.more_than ? 'более чем ' : '') + 'на ' + n + ' ' + word;
      mapSec.hidden = false;
      var cities = (d.cities || []).filter(function (c) { return c.cc === 'RU'; });
      if (!cities.length) return;
      return get('/assets/ru-map.json').then(function (m) { drawMap(m, cities); });
    }).catch(function () {});
  }

  // Названия городов: сводка отдаёт их по-английски (геоданные Vercel).
  var RU_CITY = {
    'Moscow': 'Москва', 'Saint Petersburg': 'Санкт-Петербург', 'St Petersburg': 'Санкт-Петербург', 'Novosibirsk': 'Новосибирск',
    'Yekaterinburg': 'Екатеринбург', 'Kazan': 'Казань', 'Nizhniy Novgorod': 'Нижний Новгород', 'Nizhny Novgorod': 'Нижний Новгород',
    'Chelyabinsk': 'Челябинск', 'Krasnoyarsk': 'Красноярск', 'Samara': 'Самара', 'Ufa': 'Уфа', 'Rostov-on-Don': 'Ростов-на-Дону',
    'Omsk': 'Омск', 'Krasnodar': 'Краснодар', 'Voronezh': 'Воронеж', 'Perm': 'Пермь', 'Volgograd': 'Волгоград', 'Saratov': 'Саратов',
    'Tyumen': 'Тюмень', 'Tolyatti': 'Тольятти', 'Togliatti': 'Тольятти', 'Izhevsk': 'Ижевск', 'Barnaul': 'Барнаул', 'Ulyanovsk': 'Ульяновск',
    'Irkutsk': 'Иркутск', 'Khabarovsk': 'Хабаровск', 'Makhachkala': 'Махачкала', 'Yaroslavl': 'Ярославль', 'Vladivostok': 'Владивосток',
    'Orenburg': 'Оренбург', 'Tomsk': 'Томск', 'Kemerovo': 'Кемерово', 'Novokuznetsk': 'Новокузнецк', 'Ryazan': 'Рязань',
    'Naberezhnye Chelny': 'Набережные Челны', 'Astrakhan': 'Астрахань', 'Penza': 'Пенза', 'Kirov': 'Киров', 'Lipetsk': 'Липецк',
    'Cheboksary': 'Чебоксары', 'Balashikha': 'Балашиха', 'Kaliningrad': 'Калининград', 'Tula': 'Тула', 'Kursk': 'Курск',
    'Stavropol': 'Ставрополь', 'Sochi': 'Сочи', 'Ulan-Ude': 'Улан-Удэ', 'Tver': 'Тверь', 'Magnitogorsk': 'Магнитогорск',
    'Ivanovo': 'Иваново', 'Bryansk': 'Брянск', 'Belgorod': 'Белгород', 'Surgut': 'Сургут', 'Vladimir': 'Владимир',
    'Chita': 'Чита', 'Arkhangelsk': 'Архангельск', 'Nizhny Tagil': 'Нижний Тагил', 'Simferopol': 'Симферополь', 'Kaluga': 'Калуга',
    'Smolensk': 'Смоленск', 'Volzhskiy': 'Волжский', 'Kurgan': 'Курган', 'Cherepovets': 'Череповец', 'Orel': 'Орёл', 'Oryol': 'Орёл',
    'Vologda': 'Вологда', 'Saransk': 'Саранск', 'Yakutsk': 'Якутск', 'Murmansk': 'Мурманск', 'Podolsk': 'Подольск',
    'Vladikavkaz': 'Владикавказ', 'Grozny': 'Грозный', 'Tambov': 'Тамбов', 'Sterlitamak': 'Стерлитамак', 'Petrozavodsk': 'Петрозаводск',
    'Kostroma': 'Кострома', 'Nizhnevartovsk': 'Нижневартовск', 'Novorossiysk': 'Новороссийск', 'Yoshkar-Ola': 'Йошкар-Ола',
    'Khimki': 'Химки', 'Taganrog': 'Таганрог', 'Syktyvkar': 'Сыктывкар', 'Nalchik': 'Нальчик', 'Sevastopol': 'Севастополь',
    'Mytishchi': 'Мытищи', 'Blagoveshchensk': 'Благовещенск', 'Pskov': 'Псков', 'Veliky Novgorod': 'Великий Новгород',
    'Yuzhno-Sakhalinsk': 'Южно-Сахалинск', 'Petropavlovsk-Kamchatsky': 'Петропавловск-Камчатский', 'Magadan': 'Магадан',
    'Norilsk': 'Норильск', 'Abakan': 'Абакан', 'Krasnogorsk': 'Красногорск', 'Korolev': 'Королёв', 'Zelenograd': 'Зеленоград',
    'Lyubertsy': 'Люберцы', 'Odintsovo': 'Одинцово', 'Dolgoprudnyy': 'Долгопрудный', 'Khanty-Mansiysk': 'Ханты-Мансийск'
  };

  // Та же коническая проекция Ламберта, что в tools/ru_map.py: числа приезжают в ru-map.json.
  function project(p, lat, lon) {
    if (lon < 0) lon += 360;
    var r = Math.PI / 180;
    var rho = p.F / Math.pow(Math.tan(Math.PI / 4 + lat * r / 2), p.n);
    var t = p.n * (lon - p.lon0) * r;
    return [rho * Math.sin(t) * p.k + p.tx, p.ty - (p.rho0 - rho * Math.cos(t)) * p.k];
  }

  function drawMap(m, cities) {
    var NS = 'http://www.w3.org/2000/svg';
    var svg = document.getElementById('ru-map'), tip = document.getElementById('map-tip');
    var card = svg.parentNode;
    svg.setAttribute('viewBox', '0 0 ' + m.w + ' ' + m.h);
    var land = document.createElementNS(NS, 'g'), path = document.createElementNS(NS, 'path');
    land.setAttribute('class', 'land'); path.setAttribute('d', m.d);
    land.appendChild(path); svg.appendChild(land);
    var R = [0, 4, 6, 8.5, 11.5, 15];                // радиус кружка по размеру 1–5, в пикселях экрана
    var dots = [];
    // Крупные снизу: мелкий город рядом с крупным остаётся видимым и доступным.
    cities.slice().sort(function (a, b) { return b.size - a.size; }).forEach(function (c) {
      var xy = project(m.proj, c.lat, c.lon);
      var name = RU_CITY[c.city] || c.city;
      var g = document.createElementNS(NS, 'g');
      g.setAttribute('class', 'city'); g.setAttribute('tabindex', '0'); g.setAttribute('role', 'img');
      g.setAttribute('aria-label', name);
      var halo = document.createElementNS(NS, 'circle'), dot = document.createElementNS(NS, 'circle');
      halo.setAttribute('class', 'halo'); dot.setAttribute('class', 'dot');
      [halo, dot].forEach(function (el) { el.setAttribute('cx', xy[0].toFixed(1)); el.setAttribute('cy', xy[1].toFixed(1)); g.appendChild(el); });
      var show = function () {
        var b = card.getBoundingClientRect(), d = dot.getBoundingClientRect();
        tip.textContent = name;
        tip.hidden = false;
        // Подсказка не вылезает за края карточки: у Калининграда и Камчатки центр у самого края.
        var half = tip.offsetWidth / 2, x = d.left + d.width / 2 - b.left;
        tip.style.left = Math.min(Math.max(x, half + 4), b.width - half - 4) + 'px';
        tip.style.top = (d.top - b.top) + 'px';
      };
      var hide = function () { tip.hidden = true; };
      g.addEventListener('mouseenter', show); g.addEventListener('focus', show);
      g.addEventListener('mouseleave', hide); g.addEventListener('blur', hide);
      g.addEventListener('click', function (e) { e.stopPropagation(); show(); });
      svg.appendChild(g);
      dots.push({ halo: halo, dot: dot, size: c.size });
    });
    document.addEventListener('click', function () { tip.hidden = true; });
    // Радиусы — в пикселях экрана, а не карты: на телефоне карта в два с половиной раза уже.
    var fit = function () {
      var px = svg.getBoundingClientRect().width || m.w;
      // На узкой карте кружки мельче, но не пропорционально: город должен оставаться видимым.
      var s = m.w / px * Math.min(1, Math.sqrt(px / 900));
      dots.forEach(function (o) {
        var r = R[o.size] || R[1];
        o.dot.setAttribute('r', (r * s).toFixed(2));
        o.halo.setAttribute('r', (r * 2.1 * s).toFixed(2));
      });
    };
    document.getElementById('map-card').hidden = false;
    fit();
    window.addEventListener('resize', fit);
  }
})();
