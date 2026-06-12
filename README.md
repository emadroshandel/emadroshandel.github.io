# Emad Roshandel — Personal Portfolio Website

A fully animated, AI-powered personal academic portfolio hosted on GitHub Pages with a Netlify serverless backend. This README documents the complete build process, architecture, code structure, and all lessons learned during development.

---

## 🌐 Live Sites

| Platform | URL | Purpose |
|---|---|---|
| GitHub Pages | https://emadroshandel.github.io | Main public site |
| Netlify | https://bright-donut-72d55d.netlify.app | AI proxy backend |
| Google Site | https://sites.google.com/site/emadroshandel | Content pages |

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
      Netlify Function (https://bright-donut-72d55d.netlify.app/.netlify/functions/claude)
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
  // Sends message history + system prompt to Netlify absolute URL
  // IMPORTANT: must use absolute URL, not relative path
  // Relative path (/.netlify/functions/claude) only works when
  // the page is hosted ON Netlify — not on GitHub Pages
  const res = await fetch('https://bright-donut-72d55d.netlify.app/.netlify/functions/claude', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages: history, system: PROFILE_CONTEXT })
  });
  // Displays typing indicator while waiting
  // Streams reply character by character (12ms/char typewriter effect)
  // Maintains last 10 messages of history for context
}
```

#### Profile image URL:
```
https://raw.githubusercontent.com/emadroshandel/emadroshandel.github.io/main/profile.JPG
```
> ⚠️ **Important:** Always use `raw.githubusercontent.com` for direct image URLs. The standard `github.com/blob/` URL is a viewer page, not a direct image link, and will not render in HTML.

---

### 2. `netlify/functions/claude.js`

A Netlify serverless function acting as a secure proxy between the frontend and the Google Gemini API. This prevents the API key from being exposed in client-side code.

```javascript
exports.handler = async function(event) {

  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Content-Type': 'application/json'
  };

  // CRITICAL: Handle preflight OPTIONS request
  // Browsers always send OPTIONS before POST when calling cross-origin APIs
  // Without this, the browser blocks the request before it even reaches the API
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, headers, body: 'Method Not Allowed' };
  }

  // Convert chat history to Gemini format
  // Gemini uses 'model' instead of 'assistant'
  // Gemini uses parts:[{text}] instead of plain content string
  const geminiMessages = messages.map(m => ({
    role: m.role === 'assistant' ? 'model' : 'user',
    parts: [{ text: m.content }]
  }));

  // Call Gemini API with API key from environment variable
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${process.env.GEMINI_API_KEY}`,
    { ... }
  );
};
```

> ⚠️ **Critical CORS lesson:** The `OPTIONS` preflight handler is mandatory for any cross-origin function call. Without it, the browser sends a preflight check that returns `405 Method Not Allowed`, which kills the request entirely and shows a CORS error — even if `Access-Control-Allow-Origin: *` is set.

**Gemini model used:** `gemini-2.5-flash` (free tier)

> ⚠️ **Model name lessons learned:**
> - `gemini-2.0-flash` → quota limit 0 in some regions
> - `gemini-1.5-flash` → returns 404 (deprecated/moved)
> - `gemini-2.5-flash` → ✅ works on free tier as of June 2026

---

### 3. `netlify.toml`

Tells Netlify where to find the serverless functions:

```toml
[build]
  functions = "netlify/functions"
```

> Without this file, Netlify may not detect the functions folder automatically.

---

### 4. `scholar.py`

Python script run by GitHub Actions to scrape Google Scholar and update `scholar.json`. Uses two methods with automatic fallback:

**Method 1 — scholarly with free proxies:**
```python
from scholarly import scholarly, ProxyGenerator
pg = ProxyGenerator()
pg.FreeProxies()
scholarly.use_proxy(pg)
author = scholarly.search_author_id('d1Wqu9wAAAAJ')
author = scholarly.fill(author, sections=['basics', 'indices', 'counts'])
```

**Method 2 — direct scrape fallback:**
```python
# Randomised User-Agent headers to avoid bot detection
# Parses citation stats and yearly bar chart from HTML
# Polite random delay (2-5 seconds) before request
```

**Graceful failure:**
```python
# If both methods fail, exits with code 0
# This keeps the workflow green and preserves existing scholar.json
# Never overwrites good data with empty/failed data
```

> ⚠️ **scholarly lesson:** Google actively blocks automated requests. Free proxies are required. Even with proxies, the workflow may occasionally fail — the graceful exit with code 0 prevents false alarm failure emails.

---

### 5. `.github/workflows/update_scholar.yml`

GitHub Actions workflow that runs `scholar.py` every day at 6am UTC:

```yaml
name: Update Scholar Stats
on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:        # can also be triggered manually

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - name: Install dependencies
        run: pip install scholarly requests fp
      - name: Run scholar script
        run: python scholar.py
        timeout-minutes: 10
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

### Netlify (Project configuration → Environment variables)

| Key | Value | Notes |
|---|---|---|
| `GEMINI_API_KEY` | `AIza...` | Google Gemini API key, marked as secret |

> ⚠️ **Lesson learned:** When adding the variable, tick **"Contains secret values"** and use **"Same value for all deploy contexts"** — do not use "Different value for each deploy context" as that creates separate values per environment which is confusing and error-prone.

---

## 🚀 Deployment

### GitHub Pages
- Repo must be **public** (private repos require paid GitHub plan for Pages)
- Go to Settings → Pages → Branch: `main`, folder: `/root`
- Site auto-deploys on every commit to `main`
- Updates typically live within **1–3 minutes**
- Hard refresh to see changes: `Ctrl+Shift+R` (Windows) / `Cmd+Shift+R` (Mac)

### Netlify
- Connected to the same GitHub repo via GitHub integration
- Auto-deploys on every commit to `main`
- Serverless functions deployed automatically from `netlify/functions/`
- Free plan: **300 build credits/month**
- Most credits consumed by code deploys — not by function calls
- Initial setup phase uses most credits; stable site uses very few
- AI function calls cost negligible credits (~0.001 per call)

> ⚠️ **Deploy conservation tip:** Before committing, batch all changes into one commit rather than committing file by file. Each commit triggers one Netlify deploy.

---

## 🤖 AI Research Assistant

Powered by **Google Gemini 2.5 Flash** (free tier: 1,500 requests/day, no credit card).

**System prompt context includes:**
- PhD credentials and affiliations
- Full career history (Shiraz → Isfahan → Eram Sanat → Flinders → Infusion Innovations)
- Research specialisations and tools
- Key projects (axial flux motor, IPMSM, MFL device, pipe inspection app, etc.)
- Publication count and citation metrics
- All awards and honours
- Teaching experience at Flinders University

**Response length:** controlled by two settings:
```javascript
// In claude.js:
generationConfig: { maxOutputTokens: 300 }  // increase for longer answers

// In index.html PROFILE_CONTEXT:
"Keep answers under 120 words."  // change to 250 for longer answers
```

**Conversation history:** last 10 messages retained for context continuity.

---

## 💡 AI API Journey — Lessons Learned

We tried several AI APIs before finding a working free solution:

| API | Result | Reason |
|---|---|---|
| Anthropic Claude | ❌ | No free tier — requires billing |
| DeepSeek | ❌ | "Insufficient Balance" — free credit exhausted immediately |
| Gemini 2.0 Flash | ❌ | Quota limit 0 in region |
| Gemini 1.5 Flash | ❌ | Model deprecated / returns 404 |
| **Gemini 2.5 Flash** | ✅ | Free tier, 1,500 req/day, works perfectly |

**Alternative free options if Gemini stops working:**
- **Groq** — [console.groq.com](https://console.groq.com) — Llama 3, very fast, generous free tier
- **OpenRouter** — [openrouter.ai](https://openrouter.ai) — aggregates free models

---

## 🎨 Google Sites Theme

A matching dark theme applied to the Google Site to visually connect it with the GitHub Pages site:

| Element | Value |
|---|---|
| Background | `#07091A` |
| Surface / Header | `#0D1128` |
| Primary / Buttons | `#378ADD` |
| Heading text | `#E8F0FE` |
| Body text | `#7A9CC0` |
| Heading font | Lexend Mega |
| Body font | Lexend Giga |

A custom SVG banner (1600×400px) with circuit-board aesthetic was created for the Google Sites header image.

---

## 🔧 Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| Profile photo not showing | Using GitHub blob viewer URL | Use `raw.githubusercontent.com/...` URL instead |
| AI says "Connection error" | Relative URL used instead of absolute | Change `/.netlify/functions/claude` to full Netlify URL |
| AI says "Connection error" | Missing OPTIONS preflight handler | Add `if (event.httpMethod === 'OPTIONS')` handler in `claude.js` |
| AI says "No response" | Wrong Gemini model name | Use `gemini-2.5-flash` not `gemini-2.0-flash` or `gemini-1.5-flash` |
| AI says "Insufficient Balance" | DeepSeek/paid API ran out of credit | Switch to Gemini free tier |
| Scholar stats show dashes | `scholar.json` not generated yet | Run GitHub Action manually from Actions tab |
| Scholar workflow fails | Google blocking scholarly scraper | Script has automatic fallback; exit 0 preserves existing data |
| Site not updating | Browser cache | Hard refresh: `Ctrl+Shift+R` / `Cmd+Shift+R` |
| Netlify function 404 | Wrong file path or missing `netlify.toml` | Ensure path is `netlify/functions/claude.js` and `netlify.toml` exists |
| CORS error in browser console | Missing OPTIONS handler or wrong origin | Set `Access-Control-Allow-Origin: *` and handle OPTIONS requests |
| Google Drive image not loading | CORS policy blocks cross-origin image loads | Host image in GitHub repo and use `raw.githubusercontent.com` URL |
| Netlify env variable wrong | Typed name instead of API key | Key must start with `sk-` (DeepSeek) or `AIza` (Gemini) |

---

## 📦 Dependencies & Costs

| Tool | Purpose | Cost |
|---|---|---|
| GitHub Pages | Static site hosting | Free |
| Netlify | Serverless function proxy | Free (300 credits/month) |
| Google Gemini API | AI research assistant | Free (1,500 req/day) |
| scholarly (Python) | Google Scholar scraping | Free |
| Google Fonts (Inter) | Typography | Free |
| GitHub Actions | Daily scholar stats update | Free |

**Total monthly cost: $0** 🎉

---

## 👤 Author

**Emad Roshandel**
- 🌐 [emadroshandel.github.io](https://emadroshandel.github.io)
- 🔬 [Google Scholar](https://scholar.google.com/citations?user=d1Wqu9wAAAAJ)
- 💼 [LinkedIn](https://www.linkedin.com/in/emad-roshandel-76875a187/)
- 🔗 [ResearchGate](https://www.researchgate.net/profile/Emad-Roshandel)
- 🏛️ [Google Site](https://sites.google.com/site/emadroshandel)

