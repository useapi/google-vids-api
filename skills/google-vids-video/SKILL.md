---
name: google-vids-video
description: Make AI video in Google Vids with Gemini Omni 1.1 Flash through the useapi.net Google Vids API, on the user's own Google AI plan. Creates talking AI avatars (a person drawn from a description, with one of 30 voices) and puts them in clips as an AI influencer, spokesperson or UGC ad presenter; also text-to-video, reference images, start image, extend a clip up to about 41 seconds, upscale to 1080p, edit by prompt, and Vids images. Downloads the .mp4. Use when the user asks for a Google Vids video, a Gemini Omni or Omni Flash clip, an AI avatar or talking-avatar video, an AI influencer or spokesperson video, a UGC-style ad, or to extend or upscale a Vids clip from the command line. Needs curl, jq and a USEAPI_TOKEN environment variable.
license: MIT
compatibility: Needs bash, curl, jq and network access to api.useapi.net. Requires a useapi.net API token (USEAPI_TOKEN) and a Google account on a paid Google AI plan (Pro or Ultra) connected to useapi.net with the Google Vids setup.
metadata:
  author: useapi.net
  homepage: https://github.com/useapi/google-vids-api
---

# Gemini Omni 1.1 Flash video and AI avatars with the useapi.net Google Vids API

These scripts call the [useapi.net Google Vids API](https://useapi.net/docs/api-google-vids-v1), a third-party REST API that drives the user's own Google Vids account. Every clip spends seconds of the monthly Vids allowance of the user's Google AI plan. Every script is in `scripts/` next to this file. Run them with bash.

## Before you start

1. `USEAPI_TOKEN` must be set. If it is missing, ask the user for their useapi.net API token (setup: https://useapi.net/docs/start-here/setup-useapi). Their Google account must already be connected (https://useapi.net/docs/start-here/setup-google-vids). To connect one by hand, the clean sign-in scripts at https://github.com/useapi/google-account-setup give cookies that keep working. **Never print the token, echo it, or write it to a file.**
2. `USEAPI_EMAIL` is optional: the connected Google account to use. Leave it unset and the API picks a healthy account with allowance left. Avatars, clips and images belong to the account that made them, and everything in one request must come from the same account, so set it when the user has several accounts.
3. `curl` and `jq` must be installed.

## Fastest path: one command

```bash
scripts/video.sh "<prompt>" [key=value ...]
```

It prints progress on stderr and the saved `.mp4` path on stdout, with the job record next to it as `.json` (`OUT_DIR` sets the folder, default the current one). A clip usually takes 30 to 100 seconds; run it in the background (in Claude Code, `run_in_background`) or with a timeout of at least 10 minutes, and do not start a second copy while it runs.

```bash
# Text to video, 8 s landscape 720p (the defaults)
scripts/video.sh "A lighthouse keeper climbs the spiral stairs at dusk, lantern swinging. Slow handheld follow shot."

# A talking avatar for Shorts/Reels/TikTok
AV=$(scripts/avatar.sh "Maya" Kaci appearance="a woman in her late twenties with a curly brown bob and freckles" outfit="cream knit sweater" shot=upper-body)
scripts/video.sh "@avatar_1 holds up the mug, smiles and says: \"Honestly the best coffee I've had all year.\" Handheld phone camera, natural light." \
  avatar_1="$AV" aspectRatio=portrait duration=6
```

## Costs (the Vids allowance)

Vids meters video in **seconds** and images by **count**, per month, separate from Google Flow credits. Google AI Pro gets 500 s, Ultra 5x 2,500 s, Ultra 20x ($199) 10,000 s of video; images 30 / 300 / 1,000. A free Google account gets no video or images (it can still make avatars). Allowances reset on the 1st at 00:00 Pacific.

| Request | Uses |
|---|---|
| A clip (`generate.sh`, `video.sh`) | its `duration` in seconds. **`720p` and `1080p` cost the same.** Avatars and references add nothing |
| Extend (`extend.sh`) | only the seconds it adds, whatever the clip's length |
| Upscale (`upscale.sh`) | the clip's full length again (an 8 s clip uses 8 s) |
| Edit (`edit.sh`) | the length it returns, at most 10 s |
| Image (`image.sh`) | 1 image |
| Avatar from a description | 1 image. From an `image.sh` image: nothing more. Voices are free |
| A request Google refuses (content `422` or quota `429`) | nothing |

Every finished job reports what is left (`result.quota`, logged by `wait-job.sh`). Tell the user the cost before anything over 10 s or more than one clip.

## 720p first, upscale once at the end

A `1080p` clip behaves like an upscaled `720p` one and takes about twice as long. Extending or editing a `1080p` clip makes faces softer and waxier at every step. So:

- Make, extend and edit at `720p` (the default).
- When the clip is finished and is **20 seconds or less**, upscale it once with `upscale.sh`. Longer clips are refused (`400`, nothing charged).
- A single clip that won't be extended or edited can be `resolution=1080p` from the start (same cost).
- For a `1080p` clip longer than 20 s, set `resolution=1080p` on the last extend only.

## Avatars

An avatar is a fixed picture of a person plus one of 30 voices, saved in the account's Vids document and reusable by `avatarId` in any number of clips (`avatar.sh --list` shows them, including ones made in the Vids web app).

- Made **from a description** (`appearance=`, plus `outfit=`, `shot=close-up|upper-body|full-body`, `expression=`, `details=`), where Google draws the person and the picture is saved as `avatar_<name>.jpg`; or **from an image** made with `image.sh` (`image=<mediaId>`, within a few hours of making it).
- **Not from the user's own photo**: an avatar of a real person needs Google's live selfie and phone check, which an API cannot do. Say so if asked, and offer a description instead.
- Voice: `scripts/avatar.sh --voices` lists name, voice id and style (e.g. `Holt` = Charon, informative; `Kaci` = Autonoe, bright). Ask the user or pick one that fits.
- A clip takes **up to 3 references in all**: `avatar_1..3` and `referenceImage_1..3` together. `startImage` can't be combined with them.
- Delete avatars the user no longer wants with `avatar.sh --delete <avatarId>`. Clips already made are not affected.

## Writing prompts that work

- **Name references with markers**: `@avatar_1`, `@referenceImage_1`. Each marker needs its parameter. An avatar's name plays no part in the prompt.
- **Spoken lines go in quotes** after "says:". One or two short sentences per clip of up to 10 s. An avatar speaks in its own voice.
- **Put a prop in a person's hands in the first sentence that mentions them** ("@avatar_1, holding @referenceImage_1 in both hands, ..."). A verb like "lifts" later makes the object appear from nowhere.
- **Say what must not happen**: "his hands are completely empty", "only these three people are on stage".
- **Name the camera**: "static tripod shot", "handheld phone camera, natural light" (reads as real UGC), "wide steady shot".
- **Extend prompts: the new action only, and name people by what they wear.** An extend gets the clip, not the avatars, so `@avatar_1` means nothing there: write "the man in the olive field jacket", "the blonde woman in the cream hoodie". Repeat the setting ("same stage, same wide steady shot").
- On-screen text wavers and can be misspelled in some frames.
- Ask which shape the user wants: `aspectRatio=portrait` for phone video (720×1280, 1080×1920 at 1080p), `landscape` otherwise.

## Step by step (for more control)

```bash
JOB=$(scripts/generate.sh "@avatar_1 waves and says: \"Hi!\"" avatar_1="$AV" duration=5)   # prints the job id
scripts/wait-job.sh "$JOB" > job.json                    # polls every 10 s, prints the final record
scripts/download.sh job.json ./out                       # prints the saved .mp4 path
M=$(jq -r .result.mediaId job.json)                      # the clip, for the next step
J2=$(scripts/extend.sh "$M" "The woman in the cream sweater laughs and sips from the mug." duration=5)
scripts/wait-job.sh "$J2" > ext.json && scripts/download.sh ext.json ./out
J3=$(scripts/upscale.sh "$(jq -r .result.mediaId ext.json)")    # last step, clips of <= 20 s
scripts/wait-job.sh "$J3" > up.json && scripts/download.sh up.json ./out
```

| Script | Interface |
|---|---|
| `video.sh "<prompt>" [key=value ...]` | generate + wait + download, prints the `.mp4` path |
| `generate.sh "<prompt>" [key=value ...]` | `duration=3..10` (default 8), `aspectRatio=landscape\|portrait`, `resolution=720p\|1080p`, `avatar_1..3`, `referenceImage_1..3`, `startImage`, `replyUrl`, `replyRef`; prints the job id |
| `extend.sh <mediaId> "<prompt>" [duration= aspectRatio= resolution=]` | adds 3 to 10 s, returns the whole clip (up to about 41 s); prints the job id |
| `upscale.sh <mediaId>` | 720p clip of up to 20 s to 1080p; prints the job id |
| `edit.sh <mediaId> "<change>" [duration= aspectRatio= resolution=]` | recolour, add an object, restyle; first 10 s only; prints the job id |
| `image.sh "<prompt>" [aspectRatio=16:9\|1:1\|9:16] [style=...]` | one JPEG (about 1 MP), saved to `OUT_DIR`; prints the image `mediaId` |
| `avatar.sh <name> <voice> appearance=... \| image=<mediaId>` | prints the `avatarId`; also `--list`, `--delete <avatarId>`, `--voices` |
| `wait-job.sh <jobid>` | polls until done, prints the job record; exits 1 on a failed job with a hint |
| `download.sh <job.json\|-\|mediaId> [OUT_DIR] [NAME]` | saves `vids_<mode>_<id>.mp4` (or `.jpg`), prints the path |

Every option: https://useapi.net/docs/api-google-vids-v1

**Download soon.** Files live in Google's temporary storage: videos for 24 hours, images for a few hours. Then `GET /media` answers `404`.

## Timeouts and resuming without paying twice

The generation scripts send each request **once and never retry it**: a request resent after an unclear failure could be charged twice. If a run is interrupted after `job j...-bot:google-vids` was logged, do **not** run it again. Resume with the job id:

```bash
scripts/wait-job.sh "<jobid>" > job.json && scripts/download.sh job.json
```

Reading jobs and downloading files is free, so `wait-job.sh` and `download.sh` retry network errors and `5xx` answers on their own and are safe to re-run.

## Errors

Every failed request or failed job prints the API's error and a one-line hint. What matters most is **whether it was charged**:

- `400`: a parameter was rejected (the message names it). Nothing charged. Also: an avatar from a photo, a generated image that expired, an upscale of a clip over 20 s or already 1080p.
- `401`: wrong token. `404`: the account is not connected, the file expired, or the job is older than 15 days.
- `403`: the account's plan has no Vids allowance for this (a free account makes avatars only), or the id belongs to another token. Nothing charged.
- `422`: Google refused the prompt or inputs. **Nothing charged.** Rephrase and try again. (Every edit of an uploaded video ends here.)
- `429`: either the month's allowance is used up (`retryAt` is the reset date: use another account or wait), or the account is busy / briefly rate-limited (`retryAt` about a minute away, or `maxJobs` running): **nothing charged, safe to resend once after `retryAt`**. Never loop on it.
- `502` on a failed job: Google answered without a usable file. **Google may already have charged it.** Do not resubmit automatically; tell the user and report the job id to useapi.net support. (A `502` on creating or deleting an avatar that says "please retry" is safe to try once more.)
- `503`: Google server error. Retry in a minute or two; in rare cases a failed job was still charged, so check the allowance before resubmitting repeatedly.
- `504`: Google did not answer in time. It **may have been made and charged** but cannot be retrieved: ask the user before running it again.
- `596`: the Google account is signed out or being re-checked. Retry in a minute; if it persists, reconnect it: https://useapi.net/docs/start-here/setup-google-vids

## Watermark

Every Vids MP4 carries Google's visible Gemini ✦ sparkle in the bottom-right corner and an invisible SynthID watermark. Images have no visible mark. The [watermark remover](https://github.com/useapi/google-vids-api/tree/main/watermark-remover) in this repo removes the visible ✦ (Python, `numpy`, `ffmpeg`) and leaves SynthID untouched. **It works on clips as generated and on their upscales, not on extended or edited clips**, where the model repaints the star into the picture and a faint diamond stays. To keep a long video clean, remove the mark from each generated clip and join them, rather than extending.

## After it finishes

Tell the user the file path(s), the duration, the resolution and the seconds (or images) it used, plus what `result.quota` says is left. Mention that files expire (videos 24 h) and that avatars stay on the account until deleted.
