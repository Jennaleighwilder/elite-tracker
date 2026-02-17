# Deploy The Hidden Networks

## Option 1: Vercel (Recommended)

1. **Push to GitHub** (if not already):
   ```bash
   cd /Users/jenniferwest/elite-tracker
   git init
   git add .
   git commit -m "Hidden Networks tracker"
   git remote add origin https://github.com/YOUR_USERNAME/elite-tracker.git
   git push -u origin main
   ```

2. **Deploy on Vercel**:
   - Go to [vercel.com](https://vercel.com) → New Project
   - Import your GitHub repo
   - **Root Directory**: Leave as repo root (elite-tracker)
   - **Build Command**: `python3 web/build_data.py` (from vercel.json)
   - **Output Directory**: `web` (from vercel.json)
   - Deploy

3. **Or use Vercel CLI**:
   ```bash
   npm i -g vercel
   cd elite-tracker
   vercel
   ```

## Option 2: GitHub Pages

1. Build data first:
   ```bash
   cd elite-tracker
   python3 web/build_data.py
   ```

2. Push the `web` folder to a branch named `gh-pages` or use GitHub Actions. Or:
   - Create a repo with only the web contents
   - Settings → Pages → Source: Deploy from branch
   - Branch: main, Folder: / (root)

## Option 3: Railway

1. Add a `Dockerfile` or `nixpacks.toml` for static serving
2. Or use Railway's static site: point to `web` folder

## Before Deploy

Run to regenerate data:
```bash
cd /Users/jenniferwest/elite-tracker
python3 power_structure_data/extract_all.py   # Full extraction
python3 web/build_data.py                     # Build web data
```

## Local Preview

```bash
cd elite-tracker/web
python3 -m http.server 8080
# Open http://localhost:8080
```
