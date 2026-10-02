# splify2.github.io

Сайт организации [splify2](https://github.com/splify2): главная страница (`index.html`, `assets/`),
раздел документации `/docs`, собранный из markdown репозиториев проектов, и страница выпусков
`/releases` из [splify2/releases](https://github.com/splify2/releases).

- `build.py` — сборка документации: список страниц (`NAV`), источники — `репозиторий:путь` или
  `site:content/…`, шаблон — `templates/doc.html`, индекс поиска — `docs/search.json`.
- `build.py` — и выпуски: `releases/index.html` из `version.json` и `changelogs/` клона
  splify2/releases (шаблон — `templates/releases.html`) и `releases/version.json` — его копия байт в
  байт: один из адресов, с которых version.json читают установщик и роутеры.
- `build.py` — и дизайн-система: Andromeda, та же, что у пульта splify2, берётся из клона splify2
  (`SRC/splify2/ui/andromeda`, другой путь — переменной `ANDROMEDA`) и кладётся в `assets/andromeda/`:
  `styles.css`, `tokens/*.css`, `assets/fonts/` (Onest и JetBrains Mono с лицензиями OFL). Без неё
  сборка падает. Стили сайта (`assets/*.css`) — на её токенах `--an-*`; тёмная тема — `data-theme="dark"`
  и класс `dark` на `<html>` (`assets/theme.js`: выбор человека или тема системы).
  Стекло — как в пульте: подложка `.an-backdrop` на всю длину страницы, шапка, подвал, разделы и
  оглавление документации — `.an-glass-chrome`, карточки, статья и выпуски — `.an-glass`.
- `content/` — свои страницы: обзор, быстрый старт, как это работает.
- `tools/frame.html` — рамка для скриншотов панели (`assets/img/framed/`, рендер headless-браузером).
- `.github/workflows/pages.yml` — сборка и публикация: при пуше, раз в сутки, при новом выпуске
  (раз в час сверяет version.json сайта и splify2/releases; сразу — по `repository_dispatch` с типом
  `releases`) и вручную.

Локально: `SRC=/путь/к/каталогу/с/репозиториями python3 build.py && python3 -m http.server`.
