# Valmiki Ramayana App — GitHub Pages Setup

## Files in this repo
```
index.html   ← the entire app (one file)
SETUP.md     ← this file
```

---

## Step 1 — Add the file to your repository

You have two options:

### Option A — GitHub web interface (no Git needed)
1. Go to your repository on github.com
2. Click **Add file → Upload files**
3. Drag `index.html` into the upload area
4. At the bottom, click **Commit changes**

### Option B — Git command line
```bash
cp index.html /path/to/your/repo/
cd /path/to/your/repo/
git add index.html
git commit -m "Add Valmiki Ramayana reader"
git push
```

---

## Step 2 — Enable GitHub Pages

1. Go to your repository on github.com
2. Click **Settings** (top tab)
3. In the left sidebar click **Pages**
4. Under **Source**, select **Deploy from a branch**
5. Under **Branch**, choose **main** (or master) and folder **/ (root)**
6. Click **Save**
7. Wait 1–2 minutes

GitHub will show you a URL like:
```
https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/
```

---

## Step 3 — Open on iPhone

1. Open Safari on your iPhone
2. Go to the URL above
3. Tap the **Share** button (box with arrow)
4. Tap **Add to Home Screen**
5. Tap **Add**

The app now appears on your home screen like a native app.

---

## Notes

- The app needs internet — it fetches translations from IIT Kanpur and valmikiramayan.net
- Sanskrit text, theme, font size, language mode and bookmarks are all saved locally on your device
- If a sarga takes a moment to load, that is normal — two pages are being fetched and parsed
- The app works on iPhone and iPad in both portrait and landscape

