// ── VALMIKI RAMAYANA PWA — app.js ──
// Sanskrit text: GRETIL (CC BY-NC-SA 4.0) | Translations: ramayana.info (live)

// ── STATE ──
let DB        = null;   // full ramayana.json
let curKanda  = 0;      // 0-indexed
let curSarga  = 0;      // 0-indexed within kanda
let curShloka = 0;      // 0-indexed within sarga
let lang      = 'hi';
let showRoman = false;
let wbwOpen   = false;
let bmKanda   = null;
let bmSarga   = null;
let bmShloka  = null;

// localStorage keys
const LS = {
  lang:    'rv_lang',
  theme:   'rv_theme',
  size:    'rv_size',
  roman:   'rv_roman',
  bmK:     'rv_bm_kanda',
  bmS:     'rv_bm_sarga',
  bmSh:    'rv_bm_shloka',
  cache:   (k,sa,sh) => `rv_tr_${k}_${sa}_${sh}_${lang}`
};

// Translation cache in memory (also persisted to localStorage)
const trCache = {};

// ── BOOT ──
async function boot() {
  // Load preferences
  lang      = localStorage.getItem(LS.lang)  || 'hi';
  showRoman = localStorage.getItem(LS.roman) === 'true';
  const theme = localStorage.getItem(LS.theme) || 'light';
  const size  = localStorage.getItem(LS.size)  || 'medium';

  // Load bookmark
  const bmK  = localStorage.getItem(LS.bmK);
  const bmSa = localStorage.getItem(LS.bmS);
  const bmSh = localStorage.getItem(LS.bmSh);
  if (bmK !== null) { bmKanda = parseInt(bmK); bmSarga = parseInt(bmSa); bmShloka = parseInt(bmSh); }

  // Apply prefs silently
  document.getElementById('app').setAttribute('data-theme', theme);
  document.getElementById('app').setAttribute('data-fontsize', size);
  _applyThemeUI(theme);
  _applySizeUI(size);
  _applyLangUI();
  _applyRomanUI();

  // Load data
  try {
    const res = await fetch('data/ramayana.json');
    DB = await res.json();
  } catch(e) {
    showToast('Could not load data. Please check your connection.');
    return;
  }

  // Build home screen
  renderHome();
  showScreen('home-screen');

  // Register service worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
}

// ── SCREEN NAVIGATION ──
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => {
    s.classList.remove('active', 'exit-left');
  });
  const target = document.getElementById(id);
  if (target) target.classList.add('active');
}

function pushScreen(id) {
  // Slide current screen left, bring new one in
  document.querySelectorAll('.screen.active').forEach(s => s.classList.add('exit-left'));
  const target = document.getElementById(id);
  if (target) { target.style.transform = 'translateX(100%)'; target.classList.add('active');
    requestAnimationFrame(() => { target.style.transition = 'transform 0.28s ease';
      target.style.transform = 'translateX(0)'; }); }
}

function popScreen(toId) {
  const current = document.querySelector('.screen.active');
  if (current) {
    current.style.transition = 'transform 0.25s ease';
    current.style.transform  = 'translateX(100%)';
    setTimeout(() => { current.classList.remove('active'); current.style.transform = ''; }, 260);
  }
  document.querySelectorAll('.screen.exit-left').forEach(s => {
    s.classList.remove('exit-left');
    s.style.transition = 'transform 0.25s ease';
    s.style.transform  = 'translateX(0)';
    setTimeout(() => { s.style.transition = ''; s.style.transform = ''; }, 260);
  });
  if (toId) {
    const target = document.getElementById(toId);
    if (target && !target.classList.contains('active')) {
      target.classList.add('active');
      target.style.transform = '';
    }
  }
}

// ── HOME SCREEN ──
function renderHome() {
  // Continue reading button
  const btn = document.getElementById('continue-btn');
  if (bmKanda !== null && DB) {
    const k  = DB.kandas[bmKanda];
    const sa = k.sargas[bmSarga];
    const sh = sa ? sa.shlokas[bmShloka] : null;
    if (k && sa && sh) {
      btn.classList.add('visible');
      document.getElementById('continue-loc').textContent =
        `${k.name_sa} · सर्ग ${bmSarga + 1} · श्लोक ${sh.nd}`;
    }
  } else {
    btn.classList.remove('visible');
  }

  // Kanda list
  const list = document.getElementById('kanda-list');
  list.innerHTML = '';
  DB.kandas.forEach((k, i) => {
    const card = document.createElement('div');
    card.className = 'kanda-card';
    card.innerHTML = `
      <div class="kanda-card-left">
        <div class="kanda-num">काण्ड ${i + 1}</div>
        <div class="kanda-name-sa">${k.name_sa}</div>
        <div class="kanda-name-en">${k.name_roman} · ${k.name_en}</div>
      </div>
      <div style="display:flex;align-items:center;gap:10px">
        <span class="kanda-sargas">${k.sarga_count} sargas</span>
        <span class="kanda-arrow">›</span>
      </div>`;
    card.addEventListener('click', () => openKanda(i));
    list.appendChild(card);
  });
}

function continueReading() {
  if (bmKanda === null) return;
  curKanda  = bmKanda;
  curSarga  = bmSarga;
  curShloka = bmShloka;
  openSarga(curSarga, true);
}

// ── SARGA LIST SCREEN ──
function openKanda(ki) {
  curKanda = ki;
  const k = DB.kandas[ki];

  // Header
  document.getElementById('sarga-screen-title').textContent = k.name_sa;
  document.getElementById('sarga-screen-sub').textContent   = k.name_roman;

  // List
  const list = document.getElementById('sarga-list-scroll');
  list.innerHTML = '';

  if (!k.sargas || k.sargas.length === 0) {
    list.innerHTML = `<div style="padding:30px 0;text-align:center;font-family:var(--font-lat);
      font-style:italic;color:var(--ink-soft)">
      Full data for this Kāṇḍa will be available once the complete dataset is loaded.<br><br>
      See README.md for instructions.
    </div>`;
    pushScreen('sarga-screen');
    return;
  }

  k.sargas.forEach((sa, si) => {
    const isBm = bmKanda === ki && bmSarga === si;
    const row  = document.createElement('div');
    row.className = 'sarga-row' + (isBm ? ' bookmarked' : '');
    row.innerHTML = `
      <div class="sarga-left">
        <div class="sarga-num">Sarga ${si + 1}</div>
        <div class="sarga-name-sa">${sa.title_sa || ''}</div>
        <div class="sarga-name-en">${sa.title_en || ''} · ${sa.shlokas.length} shlokas</div>
      </div>
      <div class="sarga-right">
        ${isBm ? '<span class="sarga-bm">🔖</span>' : ''}
        <span class="sarga-arrow">›</span>
      </div>`;
    row.addEventListener('click', () => openSarga(si));
    list.appendChild(row);
  });

  pushScreen('sarga-screen');
}

function backToHome() { popScreen('home-screen'); }

// ── READER ──
function openSarga(si, skipPush) {
  curSarga  = si;
  curShloka = 0;

  // If coming from bookmark, go to bookmarked shloka
  if (bmKanda === curKanda && bmSarga === si) {
    curShloka = bmShloka;
  }

  // Close WBW if open
  wbwOpen = false;
  document.getElementById('wbw-panel').classList.remove('open');
  document.getElementById('wbw-arrow').classList.remove('open');

  paintShloka();
  if (!skipPush) pushScreen('reader-screen');
  else {
    // Coming from continue button — go home → sarga → reader
    pushScreen('reader-screen');
  }
}

function backToSarga() {
  popScreen('sarga-screen');
}

function paintShloka(dir) {
  const k  = DB.kandas[curKanda];
  const sa = k.sargas[curSarga];
  const sh = sa.shlokas[curShloka];

  const doRender = () => {
    // Watermark & labels
    document.getElementById('watermark').textContent = sh.nd;
    document.getElementById('sarga-sublabel').textContent =
      `${k.name_sa} · सर्ग ${curSarga + 1} · श्लोक ${sh.nd}`;
    document.getElementById('reader-counter').textContent =
      `${sh.n} / ${sa.shlokas.length}`;

    // Sanskrit
    document.getElementById('sanskrit-text').innerHTML = sh.sa.replace(/\n/g, '<br>');
    document.getElementById('roman-text').innerHTML    = sh.ro.replace(/\n/g, '<br>');

    // Translation placeholder while fetching
    const td = document.getElementById('trans-text');
    document.getElementById('trans-label').textContent =
      lang === 'hi' ? 'हिंदी अर्थ' : 'English Translation';
    td.className = lang === 'en' ? 'lang-en' : '';
    td.innerHTML = `<span class="trans-offline">${lang === 'hi' ? 'अनुवाद लोड हो रहा है…' : 'Loading translation…'}</span>`;

    // Progress bar
    document.getElementById('reader-progress').style.width =
      ((curShloka + 1) / sa.shlokas.length * 100) + '%';

    // Nav buttons
    document.getElementById('prev-btn').disabled = curShloka === 0;
    document.getElementById('next-btn').disabled = curShloka === sa.shlokas.length - 1;

    // Scroll top
    document.getElementById('reader-scroll').scrollTop = 0;

    // Close WBW
    if (wbwOpen) {
      wbwOpen = false;
      document.getElementById('wbw-panel').classList.remove('open');
      document.getElementById('wbw-arrow').classList.remove('open');
    }

    updateBmBtn();
    fetchTranslation(sh.n);
  };

  if (dir) {
    const rs = document.getElementById('reader-scroll');
    rs.classList.add('fade-out');
    setTimeout(() => {
      rs.classList.remove('fade-out');
      doRender();
      rs.classList.add('fade-in');
      setTimeout(() => rs.classList.remove('fade-in'), 180);
    }, 160);
  } else {
    doRender();
  }
}

// ── TRANSLATION FETCH ──
async function fetchTranslation(shlokaNum) {
  const cacheKey = LS.cache(curKanda + 1, curSarga + 1, shlokaNum);

  // Check localStorage cache first
  const cached = localStorage.getItem(cacheKey);
  if (cached) {
    setTranslationText(cached);
    return;
  }

  // Check memory cache
  if (trCache[cacheKey]) {
    setTranslationText(trCache[cacheKey]);
    return;
  }

  // Check if offline
  if (!navigator.onLine) {
    setTranslationText(null);
    return;
  }

  // Build ramayana.info URL
  // URL format: /story/{kanda-slug}/{sarga-num}/#shloka-{n}
  const kandaSlugs = ['bala','ayodhya','aranya','kishkindha','sundara','yuddha','uttara'];
  const slug = kandaSlugs[curKanda];
  const url  = `https://ramayana.info/story/${slug}/${curSarga + 1}/`;

  try {
    const res  = await fetch(url);
    const html = await res.text();
    const text = extractTranslation(html, shlokaNum, lang);

    if (text) {
      trCache[cacheKey] = text;
      try { localStorage.setItem(cacheKey, text); } catch(e) {}
      setTranslationText(text);
    } else {
      setTranslationText(null);
    }
  } catch(e) {
    setTranslationText(null);
  }
}

function extractTranslation(html, shlokaNum, language) {
  // Parse the ramayana.info page HTML to find the translation for this shloka
  // ramayana.info uses data attributes and structured divs per shloka
  const parser = new DOMParser();
  const doc    = parser.parseFromString(html, 'text/html');

  // Try to find shloka by id or data attribute patterns used on ramayana.info
  const shlokaId = `shloka-${shlokaNum}`;
  let el = doc.getElementById(shlokaId);

  if (!el) {
    // Try data-shloka attribute
    el = doc.querySelector(`[data-shloka="${shlokaNum}"]`);
  }

  if (!el) {
    // Try finding by sequential position
    const allShlokas = doc.querySelectorAll('.shloka, [class*="shloka"]');
    if (allShlokas[shlokaNum - 1]) el = allShlokas[shlokaNum - 1];
  }

  if (!el) return null;

  // Find translation within the element
  const langAttr  = language === 'hi' ? 'hi' : 'en';
  let transEl = el.querySelector(`[lang="${langAttr}"], .translation-${langAttr}, .meaning-${langAttr}`);

  if (!transEl) {
    // Fallback: look for the first paragraph-like element after the Sanskrit
    const ps = el.querySelectorAll('p');
    if (ps.length > 1) transEl = ps[1];
  }

  return transEl ? transEl.textContent.trim() : null;
}

function setTranslationText(text) {
  const td = document.getElementById('trans-text');
  td.className = lang === 'en' ? 'lang-en' : '';

  if (!text) {
    if (!navigator.onLine) {
      td.innerHTML = `<span class="trans-offline">
        ${lang === 'hi'
          ? 'अनुवाद के लिए इंटरनेट आवश्यक है। संस्कृत पाठ नीचे उपलब्ध है।'
          : 'Translation requires internet. The Sanskrit text is available above.'}
      </span>`;
    } else {
      td.innerHTML = `<span class="trans-offline">
        ${lang === 'hi'
          ? 'इस श्लोक का अनुवाद अभी उपलब्ध नहीं है।'
          : 'Translation not yet available for this shloka.'}
      </span>`;
    }
    return;
  }
  td.textContent = text;
}

// ── NAVIGATION ──
function navigate(dir) {
  const sa   = DB.kandas[curKanda].sargas[curSarga];
  const next = curShloka + dir;
  if (next < 0 || next >= sa.shlokas.length) return;
  curShloka = next;
  paintShloka(dir);
}

// ── WORD BY WORD ──
function toggleWBW() {
  wbwOpen = !wbwOpen;
  document.getElementById('wbw-panel').classList.toggle('open', wbwOpen);
  document.getElementById('wbw-arrow').classList.toggle('open', wbwOpen);
  if (wbwOpen) {
    const sh   = DB.kandas[curKanda].sargas[curSarga].shlokas[curShloka];
    const rows = sh.wbw.map(w =>
      `<div class="wbw-row">
        <span class="wbw-sk">${w.s}</span>
        <span class="wbw-sep">→</span>
        <span class="wbw-mn">${w.m}</span>
      </div>`).join('');
    document.getElementById('wbw-content').innerHTML = rows;
  }
}

// ── BOOKMARK ──
function toggleBookmark() {
  if (bmKanda === curKanda && bmSarga === curSarga && bmShloka === curShloka) {
    bmKanda = bmSarga = bmShloka = null;
    localStorage.removeItem(LS.bmK);
    localStorage.removeItem(LS.bmS);
    localStorage.removeItem(LS.bmSh);
    showToast('Bookmark removed');
  } else {
    bmKanda = curKanda; bmSarga = curSarga; bmShloka = curShloka;
    localStorage.setItem(LS.bmK,  bmKanda);
    localStorage.setItem(LS.bmS,  bmSarga);
    localStorage.setItem(LS.bmSh, bmShloka);
    const sh = DB.kandas[curKanda].sargas[curSarga].shlokas[curShloka];
    showToast(`Saved · ${DB.kandas[curKanda].name_sa} · सर्ग ${curSarga+1} · ${sh.nd}`);
    renderHome();
  }
  updateBmBtn();
}

function updateBmBtn() {
  const saved = bmKanda === curKanda && bmSarga === curSarga && bmShloka === curShloka;
  document.getElementById('bookmark-btn').classList.toggle('saved', saved);
  document.getElementById('bm-label').textContent = saved
    ? 'Saved · सुरक्षित ✓'
    : 'Save Position · स्थान सुरक्षित करें';
}

// ── LANGUAGE ──
function setLang(l) {
  lang = l;
  localStorage.setItem(LS.lang, l);
  _applyLangUI();
  // Refresh translation if on reader screen
  if (document.getElementById('reader-screen').classList.contains('active')) {
    const sh = DB.kandas[curKanda].sargas[curSarga].shlokas[curShloka];
    document.getElementById('trans-label').textContent =
      lang === 'hi' ? 'हिंदी अर्थ' : 'English Translation';
    const td = document.getElementById('trans-text');
    td.className = lang === 'en' ? 'lang-en' : '';
    td.innerHTML = `<span class="trans-offline">${lang === 'hi' ? 'अनुवाद लोड हो रहा है…' : 'Loading…'}</span>`;
    fetchTranslation(sh.n);
  }
}

function _applyLangUI() {
  document.getElementById('tab-hi').classList.toggle('active', lang === 'hi');
  document.getElementById('tab-en').classList.toggle('active', lang === 'en');
  document.getElementById('slang-hi').classList.toggle('active', lang === 'hi');
  document.getElementById('slang-en').classList.toggle('active', lang === 'en');
}

// ── SETTINGS ──
function openSettings()  { document.getElementById('settings-panel').classList.add('open'); }
function closeSettings() { document.getElementById('settings-panel').classList.remove('open'); }

function setTheme(t) {
  document.getElementById('app').setAttribute('data-theme', t);
  localStorage.setItem(LS.theme, t);
  _applyThemeUI(t);
}
function _applyThemeUI(t) {
  document.getElementById('theme-light').classList.toggle('active', t === 'light');
  document.getElementById('theme-dark').classList.toggle('active',  t === 'dark');
}

function setSize(s) {
  document.getElementById('app').setAttribute('data-fontsize', s);
  localStorage.setItem(LS.size, s);
  _applySizeUI(s);
}
function _applySizeUI(s) {
  ['small','medium','large'].forEach(x =>
    document.getElementById('size-' + x).classList.toggle('active', x === s));
}

function setRoman(on) {
  showRoman = on;
  localStorage.setItem(LS.roman, on);
  _applyRomanUI();
}
function _applyRomanUI() {
  document.getElementById('roman-text').classList.toggle('visible', showRoman);
  document.getElementById('roman-on').classList.toggle('active',  showRoman);
  document.getElementById('roman-off').classList.toggle('active', !showRoman);
}

// ── HOME CONTROLS ──
function setHomeTheme(t) { setTheme(t);
  document.getElementById('home-ctrl-light').classList.toggle('active', t === 'light');
  document.getElementById('home-ctrl-dark').classList.toggle('active',  t === 'dark');
}

// ── TOAST ──
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2400);
}

// ── SWIPE ON READER ──
let _tx = 0;
document.getElementById('reader-scroll').addEventListener('touchstart',
  e => { _tx = e.touches[0].clientX; }, { passive: true });
document.getElementById('reader-scroll').addEventListener('touchend',
  e => { const dx = e.changedTouches[0].clientX - _tx;
    if (Math.abs(dx) > 55) navigate(dx < 0 ? 1 : -1); }, { passive: true });

// ── START ──
boot();
