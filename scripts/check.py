"""Check generated links, content coverage, and important schema failures."""
import copy
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from build import ROOT, OUT, validate


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.ids = set()
        self.h1 = 0
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids, f'重複 id: {a["id"]}'
            self.ids.add(a['id'])
        self.h1 += tag == 'h1'
        for field in ('href', 'src'):
            if field in a:
                self.refs.append(a[field])
        if tag == 'script' or (tag == 'link' and a.get('rel') == 'stylesheet'):
            self.scripts.append(a.get('src', a.get('href', '')))


pages = {}
for path in OUT.rglob('*.html'):
    p = Page()
    p.feed(path.read_text())
    assert p.h1 == 1, f'{path}: 必須只有一個 h1'
    assert all(not urlsplit(s).scheme and not s.startswith('//') for s in p.scripts), '不得載入外部執行資源'
    pages[path.resolve()] = p
assert pages, '請先執行 build.py'
for path, page in pages.items():
    for ref in page.refs:
        u = urlsplit(ref)
        if u.scheme or u.netloc:
            continue
        assert not u.path.startswith('/'), f'不支援子路徑部署: {ref}'
        target = (path.parent / unquote(u.path)).resolve() if u.path else path
        assert target.is_relative_to(OUT.resolve()), f'連結超出輸出目錄: {ref}'
        assert target.exists(), f'{path.name} 中連結不存在: {ref}'
        if u.fragment and target in pages:
            assert unquote(u.fragment) in pages[target].ids, f'錨點不存在: {ref}'
sources = sorted((ROOT / 'content/notes').glob('*.json'))
assert len(list((OUT / 'notes').glob('*.html'))) == len(sources), '文章數不一致'
index = (OUT / 'index.html').read_text()
for path in sources:
    assert f'notes/{path.stem}.html' in index, '首頁缺少新文章'
assert (OUT / 'AGENTS.md').read_bytes() == (ROOT / 'AGENTS.md').read_bytes(), '規則頁來源不一致'

# Invalid additions must fail before publishing, including path traversal.
sample = json.loads(sources[0].read_text())
for field, bad in [('slug', '../escape'), ('category', '未知分類'), ('date', '2026-02-30'), ('minutes', True), ('tags', ['重複', '重複']), ('sections', [])]:
    n = copy.deepcopy(sample)
    n[field] = bad
    try:
        validate(n, n['slug'])
    except (AssertionError, ValueError):
        pass
    else:
        raise AssertionError(f'驗證未攔截錯誤欄位: {field}')
print(f'PASS: {len(pages)} pages, all local links, source coverage, 6 invalid-content checks')
