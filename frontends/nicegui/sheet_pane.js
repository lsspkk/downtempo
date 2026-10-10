// Sheet pane's page script (sheet_pane.py): scroll keys, fit page, refit on resize.
// The sheet viewport turns as a whole, so its scrollbar, the wheel and the scroll keys follow the page.
// Sheet scroll keys run in the page: no server round trip, and preventDefault stops the browser
// from scrolling too. A press during a smooth scroll continues from its target, so a quick
// double tap on a footswitch moves two steps. Space and ←/→ only get preventDefault (the server
// handles them) so a focused scroll area doesn't also scroll.
window.dt = {settings: __SETTINGS__, target: null, timer: null, fit: null};
dt.scrollTo = (el, top) => {
  top = Math.max(0, Math.min(top, el.scrollHeight - el.clientHeight));
  clearTimeout(dt.timer);
  dt.target = dt.settings.smooth ? top : null;
  if (dt.settings.smooth) dt.timer = setTimeout(() => { dt.target = null; }, 600);
  el.scrollTo({top, behavior: dt.settings.smooth ? 'smooth' : 'instant'});
};
dt.scroll = (kind, dir) => {
  const el = document.querySelector('.sheet-view');
  if (!el) return;
  const from = dt.target ?? el.scrollTop;
  if (kind === 'step') return dt.scrollTo(el, from + dir * el.clientHeight * dt.settings.scroll_step / 100);
  if (kind === 'end') return dt.scrollTo(el, dir < 0 ? 0 : el.scrollHeight);
  if (dt.settings.page_mode === 'page') {
    const tops = [...el.querySelectorAll('img')].map((img) => img.offsetTop - 8);
    const next = dir > 0 ? tops.find((t) => t > from + 24) : tops.reverse().find((t) => t < from - 24);
    return dt.scrollTo(el, next ?? (dir > 0 ? el.scrollHeight : 0));
  }
  dt.scrollTo(el, from + dir * el.clientHeight * 0.85);
};
const SCROLL_KEYS = {ArrowUp: ['step', -1], ArrowDown: ['step', 1], PageUp: ['screen', -1],
                     PageDown: ['screen', 1], Home: ['end', -1], End: ['end', 1]};
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey || e.altKey || e.metaKey) return;
  if (['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;
  if (document.querySelector('.q-dialog')) return;
  const action = SCROLL_KEYS[e.key];
  if (action) { e.preventDefault(); dt.scroll(...action); }
  else if ([' ', 'ArrowLeft', 'ArrowRight'].includes(e.key)) e.preventDefault();
});
// Fit page: the zoom (width %) at which the page at the top of the view fits whole, in the
// view's own (rotated) axes; never wider than fit width. Waits for the image to load.
dt.fitPage = async () => {
  const el = document.querySelector('.sheet-view');
  const imgs = el ? [...el.querySelectorAll('img')] : [];
  if (!imgs.length) return null;
  const img = imgs.filter((i) => i.offsetTop - 16 <= el.scrollTop + 24).pop() ?? imgs[0];
  if (!img.naturalWidth) await new Promise((done) => {
    img.addEventListener('load', done, {once: true});
    img.addEventListener('error', done, {once: true});
  });
  if (!img.naturalWidth) return null;
  const width = el.clientWidth - 32, height = el.clientHeight - 32;  // minus p-4
  const zoom = height * img.naturalWidth / img.naturalHeight / width * 100;
  return {zoom: Math.floor(Math.min(100, zoom)), page: imgs.indexOf(img)};
};
// After the server changed the zoom: put that page at the top again.
dt.toPage = (page) => requestAnimationFrame(() => requestAnimationFrame(() => {
  const el = document.querySelector('.sheet-view');
  const img = el?.querySelectorAll('img')[page];
  if (img) el.scrollTo({top: img.offsetTop - 16, behavior: 'instant'});
}));
// The frame changes size with the window, song list, controls and full screen: fit again.
dt.watch = () => new ResizeObserver(() => { if (dt.fit === 'page') emitEvent('refit'); })
  .observe(document.querySelector('.sheet-frame'));
