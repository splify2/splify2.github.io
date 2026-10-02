# splify2.github.io

Сайт организации [splify2](https://github.com/splify2): главная страница (`index.html`, `assets/`) и
раздел документации `/docs`, собранный из markdown репозиториев проектов.

- `build.py` — сборка документации: список страниц (`NAV`), источники — `репозиторий:путь` или
  `site:content/…`, шаблон — `templates/doc.html`, индекс поиска — `docs/search.json`.
- `content/` — свои страницы: обзор, быстрый старт, как это работает.
- `tools/frame.html` — рамка для скриншотов панели (`assets/img/framed/`, рендер headless-браузером).
- `.github/workflows/pages.yml` — сборка и публикация: при пуше, раз в сутки и вручную.

Локально: `SRC=/путь/к/каталогу/с/репозиториями python3 build.py && python3 -m http.server`.
