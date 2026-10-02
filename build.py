#!/usr/bin/env python3
"""Сборка раздела документации splify2.github.io/docs из markdown в репозиториях.

Источники — каталоги репозиториев (SRC/<репозиторий>, по умолчанию ../<репозиторий> рядом с этим
деревом; в GitHub Actions их выкладывает checkout). Свои страницы сайта (обзор, быстрый старт) лежат
здесь, в content/. Результат — docs/<страница>/index.html и docs/search.json.

    python3 build.py            # SRC — родительский каталог
    SRC=/путь python3 build.py
"""
import html
import json
import os
import posixpath
import re
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
    if missing:
        print("нет источников:", ", ".join(missing), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
