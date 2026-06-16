# वाल्मीकि रामायण — Valmiki Ramayana PWA

A Progressive Web App for reading the Valmiki Ramayana verse by verse in Sanskrit,
with Hindi and English translations. Installs on iPhone home screen like a native app.

## License

CC BY-NC-SA 4.0 — free for personal, educational, and spiritual use.
Not for commercial distribution. See ATTRIBUTION.md for source credits.

---

## How to Use on Your iPhone (No App Store Needed)

1. Host the app on GitHub Pages or Netlify (see Hosting below)
2. Open the URL in **Safari** on your iPhone
3. Tap the **Share** button (box with arrow)
4. Tap **Add to Home Screen**
5. Tap **Add**

The app now lives on your home screen and works offline for any shloka you have read before.

---

## File Structure

```
ramayana-pwa/
├── index.html          ← Main app (all three screens)
├── app.js              ← All logic: navigation, fetch, state
├── style.css           ← All styles: light/dark mode, fonts
├── sw.js               ← Service Worker: offline support
├── manifest.json       ← PWA: home screen icon, display mode
├── data/
│   └── ramayana.json   ← Sanskrit text (all 7 Kandas)
├── icons/
│   ├── icon-192.png    ← Home screen icon (192×192)
│   └── icon-512.png    ← Splash screen icon (512×512)
├── README.md           ← This file
└── ATTRIBUTION.md      ← Source credits
```

---

## Hosting on GitHub Pages (Free, Recommended)

1. Create a free account at https://github.com
2. Create a new repository called `ramayana-pwa`
3. Upload all files (maintaining the folder structure above)
4. Go to repository Settings → Pages → Source → main branch → / (root)
5. Your app will be live at `https://yourusername.github.io/ramayana-pwa`

Share this URL with anyone who wants to use it.

---

## Hosting on Netlify (Alternative, also Free)

1. Go to https://netlify.com and sign up
2. Drag and drop the entire `ramayana-pwa` folder onto the Netlify dashboard
3. Your app gets a URL like `https://ramayana-abc123.netlify.app`
4. You can set a custom subdomain in Netlify settings

---

## The Sanskrit Data File (ramayana.json)

The file at `data/ramayana.json` contains the Sanskrit text for all 7 Kāṇḍas.
The current file ships with **Bālakāṇḍa Sarga 1, Shlokas 1–5** as seed data
so you can test the app immediately.

To load the complete text (all ~24,000 shlokas):

### Option A — Manual (Recommended for small additions)

Open `data/ramayana.json` and add sargas following the existing structure:

```json
{
  "id": 2,
  "title_sa": "सर्ग शीर्षक",
  "title_en": "Sarga title",
  "shlokas": [
    {
      "n": 1, "nd": "१",
      "sa": "Sanskrit text line 1 ।\nline 2 ॥",
      "ro": "roman transliteration line 1 |\nline 2 ||",
      "wbw": [
        { "s": "word", "m": "meaning" }
      ]
    }
  ]
}
```

### Option B — Fetch from GRETIL (For developers)

GRETIL provides the full text at:
https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/

A Python or Node.js script can parse the GRETIL XML files and populate ramayana.json.
The data structure in ramayana.json is designed to accept this directly.

---

## App Icons

The `icons/` folder needs two PNG files for the home screen icon:
- `icon-192.png` — 192×192 pixels
- `icon-512.png` — 512×512 pixels

You can create these using any image editor, or use a free tool like
https://realfavicongenerator.net to generate them from any image.

A simple saffron background with ॐ in white Devanagari works well.

---

## How Translations Work

- **Sanskrit text**: bundled in `data/ramayana.json`, always available offline
- **Hindi / English translation**: fetched live from ramayana.info when you read a shloka
- **Caching**: after a shloka is read online, the translation is saved to your device
  and available offline on all future visits
- **Offline message**: if you are offline and haven't read a shloka before,
  the app shows a message and the Sanskrit text is still fully readable

---

## How to Share with Friends

1. Host the app (see above) — one person needs to do this once
2. Share the URL
3. Each person opens it in Safari on iPhone and taps Add to Home Screen
4. Everyone gets their own reading position and settings stored locally

No accounts. No sign-up. No cost.

---

## Open Source

This project is open source under CC BY-NC-SA 4.0.
If you improve it, please share your changes with the same license
and credit the original Sanskrit source (GRETIL) and translation source (ramayana.info).
