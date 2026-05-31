# Content Distribution Agent

Automates publishing blog articles from [peiluai.netlify.app](https://peiluai.netlify.app) to Twitter/X, LinkedIn, Medium, Substack, and Reddit.
It also prepares article-derived video assets for YouTube, TikTok, Xiaohongshu, and Bilibili.

## How it works

Each article in `content.py` holds platform-specific content (tweet thread, LinkedIn draft, Medium import URL, Substack body, Reddit title). Running `distribute.py` publishes to whichever platforms you specify.

```
python distribute.py                        # all articles, working platforms
python distribute.py --article ai_native    # one article
python distribute.py --platform medium      # one platform
python distribute.py --dry-run              # preview without posting
```

By default, `all` runs the working stack: Twitter/X, LinkedIn, Medium, and Substack. Reddit remains available with `--platform reddit` once API access is approved.

## Video workflow

The video pipeline turns the same article entry in `content.py` into recording scripts, platform descriptions, captions, and upload metadata. The intended flow is:

1. Generate the video assets.
2. Record/edit the video manually or with your preferred editor.
3. Put the finished `.mp4`/`.mov` under `assets/videos/`.
4. Distribute to YouTube by API, or open browser-assisted upload flows for TikTok, Xiaohongshu, and Bilibili.

Generate a script and platform metadata:

```bash
python video.py prepare --article is_the_startup_success_rate_really_that_low
```

Generate thumbnails too, if you already have a base image:

```bash
python video.py prepare \
  --article is_the_startup_success_rate_really_that_low \
  --thumbnail-base /path/to/base-image.jpg
```

After recording, dry-run distribution:

```bash
python video.py distribute \
  --article is_the_startup_success_rate_really_that_low \
  --platform all \
  --video assets/videos/is_the_startup_success_rate_really_that_low.mov \
  --dry-run
```

YouTube uses API upload and expects OAuth credentials at `secrets/youtube_client_secrets.json`. TikTok, Xiaohongshu, and Bilibili currently use visible browser-assisted handoffs so the agent can upload safely while you stay logged in.

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
| LinkedIn | Visible browser handoff | Copies a draft, opens Chrome, then use Computer Use to click through |
| Substack | Cookie string in `.env` | Set `SUBSTACK_COOKIE_STRING` from browser DevTools |
| Medium | Browser cookies file | Run the login script to save `medium_cookies.json` |
| Reddit | API credentials in `.env` | Create an app at reddit.com/prefs/apps |

### LinkedIn posting

LinkedIn is handled as a visible browser-assisted step because the public API is restricted for personal feed publishing. The agent prepares a limited-length post, copies it to your clipboard, opens LinkedIn in Chrome, and prints the exact Computer Use handoff.

```bash
python distribute.py --article is_the_startup_success_rate_really_that_low --platform linkedin
```

The draft source order is:

1. `content.py` under `article["platforms"]["linkedin"]["content"]`
2. `drafts/linkedin_<article_id>.txt`
3. A generated excerpt from the article's Substack body plus the canonical URL

The generated draft is saved back to `drafts/linkedin_<article_id>.txt`. It is ASCII-normalized by default to avoid browser clipboard encoding glitches.

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
  linkedin.py          # browser-assisted LinkedIn posting handoff
  medium.py            # patchright browser automation (import + publish flow)
  substack.py          # python-substack API wrapper
  reddit.py            # PRAW-based link posting
video.py               # video asset generation and distribution entry point
video/
  assets.py            # article -> video script/metadata/captions
  generate_thumbnail.py
video_platforms/
  youtube.py           # YouTube Data API upload
  browser_assisted.py  # TikTok/Xiaohongshu/Bilibili upload runbooks
drafts/                # Medium and LinkedIn draft files
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
        "linkedin": {
            "content": "LinkedIn post text here...",
        },
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
