# Emad Roshandel — Personal Portfolio Website

A fully animated, AI-powered personal academic portfolio hosted on GitHub Pages and enhanced via Netlify Functions. This README documents the complete build process, architecture, and code structure for reference.

---

## 🌐 Live Sites

| Platform | URL |
|---|---|
| GitHub Pages | https://emadroshandel.github.io |
| Netlify (AI proxy) | https://bright-donut-72d55d.netlify.app |
| Google Site (content) | https://sites.google.com/site/emadroshandel |

---

## 📁 Repository Structure

```
emadroshandel.github.io/
├── index.html                  # Main landing page
├── profile.JPG                 # Profile photo
├── scholar.json                # Auto-generated Google Scholar stats
├── scholar.py                  # Python script to fetch Scholar data
├── netlify.toml                # Netlify build configuration
├── netlify/
│   └── functions/
│       └── claude.js           # Serverless proxy for Gemini AI API
└── .github/
    └── workflows/
        └── update_scholar.yml  # GitHub Action to auto-update scholar.json
```

---

## 🏗️ Architecture Overview

```
Visitor
  │
  ▼
GitHub Pages (index.html)
  │
  ├── Static content: hero, timeline, awards, scholar chart
  │
  ├── scholar.json ◄── GitHub Actions (daily auto-update via scholarly)
  │
  └── AI Chat Widget
        │
        ▼
      Netlify Function (/.netlify/functions/claude)
        │
        ▼
      Google Gemini API (gemini-2.5-flash, free tier)
```

---

## 📄 File Details

### 1. `index.html`

The main landing page. A single self-contained HTML file with embedded CSS and JavaScript. No external frameworks or build tools required.

#### Sections:
- **Hero** — animated particle network background, profile photo with spinning gradient ring, typewriter animation, stat pills, research tags, navigation buttons, social icons
- **Career Timeline** — horizontal strip showing academic and professional milestones
- **Honours & Awards** — card grid of all awards
- **Google Scholar Stats** — citation metrics with animated count-up and bar chart, auto-loaded from `scholar.json`
- **AI Research Assistant** — chat widget powered by Google Gemini via Netlify proxy

#### Key CSS variables:
```css
:root {
  --bg: #07091a;        /* dark navy background */
  --bg2: #0d1128;       /* slightly lighter navy for sections */
  --accent: #378ADD;    /* blue accent */
  --accent2: #1D9E75;   /* green accent */
  --muted: #7a9cc0;     /* muted text */
  --border: rgba(55,138,221,0.18); /* subtle border */
}
```

#### Particle canvas animation:
```javascript
// 80 floating particles with connecting lines when within 130px
// Subtle engineering grid overlay at 60px spacing
// Runs on requestAnimationFrame for smooth 60fps animation
```

#### Typewriter animation:
```javascript
const lines = [
  'Power Electronics Engineer',
  'Ph.D. — Flinders University',
  'R&D Lead at Infusion Innovations',
  '533 Citations · h-index 12',
  'Electric Machine Designer',
  'Medical Device Innovator'
];
// Types forward at 70ms/char, deletes at 40ms/char, pauses 2s at end
```

#### Scholar stats loader:
```javascript
// Tries to fetch scholar.json first (live data)
// Falls back to hardcoded values if file missing or fetch fails
// Animates numbers counting up on load
// Renders citation-per-year bar chart dynamically
```

#### AI chat sendMsg function:
```javascript
async function sendMsg() {
  // Sends message history + system prompt to Netlify proxy
  // Displays typing indicator while waiting
  // Streams reply character by character (12ms/char typewriter effect)
  // Maintains last 10 messages of history for context
}
```

#### Profile image URL:
```
https://raw.githubusercontent.com/emadroshandel/emadroshandel.github.io/main/profile.JPG
```
> **Note:** Always use `raw.githubusercontent.com` for direct image URLs from GitHub repos, not the standard `github.com/blob/` viewer URL.

---

### 2. `netlify/functions/claude.js`

A Netlify serverless function acting as a secure proxy between the frontend and the Google Gemini API. This prevents the API key from being exposed in client-side code.

```javascript
exports.handler = async function(event) {
  // Only accepts POST requests
  // CORS restricted to allowed origins only
  // Reads GEMINI_API_KEY from Netlify environment variables
  // Converts chat history to Gemini message format
  // Calls gemini-2.5-flash model (free tier)
  // Returns { reply: "..." } JSON response
};
```

**Allowed origins:**
```javascript
const allowedOrigins = [
  'https://emadroshandel.github.io',
  'https://bright-donut-72d55d.netlify.app'
];
```

**Gemini API endpoint used:**
```
https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
```

**Message format conversion** (Anthropic → Gemini):
```javascript
// Gemini uses 'model' instead of 'assistant' for role
// Gemini uses parts:[{text}] instead of content string
const geminiMessages = messages.map(m => ({
  role: m.role === 'assistant' ? 'model' : 'user',
  parts: [{ text: m.content }]
}));
```

---

### 3. `netlify.toml`

Tells Netlify where to find the serverless functions:

```toml
[build]
  functions = "netlify/functions"
```

---

### 4. `scholar.py`

Python script run by GitHub Actions to scrape Google Scholar and update `scholar.json`:

```python
from scholarly import scholarly
import json

author = scholarly.search_author_id('d1Wqu9wAAAAJ')
author = scholarly.fill(author, sections=['basics', 'indices'])

data = {
    "citations": author['citedby'],
    "h_index": author['hindex'],
    "i10_index": author['i10index'],
    "citations_since": author['citedby5y'],
    "h_index_since": author['hindex5y'],
    "i10_index_since": author['i10index5y'],
}

with open('scholar.json', 'w') as f:
    json.dump(data, f)
```

---

### 5. `.github/workflows/update_scholar.yml`

GitHub Actions workflow that runs `scholar.py` every day at 6am UTC and commits the updated `scholar.json` back to the repo:

```yaml
name: Update Scholar Stats
on:
  schedule:
    - cron: '0 6 * * *'   # runs daily at 6am UTC
  workflow_dispatch:        # can also be triggered manually

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - run: pip install scholarly
      - run: python scholar.py
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "Auto-update scholar stats"
```

**To trigger manually:**
1. Go to GitHub repo → Actions tab
2. Click **Update Scholar Stats**
3. Click **Run workflow**

---

## ⚙️ Environment Variables

### Netlify (set in Project configuration → Environment variables)

| Key | Value | Notes |
|---|---|---|
| `GEMINI_API_KEY` | `sk-...` | Google Gemini API key, marked as secret |

### GitHub Actions
No secrets needed — `scholarly` scrapes public Google Scholar data.

---

## 🚀 Deployment

### GitHub Pages
- Repo must be **public**
- Go to Settings → Pages → Branch: `main`, folder: `/root`
- Site auto-deploys on every commit to `main`
- Profile image served at: `https://raw.githubusercontent.com/emadroshandel/emadroshandel.github.io/main/profile.JPG`

### Netlify
- Connected to the same GitHub repo
- Auto-deploys on every commit to `main`
- Serverless functions deployed automatically from `netlify/functions/`
- Free plan: 300 build credits/month (mostly consumed by deploys, not function calls)
- AI function calls cost negligible credits (~0.001 per call)

---

## 🤖 AI Research Assistant

The AI chat widget is powered by **Google Gemini 2.5 Flash** (free tier: 1,500 requests/day).

**System prompt context includes:**
- PhD credentials and affiliations
- Full career history
- Research specialisations
- Key projects (axial flux motor, IPMSM, MFL device, etc.)
- Publication count and citation metrics
- All awards and honours
- Teaching experience

**Suggestion buttons** provide quick-start prompts for visitors.

**Conversation history** — last 10 messages retained for context continuity.

---

## 🎨 Google Sites Theme

A matching dark theme was applied to the Google Site:

| Element | Value |
|---|---|
| Background | `#07091A` |
| Surface / Header | `#0D1128` |
| Primary / Buttons | `#378ADD` |
| Heading text | `#E8F0FE` |
| Body text | `#7A9CC0` |
| Heading font | Lexend Mega |
| Body font | Lexend Giga |

A custom SVG banner (1600×400px) was created with circuit-board aesthetic matching the GitHub Pages site, for use as the Google Sites header image.

---

## 🔧 Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| Profile photo not showing | Using GitHub blob URL | Use `raw.githubusercontent.com` URL |
| AI says "Connection error" | API key missing or function not found | Check Netlify env vars and function path |
| AI says "No response" | Wrong API key or model name | Verify key and model string in `claude.js` |
| Scholar stats show dashes | `scholar.json` not generated yet | Run GitHub Action manually |
| Site not updating | Browser cache | Hard refresh: `Ctrl+Shift+R` / `Cmd+Shift+R` |
| Netlify function 404 | Wrong file path | Must be at `netlify/functions/claude.js` |
| Gemini quota exceeded | Wrong model name | Use `gemini-2.5-flash` not `gemini-2.0-flash` |

---

## 📦 Dependencies

| Tool | Purpose | Cost |
|---|---|---|
| GitHub Pages | Static site hosting | Free |
| Netlify | Serverless function proxy | Free (300 credits/month) |
| Google Gemini API | AI research assistant | Free (1,500 req/day) |
| scholarly (Python) | Google Scholar scraping | Free |
| Google Fonts (Inter) | Typography | Free |
| GitHub Actions | Daily scholar stats update | Free |

**Total monthly cost: $0**

---

## 👤 Author

**Emad Roshandel**
- 🌐 [emadroshandel.github.io](https://emadroshandel.github.io)
- 🔬 [Google Scholar](https://scholar.google.com/citations?user=d1Wqu9wAAAAJ)
- 💼 [LinkedIn](https://www.linkedin.com/in/emad-roshandel-76875a187/)
- 🔗 [ResearchGate](https://www.researchgate.net/profile/Emad-Roshandel)
- 🏛️ [Google Site](https://sites.google.com/site/emadroshandel)

