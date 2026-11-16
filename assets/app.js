/* Progressive enhancement: all content remains available without JavaScript. */
(() => {
  const tools = document.querySelector('.collection-tools');
  if (!tools) return;
  const notebook = document.querySelector('.notebook');
  const cover = notebook.querySelector('.hero');
  const collection = document.querySelector('#collection');
  const openButton = document.querySelector('[data-open-book]');
  const closeButton = document.querySelector('.close-book');
  const heading = document.querySelector('#collection-title');
  let turning = false;
  let opened = location.hash === '#collection';
  const setOpen = value => {
    opened = value;
    cover.hidden = value;
    collection.hidden = !value;
    openButton.setAttribute('aria-expanded', String(value));
  };
  openButton.setAttribute('role', 'button');
  openButton.setAttribute('aria-controls', 'collection');
  closeButton.hidden = false;
  setOpen(opened);

  const turnBook = async value => {
    if (turning || value === opened) return;
    turning = true;
    const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
    let sheet;
    if (!reduceMotion) {
      sheet = document.createElement('div');
      sheet.className = 'book-turn-sheet';
      sheet.setAttribute('aria-hidden', 'true');
      sheet.inert = true;
      // The turning cover uses the existing artwork and typography.
      const copy = cover.cloneNode(true);
      copy.hidden = false;
      sheet.append(copy);
      sheet.style.top = `${Math.max(0, document.querySelector('.site-header').getBoundingClientRect().bottom)}px`;
      document.body.append(sheet);
    }
    setOpen(value);
    history.replaceState(null, '', value ? '#collection' : location.pathname + location.search);
    // Switch the page in place; no scrolling animation is used.
    window.scrollTo({ top: 0, behavior: 'instant' });
    if (sheet) {
      document.body.classList.add('book-turning');
      const frames = [
        { transform: 'perspective(1800px) rotateY(0deg)', opacity: 1 },
        { transform: 'perspective(1800px) rotateY(-105deg)', opacity: 0.15 }
      ];
      const animation = sheet.animate(value ? frames : [...frames].reverse(), {
        duration: 950, easing: 'cubic-bezier(.35,.05,.2,1)', fill: 'forwards'
      });
      try { await animation.finished; } catch { /* Clean up if interrupted. */ }
      sheet.remove();
      document.body.classList.remove('book-turning');
    }
    turning = false;
    (value ? heading : openButton).focus({ preventScroll: true });
  };
  openButton.addEventListener('click', event => {
    event.preventDefault();
    turnBook(true);
  });
  openButton.addEventListener('keydown', event => {
    if (event.key === ' ') {
      event.preventDefault();
      turnBook(true);
    }
  });
  closeButton.addEventListener('click', () => turnBook(false));
  document.querySelector('.site-header a[href="index.html#collection"]').addEventListener('click', event => {
    if (!opened) {
      event.preventDefault();
      turnBook(true);
    }
  });
  // Hash links from article pages open the collection immediately.
  window.addEventListener('hashchange', () => {
    if (!turning) setOpen(location.hash === '#collection');
  });
  const cards = [...document.querySelectorAll('.note-card')];
  const buttons = [...document.querySelectorAll('[data-filter]')];
  const search = document.querySelector('#search');
  const status = document.querySelector('#result-status');
  let category = 'all';
  const update = () => {
    const query = search.value.trim().toLocaleLowerCase('zh-Hant');
    let count = 0;
    cards.forEach(card => {
      const match = (category === 'all' || card.dataset.category === category) &&
        card.dataset.search.toLocaleLowerCase('zh-Hant').includes(query);
      card.hidden = !match;
      if (match) count++;
    });
    status.textContent = `顯示 ${count} / ${cards.length} 篇筆記`;
    const title = category === 'all' ? '全部筆記' : category;
    document.querySelector('#chapter-title').textContent = title;
    document.querySelector('.chapter-count').textContent = `（${String(count).padStart(2, '0')}）`;
    document.querySelector('#folio-title').textContent = title;
    document.querySelector('#folio-number').textContent = String(buttons.findIndex(b => b.dataset.filter === category) + 1).padStart(2, '0');
    document.querySelector('#empty').hidden = count !== 0;
  };
  buttons.forEach(button => button.addEventListener('click', () => {
    const changed = category !== button.dataset.filter;
    category = button.dataset.filter;
    buttons.forEach(b => {
      const selected = b === button;
      b.classList.toggle('selected', selected);
      b.setAttribute('aria-pressed', String(selected));
    });
    update();
    if (changed && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      document.querySelector('.book-page-content').animate([
        { opacity: 0.25, transform: 'perspective(1000px) rotateY(-7deg)' },
        { opacity: 1, transform: 'perspective(1000px) rotateY(0deg)' }
      ], { duration: 380, easing: 'ease-out' });
    }
  }));
  search.addEventListener('input', update);
  tools.hidden = false;
  search.closest('label').hidden = false;
  update();
})();
