# Content Distribution Agent

Automates publishing blog articles from [peiluai.netlify.app](https://peiluai.netlify.app) to Twitter/X, Medium, Substack, and Reddit.

## How it works

Each article in `content.py` holds platform-specific content (tweet thread, Medium import URL, Substack body, Reddit title). Running `distribute.py` publishes to whichever platforms you specify.

```
python distribute.py                        # all articles, all platforms
python distribute.py --article ai_native    # one article
python distribute.py --platform medium      # one platform
python distribute.py --dry-run              # preview without posting
```

## Setup

**1. Clone and create a virtual env**
```bash
git clone https://github.com/PuleiPai/content-distribution-agent.git
cd content-distribution-agent
python -m venv content-distribution-agent
source content-distribution-agent/bin/activate
pip install -r requirements.txt
```

**2. Copy `.env.example` to `.env` and fill in your credentials**
```bash
cp .env.example .env
```

**3. Platform-specific auth**

| Platform | Method | Notes |
|----------|--------|-------|
| Twitter | API keys in `.env` | Requires Basic or Elevated access |
| Substack | Cookie string in `.env` | Set `SUBSTACK_COOKIE_STRING` from browser DevTools |
| Medium | Browser cookies file | Run the login script to save `medium_cookies.json` |
| Reddit | API credentials in `.env` | Create an app at reddit.com/prefs/apps |

### Medium login

Medium uses browser automation ([patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright), an undetected Playwright fork) to bypass bot detection. Install the browser and log in once to save cookies:

```bash
pip install patchright
patchright install chromium
python platforms/medium_login.py   # follow the prompts, saves medium_cookies.json
```

After that, `distribute.py --platform medium` uses the saved cookies automatically.

## Project structure

```
distribute.py          # entry point — orchestrates all platforms
content.py             # article definitions with per-platform content
platforms/
  twitter.py           # tweepy-based thread posting
  medium.py            # patchright browser automation (import + publish flow)
  substack.py          # python-substack API wrapper
  reddit.py            # PRAW-based link posting
drafts/                # Medium markdown source files
.env.example           # credential template (copy to .env)
```

## Adding a new article

Add an entry to `ARTICLES` in `content.py`:

```python
"my_article": {
    "id": "my_article",
    "title": "My Article Title",
    "platforms": {
        "twitter": ["Tweet 1/n ...", "Tweet 2/n ..."],
        "medium": {
            "title": "...",
            "content": "...",
            "tags": ["tag1", "tag2"],
            "canonical_url": "https://peiluai.netlify.app/blog/my-article",
        },
        "substack": {
            "title": "...",
            "subtitle": "...",
            "content": "Markdown content here...",
        },
        "reddit": {
            "title": "...",
            "url": "https://peiluai.netlify.app/blog/my-article",
        },
    },
    "reddit_subreddits": ["MachineLearning", "artificial"],
}
```
