# Emad Roshandel — Personal Academic Portfolio Website

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

Python script run by GitHub Actions to fetch citation data via **SerpApi's Google Scholar Author API** (after `scholarly` and direct scraping both proved unreliable — see lessons below):

```python
def fetch_with_serpapi():
    """Fetch citation data via SerpApi's Google Scholar Author endpoint."""
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_scholar_author",
        "author_id": "d1Wqu9wAAAAJ",
        "api_key": SERPAPI_KEY
    }
    resp = requests.get(url, params=params, timeout=30)
    result = resp.json()

    # SerpApi returns "table" as a list of single-key dicts:
    # [ {"citations": {"all": 535, "since_2021": 478}},
    #   {"h_index":   {"all": 12,  "since_2021": 11}},
    #   {"i10_index": {"all": 13,  "since_2021": 11}} ]
    # Build a flat lookup keyed by stat name rather than relying on index order —
    # this is more robust if SerpApi changes the order or omits an entry.
    table = result.get("cited_by", {}).get("table", [])
    stats = {}
    for entry in table:
        for key, val in entry.items():
            stats[key] = val

    def get_all(key):   return stats.get(key, {}).get("all", 0)
    def get_since(key): return stats.get(key, {}).get("since_2021", 0)

    data = {
        "citations":       get_all("citations"),
        "citations_since": get_since("citations"),
        "h_index":         get_all("h_index"),
        "h_index_since":   get_since("h_index"),
        "i10_index":       get_all("i10_index"),
        "i10_index_since": get_since("i10_index"),
        "yearly": {str(p["year"]): p["citations"] for p in result["cited_by"]["graph"]}
    }
    return data
```

**Graceful failure:** if SerpApi fails for any reason, the script exits with code `0` and leaves the existing `scholar.json` untouched, so the live site is never broken by a failed fetch.

> ⚠️ **Parsing lesson:** Don't assume API response structures from memory or guesswork — always fetch one real raw response and inspect it directly before writing parsing code. An earlier version assumed a `"value"` wrapper key that didn't exist, and a later version assumed fixed table index positions matched fixed stat names, which happened to work but was fragile. Building a name-keyed lookup dict is more robust than positional indexing for list-of-single-key-dict API shapes.

---

### 5. `.github/workflows/update_scholar.yml`

GitHub Actions workflow that runs `scholar.py` every day at 6am UTC:

```yaml
name: Update Scholar Stats
on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:        # allows manual triggering from the Actions tab

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - name: Install dependencies
        run: pip install requests
      - name: Run scholar script
        run: python scholar.py
        timeout-minutes: 10
        env:
          SERPAPI_KEY: ${{ secrets.SERPAPI_KEY }}
      - name: Commit updated scholar.json
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "Auto-update scholar stats"
          push_options: '--force'
          skip_fetch: true
```

**Key settings explained:**
- `push_options: '--force'` — overwrites remote history for this auto-generated file; safe here since nothing else should be editing `scholar.json` concurrently
- `skip_fetch: true` — skips the action's internal `git fetch`/divergence check entirely, avoiding "non-fast-forward" rejections caused by the repo having moved on (e.g. from GitHub Pages deploy commits) since the job's checkout

**To trigger manually:**
1. Go to GitHub repo → **Actions** tab
2. Click **"Update Scholar Stats"** in the left sidebar (not "All workflows")
3. Click **"Run workflow"** (creates a fresh run using the current file on `main`)

> ⚠️ **Critical lesson — "Re-run jobs" vs "Run workflow":** These are NOT the same thing. **"Re-run jobs"** on an existing run replays that run's *frozen snapshot* of the workflow file from whatever commit it originally used — it will NOT pick up any subsequent edits to the `.yml` file, even if they were committed. **"Run workflow"** (found by clicking the specific workflow name in the sidebar, not "All workflows") creates a brand new run that reads the current file on the branch. If your fixes don't seem to take effect no matter what you change, check whether you've been clicking "Re-run jobs" on a stale run — this cost significant debugging time in this project.

---

## ⚙️ Environment Variables

### Netlify (Project configuration → Environment variables)

| Key | Value | Notes |
|---|---|---|
| `GEMINI_API_KEY` | `AIza...` | Google Gemini API key, marked as secret |

### GitHub Actions (Settings → Secrets and variables → Actions)

| Key | Value | Notes |
|---|---|---|
| `SERPAPI_KEY` | `sk-...` | SerpApi key for Google Scholar Author endpoint |

> ⚠️ **Lesson learned:** When adding environment variables, tick **"Contains secret values"** and use **"Same value for all deploy contexts"** — do not use "Different value for each deploy context" as that creates separate values per environment which is confusing and error-prone. Also double check you're pasting the actual key value, not a placeholder or label — an earlier mistake involved typing descriptive names like "EmadIntro" into the value field instead of the real API key.

### GitHub Actions — Workflow permissions
For any workflow that commits/pushes changes back to the repo (like `update_scholar.yml`), the repository needs write permission granted:
1. Repo → **Settings** → **Actions** → **General**
2. Scroll to **"Workflow permissions"**
3. Select **"Read and write permissions"**
4. Click **Save**

Without this, commits succeed locally in the runner but the push is rejected with a `403 Permission denied` error.

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
- When credits run out mid-cycle, Netlify grants 30 grace credits to keep the **live site** serving traffic, but blocks new **production deploys** until the billing cycle resets — already-deployed code keeps working fine, you just can't ship changes to it until renewal

> ⚠️ **Deploy conservation tip:** Before committing, batch all changes into one commit rather than committing file by file. Each commit triggers one Netlify deploy. GitHub Actions / GitHub Pages changes (like `scholar.py` or `index.html`) do NOT consume Netlify credits — only changes that trigger a Netlify build do (primarily `netlify/functions/` and Netlify-specific config). This means scholar-fetching debugging can be iterated on freely without any Netlify cost.

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
| Scholar workflow "succeeds" but data never changes | Script catches errors and exits 0 silently | Check the actual step logs, not just the green checkmark — "success" can mean "failed gracefully and did nothing" |
| Scholar workflow fails with `scholarly` proxy error | `Client.__init__() got an unexpected keyword argument 'proxies'` — library version mismatch | Abandon `scholarly`; use a dedicated API like SerpApi instead |
| Scholar workflow fails with `403 Forbidden` | Google Scholar blocks cloud/datacenter IP ranges (GitHub Actions, AWS, etc.) | Use SerpApi or similar service that handles this server-side |
| Scholar workflow fails to push: `403 ... denied to github-actions[bot]` | Default `GITHUB_TOKEN` lacks write permission | Settings → Actions → General → Workflow permissions → "Read and write permissions" |
| Scholar workflow fails to push: `non-fast-forward` rejected | Branch diverged between checkout and push (e.g. a Pages deploy committed in between) | Add `skip_fetch: true` and `push_options: '--force'` to the commit action |
| Scholar stats show 0 for citations/h-index/i10-index but correct "_since" values | Wrong key assumed in API response parsing (e.g. assumed `"value"` key that doesn't exist) | Fetch one real raw API response and inspect actual structure before writing parsing code; prefer name-keyed lookups over positional indexing |
| Edited code but the fix "didn't work" no matter what | Forgot to click "Commit changes" after editing in GitHub's web editor, or kept re-running an old workflow run | Always verify the live file content on GitHub after editing; use "Run workflow" for a fresh run, not "Re-run jobs" on an old one |
| Site not updating | Browser cache | Hard refresh: `Ctrl+Shift+R` / `Cmd+Shift+R` |
| Netlify function 404 | Wrong file path or missing `netlify.toml` | Ensure path is `netlify/functions/claude.js` and `netlify.toml` exists |
| CORS error in browser console | Missing OPTIONS handler or wrong origin | Set `Access-Control-Allow-Origin: *` and handle OPTIONS requests |
| Google Drive image not loading | CORS policy blocks cross-origin image loads | Host image in GitHub repo and use `raw.githubusercontent.com` URL |
| Netlify env variable wrong | Typed name instead of API key | Key must start with `sk-` (DeepSeek) or `AIza` (Gemini) |
| Netlify "production deploys paused" email | Monthly build credit allowance (300) exhausted | Live site keeps working via 30 grace credits; just avoid further Netlify-triggering commits until billing cycle resets |

---

## 📦 Dependencies & Costs

| Tool | Purpose | Cost |
|---|---|---|
| GitHub Pages | Static site hosting | Free |
| Netlify | Serverless function proxy | Free (300 credits/month) |
| Google Gemini API | AI research assistant | Free (1,500 req/day) |
| SerpApi | Google Scholar data fetching | Free (100 searches/month, ~30 used) |
| Google Fonts (Inter) | Typography | Free |
| GitHub Actions | Daily scholar stats update | Free |

**Total monthly cost: $0** 🎉

---

## 👤 Author

**Dr. Emad Roshandel** — R&D Lead, Infusion Innovations Pty Ltd · Adelaide, Australia

- 🌐 [emadroshandel.github.io](https://emadroshandel.github.io)
- 🔬 [Google Scholar](https://scholar.google.com/citations?user=d1Wqu9wAAAAJ)
- 💼 [LinkedIn](https://www.linkedin.com/in/emad-roshandel-76875a187/)
- 🔗 [ResearchGate](https://www.researchgate.net/profile/Emad-Roshandel)
- 🏛️ [Google Site](https://sites.google.com/site/emadroshandel)
- 💻 [GitHub](https://github.com/emadroshandel)
