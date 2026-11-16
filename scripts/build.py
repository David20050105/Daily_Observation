"""Validate source content and build a dependency-free static site."""
import html
import json
import os
import re
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
CATEGORIES = ('散步', '影像', '書寫')
HEADINGS = ('觀察起點', '試試這個方法', '帶走一個問題')
REPO = os.environ.get('SITE_REPOSITORY', '').rstrip('/')
e = html.escape


def string(value, low, high):
    assert isinstance(value, str) and low <= len(value.strip()) <= high, f'文字長度須為 {low}–{high}'
    assert '請替換' not in value and '替換成' not in value, '請移除範本佔位文字'


def validate(n, filename):
    assert set(n) == {'slug', 'title', 'category', 'date', 'minutes', 'summary', 'tags', 'sections', 'exercise'}, '欄位不符範本'
    assert isinstance(n['slug'], str) and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', n['slug']), 'slug 格式錯誤'
    assert n['slug'] == filename, '檔名必須與 slug 相同'
    string(n['title'], 8, 32)
    string(n['summary'], 30, 100)
    assert n['category'] in CATEGORIES, '未知分類'
    assert isinstance(n['date'], str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', n['date']), '日期格式錯誤'
    date.fromisoformat(n['date'])
    assert type(n['minutes']) is int and 1 <= n['minutes'] <= 30, '時間須為 1–30 整數'
    assert isinstance(n['tags'], list) and 1 <= len(n['tags']) <= 3, '標籤數須為 1–3'
    for t in n['tags']:
        string(t, 1, 8)
    assert len(set(n['tags'])) == len(n['tags']), '標籤不得重複'
    assert isinstance(n['sections'], list) and len(n['sections']) == 3, '需要三節正文'
    for s, heading in zip(n['sections'], HEADINGS):
        assert set(s) == {'title', 'paragraphs'} and s['title'] == heading, '正文標題或欄位錯誤'
        assert isinstance(s['paragraphs'], list) and 1 <= len(s['paragraphs']) <= 3, '每節須為 1–3 段'
        for p in s['paragraphs']:
            string(p, 20, 300)
    x = n['exercise']
    assert set(x) == {'title', 'steps'}, '練習欄位錯誤'
    string(x['title'], 4, 30)
    assert isinstance(x['steps'], list) and len(x['steps']) == 3, '練習須有三步'
    for step in x['steps']:
        string(step, 10, 100)


def shell(title, body, prefix='', active='notes'):
    repo_link = f'<a class="repo-link" href="{e(REPO, quote=True)}">GitHub ↗</a>' if REPO else ''
    return f'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="日常觀察所：從散步、影像與書寫開始，練習看見生活的細節。"><title>{e(title)} · 日常觀察所</title>
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{prefix}assets/style.css"><script defer src="{prefix}assets/app.js"></script></head>
<body><a class="skip" href="#main">跳至主要內容</a><header class="site-header wrap"><a class="brand" href="{prefix}index.html"><span class="brand-mark" aria-hidden="true">日</span><span>日常觀察所</span></a>
<nav aria-label="主要導覽"><a {'aria-current="page"' if active == 'notes' else ''} href="{prefix}index.html#collection">觀察筆記</a><a {'aria-current="page"' if active == 'guide' else ''} href="{prefix}guide.html">共作規則 <span aria-hidden="true">↗</span></a>{repo_link}</nav></header>
{body}<footer class="wrap"><a class="footer-brand" href="{prefix}index.html">日常觀察所</a><div>觀察練習示範 · 2026</div></footer></body></html>'''


def build():
    notes = []
    for path in sorted((ROOT / 'content/notes').glob('*.json')):
        try:
            n = json.loads(path.read_text())
            validate(n, path.stem)
            notes.append(n)
        except (AssertionError, ValueError, TypeError, KeyError) as error:
            raise SystemExit(f'{path.name}: {error}') from error
    assert notes, '至少需要一篇筆記'
    notes.sort(key=lambda n: n['slug'])
    notes.sort(key=lambda n: n['date'], reverse=True)
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / 'notes').mkdir(parents=True)
    shutil.copytree(ROOT / 'assets', OUT / 'assets')
    shutil.copy(ROOT / 'AGENTS.md', OUT / 'AGENTS.md')
    cards = []
    for i, n in enumerate(notes, 1):
        category = CATEGORIES.index(n['category'])
        search = e(' '.join([n['title'], n['summary'], *n['tags']]), quote=True)
        cards.append(f'''<article class="note-card" data-category="{e(n['category'])}" data-search="{search}"><a class="card-image tone-{category}" href="notes/{n['slug']}.html" aria-label="閱讀：{e(n['title'])}"><img src="assets/study-{category}.svg" alt="" loading="lazy"><span class="image-arrow" aria-hidden="true">↗</span></a><div class="card-meta"><span>{e(n['category'])}</span><span>{n['minutes']} 分鐘練習</span></div><h3><a href="notes/{n['slug']}.html">{e(n['title'])}</a></h3><p>{e(n['summary'])}</p><div class="card-bottom"><span>{' · '.join(e(t) for t in n['tags'])}</span><time datetime="{n['date']}">{n['date'].replace('-', '.')}</time></div></article>''')
        paragraphs = ''.join(f'<section class="prose-section"><span class="section-number">0{j}</span><h2>{e(s["title"])}</h2>{"".join(f"<p>{e(p)}</p>" for p in s["paragraphs"])}</section>' for j, s in enumerate(n['sections'], 1))
        steps = ''.join(f'<li>{e(s)}</li>' for s in n['exercise']['steps'])
        body = f'''<main id="main" class="article wrap"><a class="back" href="../index.html#collection">← 回到觀察筆記</a><div class="eyebrow">{e(n['category'])}</div><h1>{e(n['title'])}</h1><p class="article-lead">{e(n['summary'])}</p><div class="article-meta"><time datetime="{n['date']}">{n['date']}</time><span>{n['minutes']} 分鐘練習</span></div><div class="article-banner tone-{category}"><img src="../assets/study-{category}.svg" alt="{['街道與視線的抽象線條插圖', '光影與取景的抽象構圖插圖', '文字片段與記錄的抽象紙張插圖'][category]}"></div><div class="article-body">{paragraphs}<aside class="exercise"><h2>{e(n['exercise']['title'])}</h2><ol>{steps}</ol></aside><a class="button" href="../index.html#collection">探索其他筆記 <span>↗</span></a></div></main>'''
        (OUT / 'notes' / f'{n["slug"]}.html').write_text(shell(n['title'], body, '../', ''))
    filters = ''.join(f'<button type="button" data-filter="{c}" aria-pressed="false" aria-controls="book-entries"><span class="toc-number">{j:02d}</span><span>{c}</span><span class="toc-dots" aria-hidden="true"></span><span class="toc-count">{sum(n["category"] == c for n in notes):02d}</span></button>' for j, c in enumerate(CATEGORIES, 1))
    body = f'''<main id="main" class="notebook"><section class="hero book-cover wrap"><div class="hero-copy"><h1>日子很平凡，<br>值得<span class="accent">仔細看。</span><svg class="title-spark" viewBox="0 0 60 60" aria-hidden="true"><path d="M30 2v56M2 30h56M10 10l40 40M10 50l40-40"/></svg></h1><p>從散步、影像與書寫，練習觀察日常。</p><a class="button" data-open-book href="#collection">翻開觀察筆記 <span aria-hidden="true">↗</span></a></div><figure class="hero-art"><img src="assets/observatory.svg" alt="原創觀察手帳插圖：巷弄、樹木、窗戶與橘色標記組成的日常地圖"></figure></section>
<section class="collection wrap" id="collection" aria-label="觀察筆記書本"><div class="book-toolbar"><span>日常觀察所</span><button class="close-book" type="button" hidden>← 闔上筆記</button></div><div class="book-spread"><aside class="collection-tools book-toc" hidden><div class="toc-heading"><span class="book-ornament" aria-hidden="true">✳</span><h2>目錄</h2></div><nav class="filters" aria-label="筆記分類目錄"><button class="selected" type="button" data-filter="all" aria-pressed="true" aria-controls="book-entries"><span class="toc-number">○</span><span>全部筆記</span><span class="toc-dots" aria-hidden="true"></span><span class="toc-count">{len(notes):02d}</span></button>{filters}</nav><div class="toc-illustration" aria-hidden="true"><img src="assets/observatory.svg" alt=""></div><div class="book-folio"><span>目錄</span><span>i</span></div></aside><div class="book-page"><div class="section-heading"><h2 id="collection-title" tabindex="-1"><span id="chapter-title">全部筆記</span><span class="chapter-count">（{len(notes):02d}）</span></h2><label class="search" hidden><span aria-hidden="true">⌕</span><span class="sr-only">搜尋標題、摘要或標籤</span><input id="search" type="search" placeholder="搜尋筆記" autocomplete="off"></label></div><p id="result-status" class="result-status" role="status" aria-live="polite"></p><div class="book-page-content" id="book-entries"><div class="notes-grid">{''.join(cards)}</div><p id="empty" class="empty" hidden>找不到筆記，請更換關鍵字或分類。</p></div><div class="book-folio"><span id="folio-title">全部筆記</span><span id="folio-number">01</span></div></div></div></section>
</main>'''
    (OUT / 'index.html').write_text(shell('把平凡的日子，看仔細一點', body))
    rules = e((ROOT / 'AGENTS.md').read_text())
    source_link = f'<a class="button" href="{e(REPO, quote=True)}/blob/main/AGENTS.md">GitHub 原始文件 ↗</a>' if REPO else ''
    body = f'''<main id="main" class="guide wrap"><h1>共作規則</h1><p class="article-lead">新增內容與修改網站，請依照以下 AGENTS.md。</p><div class="guide-actions">{source_link}<a href="AGENTS.md" download>下載 AGENTS.md ↓</a></div><pre class="rules">{rules}</pre></main>'''
    (OUT / 'guide.html').write_text(shell('共作規則', body, active='guide'))
    (OUT / '.nojekyll').touch()
    print(f'Built {len(notes)} notes + index + guide → {OUT}')


if __name__ == '__main__':
    build()
