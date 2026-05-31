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

For Peilu's personal workflow, `build-website` is the source-of-truth repo for original articles and recording scripts. Write articles in `build-website/src/posts/`, write scripts in `build-website/content/video-scripts/`, then run `npm run sync -- <post-slug>` from `build-website`. That syncs the article into this repo's `content.py` and copies matching scripts into `drafts/`.

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

Upload to YouTube as a private video, then review in YouTube Studio before publishing:

```bash
python video.py distribute \
  --article is_the_startup_success_rate_really_that_low \
  --platform youtube \
  --video assets/videos/is_the_startup_success_rate_really_that_low.mov \
  --privacy private
```

YouTube uses the Data API and expects OAuth credentials at `secrets/youtube_client_secrets.json` plus a cached token at `secrets/youtube_token.json`. The `secrets/` directory is ignored by git. TikTok, Xiaohongshu, and Bilibili currently use visible browser-assisted handoffs so the agent can upload safely while you stay logged in.

The detailed editing workflow is captured as a repo-local skill at `skills/talking-head-video-editing/SKILL.md`. It covers rough/fine/polish cuts, section markers, clap/slate removal, repeated takes, subtitle review, HDR-safe subtitle rendering, thumbnail variants, and platform packaging.

## Setup

You can run the project either with a local virtual environment or Docker. Docker is recommended for video processing because it keeps Python dependencies, `ffmpeg`, and system fonts isolated from your machine.

### Docker Setup

Build the image:

```bash
COMPOSE_DISABLE_ENV_FILE=1 docker compose build agent
```

Run a dry compile check inside the container:

```bash
make docker-test
```

Generate video assets inside Docker:

```bash
COMPOSE_DISABLE_ENV_FILE=1 docker compose run --rm agent \
  python video.py prepare \
  --article is_the_startup_success_rate_really_that_low
```

Dry-run a YouTube upload package inside Docker:

```bash
COMPOSE_DISABLE_ENV_FILE=1 docker compose run --rm agent \
  python video.py distribute \
  --article is_the_startup_success_rate_really_that_low_zh \
  --platform youtube \
  --video assets/exports/is_the_startup_success_rate_really_that_low_zh/fine_cut_v3_subtitled_hdr.mp4 \
  --thumbnail assets/thumbnails/generated/is_the_startup_success_rate_really_that_low_zh_youtube_1280x720_v7_bold_title.jpg \
  --privacy private \
  --dry-run
```

Docker is intended for deterministic pipeline work: Python scripts, article/video metadata generation, `ffmpeg`, subtitles, thumbnails, and API-based uploads such as YouTube. Browser-assisted flows that need your local Chrome login state, 2FA, or Computer Use should still run on the host machine.

Use `COMPOSE_DISABLE_ENV_FILE=1` for Docker commands when you do not need `.env`. This prevents Docker Compose from auto-reading local secrets for interpolation. When you need API credentials inside Docker, pass a purpose-built Docker env file explicitly:

```bash
docker compose --env-file docker.env run --rm agent python distribute.py --platform twitter --dry-run
```

Keep `docker.env` local and out of git, just like `.env`.

### Local Setup

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
| YouTube | OAuth files in `secrets/` | Upload defaults to private for review |

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
skills/
  talking-head-video-editing/
    SKILL.md           # reusable creator video editing workflow
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
