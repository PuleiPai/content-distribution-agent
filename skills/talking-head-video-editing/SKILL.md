---
name: talking-head-video-editing
description: Edit creator talking-head recordings into rough, fine, and publish-ready cuts. Use this whenever a user provides a spoken video, raw recording, section markers, claps/slates, long pauses, false starts, repeated takes, filler words, subtitles, thumbnails, or platform upload packaging for YouTube, TikTok, Xiaohongshu, Bilibili, LinkedIn, or X.
metadata:
  short-description: Transcript-guided talking-head editing and platform packaging
---

# Talking-Head Video Editing

Use this workflow for creator videos where the speaker may say section names, clap/slate before sections, pause between segments, repeat a thought until it is correct, or speak more freely than the written script.

## Core Principle

Edit from transcript-guided intent, not silence alone. Silence detection finds candidates; the transcript decides whether a cut is safe.

If the speaker repeats the same idea several times, keep the last complete and correct take unless the user says otherwise.

## Input Convention

Ask the creator to record like this when possible:

- Say the section name before each section.
- Pause for about 2 seconds between sections.
- Use a clap/slate if they want a strong visual/audio marker.
- If they make a mistake, restart the sentence or paragraph and continue.
- If a take should be removed, say a clear discard marker such as `这段剪掉`.

Repository convention:

- Raw videos: `assets/videos/`
- Project exports: `assets/exports/<project_id>/`
- Editable subtitles: `assets/exports/<project_id>/subtitles_zh_review.md` or `.csv`
- Final video: `assets/exports/<project_id>/fine_cut_v3_subtitled_hdr.mp4` when HDR should be preserved

## Standard Passes

### v1 Rough Cut

Goal: remove obvious non-content while preserving the shape of the talk.

Cut:

- recording setup at the beginning and end
- spoken section markers such as `第一段`, `结尾`, `录制段名`
- long pauses between sections
- explicit discard markers such as `这段剪掉`
- fully abandoned starts before a clean retake

Output:

- `rough_cut_v1.mp4`
- `edit_decision_list.md`

### v2 Fine Cut

Goal: improve flow while preserving natural speech.

Cut:

- visible/audible claps or slates around section starts
- repeated false starts where a later version says the same idea better
- isolated wrong words
- small abandoned phrases before a complete sentence
- long dead air inside sections

Do not automatically remove every conversational connector. Words like `就是`, `其实`, `对吧`, `然后`, and `那` are often part of the speaker's rhythm. Remove them only when isolated or clearly part of a restart.

Output:

- `fine_cut_v2.mp4`
- `edit_decision_list_v2.md`

### v3 Polish Cut

Goal: address user review notes and obvious remaining awkwardness.

Common fixes:

- trim the first second if it still contains camera/prep/photo-like behavior before the clean intro
- remove remaining clap motion/sound
- remove safe filler words: isolated `嗯`, `啊`, `呃`
- remove duplicated starts when a clean replacement follows
- tighten cuts after user review

Output:

- `fine_cut_v3.mp4`
- `edit_decision_list_v3.md`

## Tooling

Prefer local tools:

- `ffmpeg` / `ffprobe` for media processing
- `whisper-cpp` or an equivalent local ASR tool for transcript timestamps
- the project virtualenv when Python scripts are needed

Typical setup:

```bash
ffmpeg -i raw.MOV -vn -ac 1 -ar 16000 audio.wav
whisper-cli -m assets/models/ggml-small.bin -f audio.wav -l zh -osrt -otxt -oj -of transcript --print-progress
ffmpeg -i audio.wav -af silencedetect=n=-35dB:d=1.2 -f null - 2> silence.log
```

## Edit Decision Lists

Always write an edit decision list before rendering. Use source timestamps, not output timestamps.

```markdown
# Edit Decision List - <project> <pass>

## Keep Segments

| # | In | Out | Notes |
|---|----|-----|-------|
| 1 | 00:00:08.600 | 00:01:16.040 | Clean intro after clap |

## Removed

- 00:00:00.000-00:00:08.600: setup / clap / prep
```

## Rendering Pattern

Use deterministic source-based cuts with `trim` / `atrim`:

```text
[0:v]trim=start=8.600:end=76.040,setpts=PTS-STARTPTS[v0];
[0:a]atrim=start=8.600:end=76.040,asetpts=PTS-STARTPTS[a0];
[v0][a0]concat=n=1:v=1:a=1[v][a]
```

Then render:

```bash
ffmpeg -y \
  -i raw.MOV \
  -filter_complex_script cut_filter.txt \
  -map '[v]' -map '[a]' \
  -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 160k \
  -movflags +faststart \
  -metadata:s:v:0 rotate=0 \
  output.mp4
```

## Validation

After each render:

- check duration and file size with `ffprobe`
- extract at least one preview frame to verify orientation and framing
- open the output or provide a preview for user review
- mention what changed from the previous cut
- remove old rough exports only after the user agrees they are no longer needed

## Subtitles

Create editable sidecar subtitles before burning them in.

Steps:

- align subtitle timing to the final edited video, not the raw source
- write `subtitles_zh.srt`
- write an editable review copy such as `subtitles_zh_review.md`, `.txt`, or `.csv`
- wait for user approval or explicit "no changes" before burn-in
- optionally write `subtitles_zh.ass` for styled burned-in captions

Chinese caption style:

- keep lines short, usually 12-20 Chinese characters per visual line
- prefer two-line captions over one long line
- remove obvious recognition mistakes before burning in
- avoid covering the speaker's face when a lower safe area is available

## Color Handling

Check source color metadata before subtitle rendering. iPhone recordings may be HDR/HLG/BT.2020.

If the user likes the original color:

- preserve HDR tags
- avoid accidental SDR tone mapping
- render a 10-second subtitle/color sample before full export when color is uncertain

If the user says the color looks strange, compare:

- original color preserved with subtitles
- SDR tone-mapped version
- a short 10-second sample before rendering the whole video

## Thumbnail / Cover

When the user provides a cover image, create platform-ready variants:

- YouTube: `1280x720`
- Bilibili: `1280x960` or another 4:3-safe cover when the platform crops wide covers
- Xiaohongshu/TikTok vertical: `1080x1440` or `1080x1920`
- square fallback: `1080x1080`

Cover rules:

- use the user's supplied image as the primary visual when available
- keep the title short and high-contrast
- keep important text inside platform-safe margins
- do not over-darken the user's image unless requested
- verify with an image preview before finalizing
- For Xiaohongshu web uploads, wait for the intelligent cover thumbnails to finish generating and select the first recommended cover. Do not remove creator-added traffic-support tags such as `#好视频扶持计划`.

## Platform Packaging

Generate metadata per platform:

- YouTube: title, description, tags, category, thumbnail, privacy
- Bilibili: title, 简介, tags, 4:3-safe cover
- Xiaohongshu: title,正文, hashtags, vertical cover
- TikTok: short title/caption, hashtags, vertical cover
- LinkedIn/X: short text posts when useful

Default YouTube behavior:

- upload as `private`
- give the user the YouTube URL and Studio edit URL
- do not publish publicly until the user explicitly confirms

Tone:

- write platform-native copy, not one copied caption everywhere
- preserve the creator's actual argument and wording
- do not overpromise beyond the video content

Save packaging metadata as `metadata.json` or `upload_info.json` under the project asset/export directory.
