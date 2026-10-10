// Loop editor (docs/loop-editor.md): overview, time ruler and waveform drawn on canvases. Select,
// zoom and scroll run here without a server round trip; the server gets only the results through
// emitEvent: le_loop {a, b}, le_seek t, le_undo. Times are seconds of the recording.
window.le = {
  open: false,
  levels: [],      // peaks 0..255 per bin; levels[k] has bins of binSec * 2^k
  binSec: 0,
  dur: 0,
  view: {start: 0, span: 1},
  loop: null,      // [a, b]
  looping: false,
  play: {pos: 0, at: 0, playing: false, speed: 1},
  sel: null,       // {mode: 'down' | 'drag' | 'pending' | 'edge', a, b, x0}
  px: null,        // pointer x on the waveform (css px, may lie outside while dragging)
  frame: 0,
  observer: null,
};

const MIN_SPAN = 1;        // seconds across the view at the deepest zoom
const GRIP = {w: 20, h: 28};  // the drag handle on top of each loop edge (px)
const RULER_ZOOM = 0.012;  // per px dragged on the ruler: 100 px down = 3.3× in
const LINE_GRAB = 5;       // px beside an edge line that also grab it
const CLICK = 4;           // px a press may move and still be a click
// Dragging into the edge zone (or past it) scrolls: slowly at first, faster the longer the pointer
// stays there. Time, not distance: at the screen's edge the pointer can't go further.
const EDGE_ZONE = 24;      // px inside each side of the waveform
const SCROLL = {start: 0.15, perSecond: 0.6, max: 2};  // views per second: start + perSecond × held, up to max
const HINTS = {
  idle: 'Click the start, then the end · drag the ⠿ handles to move an edge · pinch or Ctrl+wheel to zoom · click the ruler to seek, drag it up / down to zoom · Esc back',
  pending: 'Click to set the end · scroll and zoom meanwhile · Esc cancels',
  drag: 'Release to set the loop · hold at the edge to scroll',
  edge: 'Release to set this edge · hold at the edge to scroll',
};

le.load = (b64, binSec, dur) => {
  const raw = atob(b64);
  let level = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) level[i] = raw.charCodeAt(i);
  le.levels = [level];
  while (level.length > 1) {  // each level halves the previous by max
    const next = new Uint8Array(Math.ceil(level.length / 2));
    for (let i = 0; i < next.length; i++) next[i] = Math.max(level[2 * i], level[2 * i + 1] ?? 0);
    le.levels.push(level = next);
  }
  le.binSec = binSec;
  le.dur = dur;
};

le.el = (name) => document.querySelector('.le-' + name);

le.show = (view, loop, looping) => {
  le.open = true;
  le.sel = null;
  le.setLoop(loop, looping);
  const start = () => {
    if (!le.el('main')?.clientWidth) return requestAnimationFrame(start);  // dialog still opening
    le.view = view ?? le.loopView() ?? {start: 0, span: le.dur};
    le.clampView();
    le.observer?.disconnect();
    le.observer = new ResizeObserver(() => le.draw());
    for (const name of ['main', 'ruler', 'overview']) le.observer.observe(le.el(name));
    le.bind();
    le.hint();
    cancelAnimationFrame(le.frame);
    le.frame = requestAnimationFrame(le.animate);
  };
  start();
};

le.hide = () => {
  le.open = false;
  le.sel = null;
  le.observer?.disconnect();
  cancelAnimationFrame(le.frame);
  return le.view;
};

le.setLoop = (loop, looping) => {
  le.loop = loop;
  le.looping = looping;
};

le.setPlay = (pos, playing, speed) => {
  le.play = {pos, at: performance.now(), playing, speed};
};

// ---------------------------------------------------------------- view

le.loopView = () => {
  if (!le.loop) return null;
  const [a, b] = le.loop, margin = (b - a) * 0.1;
  return {start: a - margin, span: b - a + 2 * margin};
};

le.clampView = () => {
  const v = le.view;
  v.span = Math.min(Math.max(v.span, Math.min(MIN_SPAN, le.dur)), le.dur);
  v.start = Math.min(Math.max(v.start, 0), le.dur - v.span);
};

le.zoomAt = (t, factor) => {  // factor > 1 zooms in; the time t stays where it is on screen
  const v = le.view, share = (t - v.start) / v.span;
  v.span /= factor;
  le.clampView();
  v.start = t - share * v.span;
  le.clampView();
  le.followSelection();
};

le.zoomBy = (factor) => {
  const v = le.view, head = le.playhead();
  let t = v.start + v.span / 2;
  if (le.sel?.mode === 'pending') t = le.sel.b;
  else if (head >= v.start && head <= v.start + v.span) t = head;
  le.zoomAt(t, factor);
};

le.wholeSong = () => { le.view = {start: 0, span: le.dur}; le.clampView(); };

le.zoomToLoop = () => {
  if (!le.loop) return;
  le.view = le.loopView();
  le.clampView();
};

// A pending selection's end follows the pointer, also when the view moves under it.
le.followSelection = () => {
  if (le.sel?.mode === 'pending' && le.px !== null) le.sel.b = le.timeAt(le.px);
};

le.width = () => le.el('main').clientWidth;
le.timeAt = (x) => le.view.start + Math.min(Math.max(x, 0), le.width()) / le.width() * le.view.span;
le.xAt = (t) => (t - le.view.start) / le.view.span * le.width();

le.playhead = () => {
  const p = le.play;
  let t = p.pos + (p.playing ? (performance.now() - p.at) / 1000 * p.speed : 0);
  if (p.playing && le.looping && le.loop && t > le.loop[1]) t = le.loop[0] + (t - le.loop[1]);
  return Math.min(t, le.dur);
};

// ---------------------------------------------------------------- input

le.bind = () => {
  const main = le.el('main');
  if (main.dataset.bound) return;  // the dialog keeps its elements between visits
  main.dataset.bound = '1';
  main.addEventListener('pointerdown', le.down);
  main.addEventListener('pointermove', le.move);
  main.addEventListener('pointerup', le.up);
  main.addEventListener('pointerleave', () => { if (!le.sel) le.px = null; });
  for (const name of ['main', 'ruler', 'overview']) {
    le.el(name).addEventListener('wheel', le.wheel, {passive: false});
  }
  const ruler = le.el('ruler');
  ruler.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    le.capture(ruler, e.pointerId);
    le.ruler = {x: e.offsetX, y: e.clientY, t: le.timeAt(e.offsetX), span: le.view.span, zoom: false};
  });
  ruler.addEventListener('pointermove', le.rulerMove);
  ruler.addEventListener('pointerup', (e) => {
    const r = le.ruler;
    le.ruler = null;
    ruler.style.cursor = 'pointer';
    try { ruler.releasePointerCapture(e.pointerId); } catch {}
    if (!r || r.zoom) return;
    le.play.pos = r.t;  // a click: play from here
    le.play.at = performance.now();
    emitEvent('le_seek', r.t);
  });
  const overview = le.el('overview');
  overview.addEventListener('pointerdown', (e) => {
    const t = e.offsetX / overview.clientWidth * le.dur, v = le.view;
    le.grab = t >= v.start && t <= v.start + v.span ? t - v.start : v.span / 2;
    le.capture(overview, e.pointerId);
    le.overviewMove(e);
  });
  overview.addEventListener('pointermove', (e) => { if (le.grab !== null) le.overviewMove(e); });
  overview.addEventListener('pointerup', () => { le.grab = null; });
  le.grab = null;
};

// Dragging the ruler zooms (as in Cubase): down zooms in, up zooms out; the grabbed time stays
// under the pointer, so moving sideways scrolls at the same time.
le.rulerMove = (e) => {
  const r = le.ruler;
  if (!r) return;
  const dy = e.clientY - r.y;
  if (!r.zoom && Math.abs(dy) + Math.abs(e.offsetX - r.x) < CLICK) return;
  r.zoom = true;
  le.el('ruler').style.cursor = 'ns-resize';
  const v = le.view;
  v.span = r.span * Math.exp(-dy * RULER_ZOOM);
  le.clampView();
  v.start = r.t - Math.min(Math.max(e.offsetX, 0), le.width()) / le.width() * v.span;
  le.clampView();
  le.followSelection();
};

le.overviewMove = (e) => {
  const overview = le.el('overview');
  le.view.start = e.offsetX / overview.clientWidth * le.dur - le.grab;
  le.clampView();
  le.followSelection();
};

// Moves outside the element keep coming while the button is down (edge scrolling needs them).
le.capture = (el, id) => { try { el.setPointerCapture(id); } catch {} };

// The loop edge whose handle (or line) is at x, y: {edge, grip} or null.
le.edgeAt = (x, y) => {
  if (!le.loop) return null;
  const d = le.loop.map((t) => Math.abs(le.xAt(t) - x));
  const edge = d[0] <= d[1] ? 0 : 1;
  if (d[edge] <= GRIP.w / 2 && y <= GRIP.h) return {edge, grip: true};
  return d[edge] <= LINE_GRAB ? {edge, grip: false} : null;
};

le.down = (e) => {
  if (e.button !== 0) return;
  const x = e.offsetX, t = le.timeAt(x);
  le.px = x;
  if (le.sel?.mode === 'pending') {  // second click of click–move–click
    le.sel.b = t;
    return le.commit();
  }
  le.capture(e.currentTarget, e.pointerId);
  const hit = le.edgeAt(x, e.offsetY);
  if (hit) {
    const edge = hit.edge;
    le.sel = {mode: 'edge', a: le.loop[1 - edge], b: le.loop[edge], x0: x};
    e.currentTarget.style.cursor = 'grabbing';
  } else {
    le.sel = {mode: 'down', a: t, b: t, x0: x};
  }
  le.hint();
};

le.move = (e) => {
  le.px = e.offsetX;
  const sel = le.sel;
  if (!sel) {
    const hit = le.edgeAt(e.offsetX, e.offsetY);
    e.currentTarget.style.cursor = !hit ? 'crosshair' : hit.grip ? 'grab' : 'ew-resize';
    return;
  }
  if (sel.mode === 'down' && Math.abs(e.offsetX - sel.x0) >= CLICK) sel.mode = 'drag';
  if (sel.mode !== 'down') sel.b = le.timeAt(e.offsetX);
  le.hint();
};

le.up = (e) => {
  const sel = le.sel;
  if (!sel) return;
  try { e.currentTarget.releasePointerCapture(e.pointerId); } catch {}
  if (sel.mode === 'down') sel.mode = 'pending';  // a click: the end follows the pointer
  else if (sel.mode === 'drag' || sel.mode === 'edge') {
    e.currentTarget.style.cursor = 'crosshair';
    return le.commit();
  }
  le.hint();
};

le.commit = () => {
  const sel = le.sel, a = Math.min(sel.a, sel.b), b = Math.max(sel.a, sel.b);
  le.sel = null;
  le.hint();
  emitEvent('le_loop', {a, b, edge: sel.mode === 'edge'});
};

le.cancel = () => {
  le.sel = null;
  le.hint();
};

le.wheel = (e) => {
  e.preventDefault();
  const v = le.view;
  if (e.ctrlKey) {  // pinch on a trackpad arrives as Ctrl + wheel
    const main = le.el('main'), x = e.currentTarget === main ? e.offsetX : main.clientWidth / 2;
    le.zoomAt(le.timeAt(x), Math.exp(-e.deltaY * 0.01));
    return;
  }
  // two-finger sideways, Shift + wheel, or a plain wheel: all move along the song
  const dx = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY;
  v.start += dx / le.width() * v.span;
  le.clampView();
  le.followSelection();
};

// Keys the editor owns while open. Capture phase, so the player's own key handling doesn't see them.
window.addEventListener('keydown', (e) => {
  if (!le.open || ['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;
  let used = true;
  if (e.key === 'Escape' && le.sel) le.cancel();
  else if ((e.key === '+' || e.key === '=') && !e.ctrlKey) le.zoomBy(2);
  else if (e.key === '-' && !e.ctrlKey) le.zoomBy(0.5);
  else if (e.key.toLowerCase() === 'z' && (e.ctrlKey || e.metaKey)) emitEvent('le_undo');
  else used = false;
  if (used) { e.preventDefault(); e.stopPropagation(); }
}, true);

le.hint = () => {
  const hint = le.el('hint');
  if (hint) hint.textContent = HINTS[le.sel?.mode === 'down' ? 'idle' : le.sel?.mode ?? 'idle'];
  const zoom = le.el('zoom');
  if (zoom) {
    const f = le.dur / le.view.span;
    zoom.textContent = (f < 10 ? Math.round(f * 10) / 10 : Math.round(f)) + '×';
  }
};

// ---------------------------------------------------------------- animation and drawing

le.animate = (now) => {
  if (!le.open) return;
  const dt = Math.min((now - (le.last ?? now)) / 1000, 0.1);
  le.last = now;
  const sel = le.sel, w = le.width();
  const dragging = sel && (sel.mode === 'drag' || sel.mode === 'edge') && le.px !== null;
  const side = !dragging ? 0 : le.px < EDGE_ZONE ? -1 : le.px > w - EDGE_ZONE ? 1 : 0;
  le.dragging = dragging;
  le.edgeSide = side;
  if (side) {
    le.edgeSince ??= now;
    const held = (now - le.edgeSince) / 1000;
    const speed = Math.min(SCROLL.start + SCROLL.perSecond * held, SCROLL.max);
    le.view.start += side * speed * le.view.span * dt;
    le.clampView();
    sel.b = le.timeAt(le.px);
  } else {
    le.edgeSince = null;
  }
  // While playing, turn a page when the playhead would leave the view (not while selecting). Not
  // while a loop edge is in view either: the user is fixing that edge, and the jump back to the
  // loop start would pull the view away on every pass (Audacity warns of this: web/audacity-timeline.txt).
  const head = le.playhead(), v = le.view;
  const edgeInView = le.looping && le.loop?.some((t) => t >= v.start && t <= v.start + v.span);
  if (le.play.playing && !sel && !edgeInView && (head > v.start + v.span || head < v.start)) {
    v.start = head - v.span * 0.05;
    le.clampView();
  }
  le.hint();
  le.draw();
  le.frame = requestAnimationFrame(le.animate);
};

le.colors = () => {
  const dark = document.body.classList.contains('body--dark');
  return {
    bg: dark ? '#1d1d1f' : '#ffffff',
    wave: dark ? '#7d87a8' : '#8a94b0',
    text: dark ? '#c8c8d0' : '#55555f',
    tick: dark ? '#55555f' : '#c8c8d0',
    head: '#4f5bd5',
    loop: '#f59e0b',
  };
};

le.canvas = (name) => {  // sized to the element in device pixels; drawing in css px
  const c = le.el(name), dpr = window.devicePixelRatio || 1;
  const w = c.clientWidth, h = c.clientHeight;
  if (c.width !== Math.round(w * dpr) || c.height !== Math.round(h * dpr)) {
    c.width = Math.round(w * dpr);
    c.height = Math.round(h * dpr);
  }
  const g = c.getContext('2d');
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, w, h);
  return {g, w, h};
};

// Max peak (0..1) for each of `w` columns covering start .. start + span.
le.columns = (start, span, w) => {
  const perPx = span / le.binSec / w;
  const k = Math.max(0, Math.min(le.levels.length - 1, Math.floor(Math.log2(Math.max(perPx, 1)))));
  const level = le.levels[k], bin = le.binSec * 2 ** k, out = new Float32Array(w);
  for (let x = 0; x < w; x++) {
    const i0 = Math.floor((start + x / w * span) / bin);
    const i1 = Math.max(i0 + 1, Math.floor((start + (x + 1) / w * span) / bin));
    let p = 0;
    for (let i = i0; i < i1 && i < level.length; i++) p = Math.max(p, level[i]);
    out[x] = p / 255;
  }
  return out;
};

le.draw = () => {
  if (!le.open || !le.levels.length || !le.el('main')?.clientWidth) return;
  const c = le.colors();
  le.drawOverview(c);
  le.drawRuler(c);
  le.drawMain(c);
};

le.region = (g, x0, x1, h, alpha, color) => {
  g.globalAlpha = alpha;
  g.fillStyle = color;
  g.fillRect(Math.min(x0, x1), 0, Math.abs(x1 - x0), h);
  g.globalAlpha = 1;
};

le.line = (g, x, h, color, width, dash = []) => {
  g.strokeStyle = color;
  g.lineWidth = width;
  g.setLineDash(dash);
  g.beginPath();
  g.moveTo(x, 0);
  g.lineTo(x, h);
  g.stroke();
  g.setLineDash([]);
};

le.bars = (g, peaks, h, color) => {
  const mid = h / 2;
  g.fillStyle = color;
  for (let x = 0; x < peaks.length; x++) {
    const half = Math.max(peaks[x] * mid * 0.92, 0.5);
    g.fillRect(x, mid - half, 1, half * 2);
  }
};

le.drawMain = (c) => {
  const {g, w, h} = le.canvas('main');
  const v = le.view, xAt = (t) => (t - v.start) / v.span * w;
  if (le.loop) le.region(g, xAt(le.loop[0]), xAt(le.loop[1]), h, le.looping ? 0.22 : 0.1, c.loop);
  const sel = le.sel;
  if (sel && sel.mode !== 'down' && sel.mode !== 'edge') le.region(g, xAt(sel.a), xAt(sel.b), h, 0.25, c.loop);
  le.bars(g, le.columns(v.start, v.span, w), h, c.wave);
  if (sel && sel.mode === 'edge') {  // one edge follows the pointer, both keep their handles
    le.region(g, xAt(sel.a), xAt(sel.b), h, 0.15, c.loop);
    le.edge(g, xAt(sel.a), h, sel.a < sel.b ? 'A' : 'B', c);
    le.edge(g, xAt(sel.b), h, sel.a < sel.b ? 'B' : 'A', c);
  } else if (sel && sel.mode !== 'down') {
    le.line(g, xAt(sel.a), h, c.loop, 2);
    le.line(g, xAt(sel.b), h, c.loop, 2, sel.mode === 'pending' ? [6, 4] : []);
  } else if (le.loop) {
    le.loop.forEach((t, i) => le.edge(g, xAt(t), h, i === 0 ? 'A' : 'B', c));
  }
  le.line(g, xAt(le.playhead()), h, c.head, 2);
  if (le.dragging) {  // the scroll zones: faint while dragging, stronger where it scrolls now
    for (const side of [-1, 1]) {
      le.region(g, side < 0 ? 0 : w - EDGE_ZONE, side < 0 ? EDGE_ZONE : w, h,
                le.edgeSide === side ? 0.25 : 0.08, c.head);
    }
  }
};

// A loop edge: its line, a drag handle with the standard grip dots on top, and its letter.
le.edge = (g, x, h, letter, c) => {
  le.line(g, x, h, c.loop, 2);
  const left = x - GRIP.w / 2;
  g.fillStyle = c.loop;
  g.beginPath();
  if (g.roundRect) g.roundRect(left, 0, GRIP.w, GRIP.h, [0, 0, 4, 4]);
  else g.rect(left, 0, GRIP.w, GRIP.h);
  g.fill();
  g.fillStyle = '#ffffff';
  for (const dx of [-3.5, 3.5]) {
    for (const y of [8, 14, 20]) {
      g.beginPath();
      g.arc(x + dx, y, 1.6, 0, 2 * Math.PI);
      g.fill();
    }
  }
  g.fillStyle = c.loop;  // the letter beside the handle, on the loop's side
  g.font = 'bold 13px sans-serif';
  g.textAlign = letter === 'A' ? 'left' : 'right';
  g.fillText(letter, letter === 'A' ? x + GRIP.w / 2 + 4 : x - GRIP.w / 2 - 4, 18);
  g.textAlign = 'start';
};

le.drawRuler = (c) => {
  const {g, w, h} = le.canvas('ruler');
  const v = le.view;
  const steps = [0.1, 0.2, 0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300];
  const step = steps.find((s) => s / v.span * w >= 70) ?? 600;
  g.fillStyle = c.text;
  g.strokeStyle = c.tick;
  g.font = '11px sans-serif';
  for (let t = Math.ceil(v.start / step) * step; t <= v.start + v.span; t += step) {
    const x = (t - v.start) / v.span * w;
    g.beginPath();
    g.moveTo(x, h - 6);
    g.lineTo(x, h);
    g.stroke();
    const m = Math.floor(t / 60), sec = t - m * 60;
    const label = `${m}:${(step < 1 ? sec.toFixed(1) : Math.round(sec).toString()).padStart(step < 1 ? 4 : 2, '0')}`;
    g.fillText(label, x + 3, h - 8);
  }
  const head = (le.playhead() - v.start) / v.span * w;
  g.fillStyle = c.head;
  g.beginPath();
  g.moveTo(head - 5, 0);
  g.lineTo(head + 5, 0);
  g.lineTo(head, 7);
  g.fill();
};

le.drawOverview = (c) => {
  const {g, w, h} = le.canvas('overview');
  const xAt = (t) => t / le.dur * w;
  if (le.loop) le.region(g, xAt(le.loop[0]), xAt(le.loop[1]), h, le.looping ? 0.3 : 0.15, c.loop);
  le.bars(g, le.columns(0, le.dur, w), h, c.wave);
  const v = le.view;
  le.region(g, xAt(v.start), xAt(v.start + v.span), h, 0.12, c.head);
  g.strokeStyle = c.head;
  g.lineWidth = 2;
  g.strokeRect(xAt(v.start) + 1, 1, Math.max(xAt(v.start + v.span) - xAt(v.start) - 2, 2), h - 2);
  le.line(g, xAt(le.playhead()), h, c.head, 1.5);
};
