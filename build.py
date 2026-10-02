#!/usr/bin/env python3
"""Сборка раздела документации splify2.github.io/docs из markdown в репозиториях и страницы выпусков.

Источники — каталоги репозиториев (SRC/<репозиторий>, по умолчанию ../<репозиторий> рядом с этим
деревом; в GitHub Actions их выкладывает checkout). Свои страницы сайта (обзор, быстрый старт) лежат
здесь, в content/. Результат — docs/<страница>/index.html и docs/search.json.

Выпуски — из клона splify2/releases (SRC/releases): releases/index.html и releases/version.json —
копия байт в байт, третий адрес чтения version.json для установщика и роутеров.

    python3 build.py            # SRC — родительский каталог
    SRC=/путь python3 build.py
"""
import html
import json
import os
import posixpath
import re
import shutil
import sys

import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("SRC", os.path.dirname(ROOT))
ORG = "splify2"

# Раздел, страницы: (адрес, заголовок в навигации, источник). Источник — "repo:путь" или
# "site:путь" (content/ этого репозитория).
NAV = [
    ("Начало", [
        ("overview", "Обзор", "site:content/overview.md"),
        ("quickstart", "Быстрый старт", "site:content/quickstart.md"),
        ("how-it-works", "Как это работает", "site:content/how-it-works.md"),
    ]),
    ("splify2", [
        ("splify2", "Панель splify2", "splify2:docs/guide.md"),
        ("splify2/rpcd-api", "API rpcd", "splify2:docs/rpcd-api.md"),
        ("splify2/telemetry", "Отчёт о работе", "splify2:docs/TELEMETRY.md"),
        ("lists", "Каталог списков", "splify2-lists:README.md"),
    ]),
    ("Ядро steer", [
        ("steer", "Ядро steer", "steer:docs/guide.md"),
        ("steer/spec-v2", "Спека v2", "steer:docs/spec-v2.md"),
        ("steer/ctl", "Управление и события", "steer:docs/ctl.md"),
        ("steer/architecture", "Устройство ядра", "steer:docs/architecture.md"),
        ("steer/contract-v1", "Спека v1 (прежняя)", "steer:docs/contract-v1.md"),
        ("steer/server", "Сервер и хаб", "steer:server/README.md"),
    ]),
    ("Протоколы", [
        ("protocols/vless", "VLESS / Reality", "steer:docs/vless.md"),
        ("protocols/hysteria2", "hysteria2", "steer:docs/hysteria2.md"),
        ("protocols/proxy", "trojan, shadowsocks, socks, http, vmess", "steer:docs/proxy.md"),
        ("protocols/xsteer", "xsteer в ядре", "steer:docs/xsteer.md"),
    ]),
    ("steer-box-connector", [
        ("connector", "Коннектор для podkop и forkop", "steer-box-connector:docs/guide.md"),
    ]),
    ("xsteer", [
        ("xsteer", "xsteer", "xsteer:README.md"),
        ("xsteer/deploy", "Развёртывание хаба", "xsteer:docs/deploy.md"),
        ("xsteer/detect", "Стойкость к обнаружению", "xsteer:docs/detect.md"),
        ("xsteer/windows", "Клиент для Windows", "xsteer:docs/windows.md"),
    ]),
]

PAGES = [(sec, slug, title, src) for sec, items in NAV for slug, title, src in items]
BY_SRC = {src: slug for _, slug, _, src in PAGES}


def src_path(src):
    repo, path = src.split(":", 1)
    base = ROOT if repo == "site" else os.path.join(SRC, repo)
    return repo, path, os.path.join(base, path)


def slugify(text, used):
    s = re.sub(r"<[^>]+>", "", text).strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.U)
    s = re.sub(r"[\s]+", "-", s) or "section"
    base, n = s, 2
    while s in used:
        s = f"{base}-{n}"
        n += 1
    used.add(s)
    return s


def rewrite_links(md_text, repo, path):
    """Относительные ссылки: на документ из NAV — на страницу сайта; на прочий файл — в GitHub."""
    folder = posixpath.dirname(path)

    def target(link):
        if re.match(r"^[a-z]+:|^#|^/", link):
            return None
        file, _, frag = link.partition("#")
        if not file:
            return None
        full = posixpath.normpath(posixpath.join(folder, file))
        key = f"{repo}:{full}"
        if key in BY_SRC:
            return f"/docs/{BY_SRC[key]}/" + (f"#{frag}" if frag else "")
        if repo == "site":
            return None
        kind = "raw" if re.search(r"\.(png|svg|jpe?g|gif|webp)$", full, re.I) else "blob"
        if kind == "raw":
            return f"https://raw.githubusercontent.com/{ORG}/{repo}/main/{full}"
        return f"https://github.com/{ORG}/{repo}/{kind}/main/{full}" + (f"#{frag}" if frag else "")

    def md_link(m):
        t = target(m.group(2))
        return f"{m.group(1)}({t})" if t else m.group(0)

    md_text = re.sub(r"(!?\[[^\]]*\])\(([^)\s]+)\)", md_link, md_text)
    md_text = re.sub(r'(src|href)="([^"]+)"',
                     lambda m: f'{m.group(1)}="{target(m.group(2)) or m.group(2)}"', md_text)
    return md_text


def indent4(md_text):
    """Вложенность в исходниках — по два пробела, python-markdown ждёт четыре: ведущие пробелы
    строк вне блоков кода удваиваются."""
    out, fence = [], False
    for line in md_text.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
            out.append(line)
            continue
        if not fence:
            m = re.match(r"^( +)(\S.*)$", line)
            if m:
                line = " " * (len(m.group(1)) * 2) + m.group(2)
        out.append(line)
    return "\n".join(out)


def render(md_text):
    md_text = indent4(md_text)
    conv = markdown.Markdown(extensions=["tables", "fenced_code", "codehilite", "sane_lists", "attr_list"],
                             extension_configs={"codehilite": {"guess_lang": False, "css_class": "hl"}})
    body = conv.convert(md_text)
    used, toc = set(), []

    def head(m):
        level, inner = int(m.group(1)), m.group(2)
        hid = slugify(inner, used)
        if level in (2, 3):
            toc.append((level, re.sub(r"<[^>]+>", "", inner), hid))
        return f'<h{level} id="{hid}">{inner}<a class="anchor" href="#{hid}" aria-label="Ссылка">#</a></h{level}>'

    body = re.sub(r"<h([1-4])>(.*?)</h\1>", head, body, flags=re.S)
    body = re.sub(r"<table>", '<div class="table"><table>', body).replace("</table>", "</table></div>")
    return body, toc


def plain(htm):
    t = re.sub(r"<pre.*?</pre>", " ", htm, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def nav_html(current):
    out = []
    for sec, items in NAV:
        out.append(f'<div class="nav-sec"><div class="nav-title">{html.escape(sec)}</div>')
        for slug, title, _ in items:
            cls = ' class="on"' if slug == current else ""
            out.append(f'<a{cls} href="/docs/{slug}/">{html.escape(title)}</a>')
        out.append("</div>")
    return "\n".join(out)


# ---- Выпуски: /releases/ из version.json клона splify2/releases ----

RELEASES_ALL = f"https://github.com/{ORG}/releases/releases"
# Порядок продуктов на странице и раздел документации каждого; прочие продукты — следом, по имени.
REL_ORDER = ["steer", "splify2", "steer-box-connector", "xsteer"]
REL_DOCS = {"steer": "steer", "splify2": "splify2", "steer-box-connector": "connector", "xsteer": "xsteer"}
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября",
          "октября", "ноября", "декабря"]
# Пакет роутера: <пакет>-<версия>-<сборка>_<архитектура>.apk|ipk; all и noarch — для любой.
PKG_RE = re.compile(r"^(?P<pv>.+?)-(?P<rel>r?\d+)_(?P<arch>[A-Za-z0-9_-]+)\.(?P<fmt>apk|ipk)$")
NOARCH = {"all", "noarch"}
OS_LABEL = {"linux": "Linux", "windows": "Windows", "android": "Android", "darwin": "macOS", "macos": "macOS",
            "freebsd": "FreeBSD"}
CPU_LABEL = {"amd64": "x86-64", "x86_64": "x86-64", "arm64": "ARM64", "aarch64": "ARM64", "armv7": "ARMv7",
             "arm": "ARM", "386": "x86", "i386": "x86", "mips": "MIPS", "mipsel": "MIPSel", "riscv64": "RISC-V 64"}


def human_date(d):
    try:
        y, m, day = (int(x) for x in str(d)[:10].split("-"))
        return f"{day} {MONTHS[m - 1]} {y}"
    except (ValueError, IndexError):
        return html.escape(str(d))


def human_size(n):
    if not isinstance(n, int) or n <= 0:
        return ""
    for unit, k in (("ГБ", 1 << 30), ("МБ", 1 << 20), ("КБ", 1 << 10)):
        if n >= k:
            v = n / k
            return (f"{v:.1f}".replace(".", ",") if v < 10 else f"{v:.0f}") + " " + unit
    return f"{n} Б"


def platform_of(name):
    """Платформа архива или приложения по токенам имени — «Linux · x86-64», «Android» — или None."""
    stem = re.sub(r"\.(tar\.gz|tgz|tar\.xz|zip|apk|exe|msi|dmg|deb|rpm)$", "", name)
    toks = re.split(r"[-_.]", stem.lower())
    os_ = next((t for t in toks if t in OS_LABEL), None)
    cpu = None
    for i, t in enumerate(toks):
        if t == "x86" and i + 1 < len(toks) and toks[i + 1] == "64":
            cpu = "x86_64"
        elif t in CPU_LABEL:
            cpu = t
    if not os_ and not cpu:
        return None
    label = " · ".join(x for x in (OS_LABEL.get(os_), CPU_LABEL.get(cpu)) if x)
    return label


def group_assets(assets):
    """Файлы версии по-человечески: пакеты роутера — по архитектуре и формату, архивы и приложения —
    по платформе, остальное — списком."""
    pkgs, plats, other = {}, {}, []
    for a in assets:
        name = a.get("name", "")
        m = PKG_RE.match(name)
        if m:
            pkg = re.match(r"^(.+?)-\d", m.group("pv"))
            pkg = pkg.group(1) if pkg else m.group("pv")
            arch = "" if m.group("arch") in NOARCH else m.group("arch")
            pkgs.setdefault(arch, {}).setdefault(m.group("fmt"), []).append((pkg, a))
            continue
        plat = platform_of(name)
        if plat:
            plats.setdefault(plat, []).append(a)
        else:
            other.append(a)
    return pkgs, plats, other


def chip(a, text=None):
    url = (a.get("urls") or [""])[0]
    size = human_size(a.get("size"))
    title = html.escape(a.get("name", "")) + (f" · {size}" if size else "")
    return (f'<a class="file" href="{html.escape(url)}" title="{title}">{html.escape(text or a.get("name", ""))}'
            + (f"<small>{size}</small>" if size else "") + "</a>")


def files_html(assets):
    pkgs, plats, other = group_assets(assets)
    out = []
    if pkgs:
        fmts = [f for f in ("apk", "ipk") if any(f in v for v in pkgs.values())]
        out.append('<div class="fgroup"><h4>Пакеты для роутера</h4>'
                   '<p class="hint">Архитектура — как в выводе <code>apk --print-arch</code> или '
                   '<code>opkg print-architecture</code> на роутере. Есть команда <code>apk</code> — '
                   'бери .apk, иначе .ipk.</p>' if len(fmts) > 1 or len(pkgs) > 1 else
                   '<div class="fgroup"><h4>Пакеты для роутера</h4>')
        rows = []
        for arch in sorted(pkgs, key=lambda x: (x != "", x)):
            cells = "".join(f'<td data-label=".{f}">' + "".join(chip(a, pkg) for pkg, a in pkgs[arch].get(f, []))
                            + "</td>" for f in fmts)
            label = f"<code>{html.escape(arch)}</code>" if arch else "Для любой архитектуры"
            rows.append(f"<tr><th>{label}</th>{cells}</tr>")
        head = "".join(f"<th>.{f}</th>" for f in fmts)
        out.append(f'<div class="table"><table class="files"><thead><tr><th>Архитектура</th>{head}</tr></thead>'
                   f'<tbody>{"".join(rows)}</tbody></table></div></div>')
    if plats:
        title = "Для сервера" if pkgs else "По платформам"
        rows = "".join(f'<tr><th>{html.escape(p)}</th><td>{"".join(chip(a) for a in plats[p])}</td></tr>'
                       for p in sorted(plats))
        out.append(f'<div class="fgroup"><h4>{title}</h4><div class="table"><table class="files">'
                   f"<tbody>{rows}</tbody></table></div></div>")
    if other:
        title = "Другие файлы" if pkgs or plats else "Файлы"
        out.append(f'<div class="fgroup"><h4>{title}</h4><div class="chips">'
                   + "".join(chip(a) for a in other) + "</div></div>")
    return "".join(out) or '<p class="hint">Файлов нет.</p>'


def changelog_html(rel_root, product, repo, v, prefix):
    fs = os.path.join(rel_root, v.get("changelog") or f"changelogs/{product}/{v.get('version')}.md")
    if not os.path.isfile(fs):
        return ""
    text = open(fs, encoding="utf-8").read().strip()
    if not text:
        return ""
    body, _ = render(rewrite_links(text, repo, "CHANGELOG.md"))
    # Заголовки списка изменений — ниже заголовков страницы, якоря — свои у каждой версии.
    body = re.sub(r"<(/?)h([1-6])([ >])", lambda m: f"<{m.group(1)}h{min(6, int(m.group(2)) + 3)}{m.group(3)}", body)
    body = re.sub(r'(id="|href="#)', lambda m: m.group(1) + prefix, body)
    return f'<div class="md changelog">{body}</div>'


def version_html(rel_root, product, repo, v, current):
    ver = str(v.get("version", ""))
    vid = f"{product}-{ver}"
    pre = v.get("channel") == "prerelease"
    kind = "Предварительная" if pre else "Стабильная"
    tag = v.get("tag") or f"{product}-v{ver}"
    links = f'<a href="{RELEASES_ALL}/tag/{html.escape(tag)}">Выпуск на GitHub</a>'
    cl = changelog_html(rel_root, product, repo, v, re.sub(r"[^\w-]", "-", vid) + "-")
    inner = (files_html(v.get("assets") or [])
             + (f'<h4 class="cl-title">Что нового в {html.escape(ver)}</h4>{cl}' if cl else "")
             + f'<div class="vlinks">{links}</div>')
    summary = (f'<span class="ver{" pre" if pre else ""}">{html.escape(ver)}</span>'
               f'<span class="vmeta">{kind} · {human_date(v.get("date"))}</span>')
    if current:
        return f'<div class="vcur" id="{html.escape(vid)}"><div class="vhead">{summary}</div>{inner}</div>'
    return f'<details class="vold" id="{html.escape(vid)}"><summary>{summary}</summary>{inner}</details>'


def product_html(rel_root, name, p):
    repo = (p.get("repo") or f"{ORG}/{name}").split("/")[-1]
    vs = p.get("versions") or []
    by = {str(v.get("version")): v for v in vs}
    stable = by.get(str(p.get("stable"))) if p.get("stable") else None
    pre = by.get(str(p.get("prerelease"))) if p.get("prerelease") else None
    cur = stable or pre
    badges = []
    for v in (stable, pre):
        if v:
            k = "предварительная" if v is pre else "стабильная"
            badges.append(f'<a class="ver{" pre" if v is pre else ""}" href="#{html.escape(name)}-{html.escape(str(v["version"]))}">'
                          f'{html.escape(str(v["version"]))}</a><span class="vmeta">{k} · {human_date(v.get("date"))}</span>')
    links = []
    if name in REL_DOCS:
        links.append(f'<a href="/docs/{REL_DOCS[name]}/">Документация</a>')
    links.append(f'<a href="https://github.com/{html.escape(p.get("repo") or f"{ORG}/{name}")}">GitHub</a>')
    out = [f'<section class="product" id="{html.escape(name)}"><div class="phead">'
           f'<h2>{html.escape(p.get("title") or name)}</h2><div class="plinks">{"".join(links)}</div></div>']
    # Строка версий — когда есть и стабильная, и предварительная (иначе она повторяет заголовок версии ниже).
    if len(badges) > 1:
        out.append(f'<div class="badges">{"".join(f"<span>{b}</span>" for b in badges)}</div>')
    elif not cur:
        out.append('<p class="hint">Выпусков пока нет.</p>')
    if pre and stable:
        out.append(version_html(rel_root, name, repo, pre, False).replace('class="vold"', 'class="vold vpre"', 1))
    if cur:
        out.append(version_html(rel_root, name, repo, cur, True))
    older = [v for v in vs if v is not cur and v is not pre]
    if older:
        out.append('<h3 class="older">Прежние версии</h3>')
        out.extend(version_html(rel_root, name, repo, v, False) for v in older)
    out.append("</section>")
    return "".join(out)


def build_releases():
    """releases/index.html и копия version.json. Нет клона — False (сборка падает, как без документации)."""
    rel_root = os.path.join(SRC, "releases")
    vj = os.path.join(rel_root, "version.json")
    if not os.path.isfile(vj):
        return False
    with open(vj, encoding="utf-8") as f:
        doc = json.load(f)
    prods = doc.get("products") or {}
    order = [n for n in REL_ORDER if n in prods] + sorted(n for n in prods if n not in REL_ORDER)
    side = ['<div class="nav-sec"><div class="nav-title">Выпуски</div>']
    side += [f'<a href="#{html.escape(n)}">{html.escape(prods[n].get("title") or n)}</a>' for n in order]
    side.append(f'</div><div class="nav-sec"><div class="nav-title">Ещё</div><a href="{RELEASES_ALL}">Все выпуски на GitHub</a>'
                '<a href="/releases/version.json">version.json</a></div>')
    body = "".join(product_html(rel_root, n, prods[n]) for n in order)
    upd = f'<p class="updated">Обновлено {human_date(doc.get("updated"))}</p>' if doc.get("updated") else ""
    tpl = open(os.path.join(ROOT, "templates", "releases.html"), encoding="utf-8").read()
    page = (tpl.replace("{{nav}}", "".join(side)).replace("{{updated}}", upd)
            .replace("{{all}}", RELEASES_ALL).replace("{{body}}", body))
    out = os.path.join(ROOT, "releases")
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page)
    # Байт в байт: этот адрес читают установщик и роутер, содержимое обязано совпасть с остальными двумя.
    shutil.copyfile(vj, os.path.join(out, "version.json"))
    print(f"выпуски: продуктов {len(order)}, версий {sum(len(prods[n].get('versions') or []) for n in order)}")
    return True


def main():
    tpl = open(os.path.join(ROOT, "templates", "doc.html"), encoding="utf-8").read()
    index, missing = [], []
    for i, (sec, slug, title, src) in enumerate(PAGES):
        repo, path, fs = src_path(src)
        if not os.path.exists(fs):
            missing.append(src)
            continue
        text = open(fs, encoding="utf-8").read()
        # Шапка README в духе Xray-core (<div align="center"> с логотипом и значками) — для GitHub;
        # на сайте вместо неё заголовок и строка-описание из неё же.
        m = re.match(r'\s*<div align="center">(.*?)</div>\s*', text, re.S)
        if m:
            head = re.search(r"^#\s+(.+)$", m.group(1), re.M)
            sub = re.search(r"^\*\*(.+)\*\*\s*$", m.group(1), re.M)
            text = (f"# {head.group(1) if head else title}\n\n" + (f"{sub.group(1)}\n\n" if sub else "")
                    + text[m.end():])
        text = rewrite_links(text, repo, path)
        body, toc = render(text)
        toc_html = "".join(f'<a class="l{l}" href="#{h}">{html.escape(t)}</a>' for l, t, h in toc)
        prev = PAGES[i - 1] if i > 0 else None
        nxt = PAGES[i + 1] if i + 1 < len(PAGES) else None
        pn = ""
        if prev:
            pn += f'<a class="prev" href="/docs/{prev[1]}/"><span>Назад</span>{html.escape(prev[2])}</a>'
        if nxt:
            pn += f'<a class="next" href="/docs/{nxt[1]}/"><span>Дальше</span>{html.escape(nxt[2])}</a>'
        edit = ("" if repo == "site" else
                f'<a class="edit" href="https://github.com/{ORG}/{repo}/blob/main/{path}">Исходник на GitHub</a>')
        page = (tpl.replace("{{title}}", html.escape(title)).replace("{{section}}", html.escape(sec))
                .replace("{{nav}}", nav_html(slug)).replace("{{toc}}", toc_html)
                .replace("{{body}}", body).replace("{{prevnext}}", pn).replace("{{edit}}", edit))
        out = os.path.join(ROOT, "docs", slug, "index.html")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(page)
        sections = re.split(r'(?=<h[23] id=")', body)
        for part in sections:
            m = re.match(r'<h[23] id="([^"]+)">(.*?)<a class="anchor"', part, re.S)
            anchor, head = (m.group(1), re.sub(r"<[^>]+>", "", m.group(2))) if m else ("", title)
            text = plain(part)[:600]
            if text:
                index.append({"p": slug, "t": title, "h": head, "a": anchor, "x": text})
    with open(os.path.join(ROOT, "docs", "search.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    # /docs/ — сразу на обзор.
    open(os.path.join(ROOT, "docs", "index.html"), "w", encoding="utf-8").write(
        '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=/docs/overview/">'
        '<link rel="canonical" href="/docs/overview/"><title>Документация</title>')
    print(f"страниц: {len(PAGES) - len(missing)}, разделов в поиске: {len(index)}")
    if not build_releases():
        missing.append("releases:version.json")
    if missing:
        print("нет источников:", ", ".join(missing), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
