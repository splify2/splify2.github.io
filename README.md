# splify2.github.io

Сайт организации [splify2](https://github.com/splify2): главная страница (`index.html`, `assets/`),
раздел документации `/docs`, собранный из markdown репозиториев проектов, и страница выпусков
`/releases` из [splify2/releases](https://github.com/splify2/releases).

- `build.py` — сборка документации: список страниц (`NAV`), источники — `репозиторий:путь` или
  `site:content/…`, шаблон — `templates/doc.html`, индекс поиска — `docs/search.json`.
- `build.py` — и выпуски: `releases/index.html` из `version.json` и `changelogs/` клона
  splify2/releases (шаблон — `templates/releases.html`) и `releases/version.json` — его копия байт в
  байт: один из адресов, с которых version.json читают установщик и роутеры.
- `content/` — свои страницы: обзор, быстрый старт, как это работает.
- `tools/frame.html` — рамка для скриншотов панели (`assets/img/framed/`, рендер headless-браузером).
- `.github/workflows/pages.yml` — сборка и публикация: при пуше, раз в сутки, при новом выпуске
  (раз в час сверяет version.json сайта и splify2/releases; сразу — по `repository_dispatch` с типом
  `releases`) и вручную.

Локально: `SRC=/путь/к/каталогу/с/репозиториями python3 build.py && python3 -m http.server`.
