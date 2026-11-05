# Talking avatar from a photo, and speech — Google Vids API (Node.js & Python)

Full walkthrough: [How to Make AI Influencer Videos with Avatars via the Google Vids API › A talking avatar from a photo](https://useapi.net/docs/articles/google-vids-influencer-avatars?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#a-talking-avatar-from-a-photo) — October 7, 2026 (November 4, 2026)

Release post with the same requests and their results: [Google Vids: 30-Second Talking Avatars from a Photo, and Text to Speech](https://useapi.net/blog/261104?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)

Turn a photo into a voiced avatar and have it read your script, through the [Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) by [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api): a 1280×720 talking-head video with sound and lip sync, as long as the speech, up to 30 seconds. A second script reads a text of up to 2,500 characters as speech on its own, in any of the 30 Gemini voices.

| Script | What it does |
|---|---|
| `talking-avatar.mjs` / `talking-avatar.py` | Uploads your photo with [`POST /assets`](https://useapi.net/docs/api-google-vids-v1/post-google-vids-assets?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api), makes an avatar from it with [`POST /avatars`](https://useapi.net/docs/api-google-vids-v1/post-google-vids-avatars?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) (`image` + `refine` + `name` + `voice`), then has the avatar read the script with [`POST /videos/avatar`](https://useapi.net/docs/api-google-vids-v1/post-google-vids-videos-avatar?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) as an async job (`async: true`), polls [`GET /jobs/{jobid}`](https://useapi.net/docs/api-google-vids-v1/get-google-vids-jobs-jobid?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) every 10 seconds and downloads the MP4 with [`GET /media/{mediaId}`](https://useapi.net/docs/api-google-vids-v1/get-google-vids-media-mediaId?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) |
| `speech.mjs` / `speech.py` | Reads a script of up to 2,500 characters aloud with [`POST /speech`](https://useapi.net/docs/api-google-vids-v1/post-google-vids-speech?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) and downloads the WAV (24 kHz, mono) |

The Node.js and Python versions are equivalent. `prompts.json` holds the tutorial's avatar (Amber, voice `Vira`, the hilltop `refine`) and its 327-character script, and `smart-fridge.txt` the tutorial's 2,426-character story.

## Prerequisites

- [Node.js](https://nodejs.org) v21 or newer (no dependencies to install — uses built-in `fetch`), or [Python](https://www.python.org) 3.x (standard library only — no dependencies to install)
- A useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)
- A Google account connected through [Setup Google Vids](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) whose plan has AI avatar videos and Gemini uses. In our tests (November 2026) a free Google account had them too, though it has no video seconds or images.
- For the talking avatar: a JPEG, PNG or WebP photo of one person, facing the camera. Google refuses photos of prominent people and of minors.

What each script uses, from the account's own monthly counters, which [`GET /accounts/{email}`](https://useapi.net/docs/api-google-vids-v1/get-google-vids-accounts-email?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) shows as `avatarVideo`, `speech` and `image`:

| Step | Endpoint | Allowance used | Saved as |
|---|---|--:|---|
| Upload the photo | [POST /assets](https://useapi.net/docs/api-google-vids-v1/post-google-vids-assets?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) | nothing | |
| The avatar from the photo, with `refine` | [POST /avatars](https://useapi.net/docs/api-google-vids-v1/post-google-vids-avatars?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) | 2 images (the reframed photo and the change), nothing on a plan without images | `amber-avatar.jpg`, `amber-avatar.json` |
| The talking video | [POST /videos/avatar](https://useapi.net/docs/api-google-vids-v1/post-google-vids-videos-avatar?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) | 1 AI avatar video and 1 Gemini use, no video seconds | `amber-talking.mp4`, `amber-talking.json` |
| Speech on its own | [POST /speech](https://useapi.net/docs/api-google-vids-v1/post-google-vids-speech?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) | 1 Gemini use | `smart-fridge.wav`, `smart-fridge.json` |

One useapi.net [$15/month subscription](https://useapi.net/docs/subscription?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) covers every useapi.net API, with no per-video charge.

## Usage

```bash
node ./talking-avatar.mjs <API_TOKEN> <EMAIL> <PHOTO> [PROMPTS_FILE]
python3 ./talking-avatar.py <API_TOKEN> <EMAIL> <PHOTO> [PROMPTS_FILE]

node ./speech.mjs <API_TOKEN> <EMAIL> [SCRIPT_FILE] [VOICE]
python3 ./speech.py <API_TOKEN> <EMAIL> [SCRIPT_FILE] [VOICE]
```

`EMAIL` is the connected Google account. The upload, the avatar and the video all run on it, since an uploaded file and an avatar work only on their own account. `PROMPTS_FILE` defaults to the `prompts.json` next to the script, `SCRIPT_FILE` to `smart-fridge.txt` and `VOICE` to `Vira`. [`GET /voices`](https://useapi.net/docs/api-google-vids-v1/get-google-vids-voices?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) lists all 30 voices, by Vids name (`Vira`) or Google voice id (`Pulcherrima`).

Before it spends anything, `talking-avatar` checks `prompts.json` and reads the account with `GET /accounts/{email}`. It stops if the account is unhealthy, its plan has no AI avatar videos, or none or no Gemini uses are left this month.

## prompts.json

- `avatar` — the [`POST /avatars`](https://useapi.net/docs/api-google-vids-v1/post-google-vids-avatars?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) fields, sent as is with your photo as `image`: `name` (1 to 40 characters), `voice` (a name or voice id from `GET /voices`) and the optional `refine` (a change in words, up to 1,000 characters: clothes, place, light). Google reframes the photo into a 16:9 avatar picture of one person facing the camera, then applies `refine`. A `logo` (an `assetId` or image `mediaId` on the same account) can go here too.
- `script` — what the avatar says, word for word: 1 to 400 characters that, spoken, fit in 30 seconds. Audio tags in square brackets, such as `[awe]`, `[whisper]` or `[short pause]`, are performed, not read.

Two things help the video, as in the tutorial: the avatar faces the camera, because the video lip-syncs the face, and the background is still, so the person is the only thing that moves.

How long a script runs depends on the voice. In `Vira` the 327-character script ran 23.8 seconds, while a slower voice or `[slow pace]` makes the same text longer. To hear a script in the avatar's voice first, put it in a text file and read it with `speech.mjs` / `speech.py` in the same voice (1 Gemini use).

## Output

Everything lands in an `output/` folder in the current directory:

- the avatar picture (`<name>-avatar.jpg`) and the avatar as `POST /avatars` returned it (`<name>-avatar.json`),
- the talking video (`<name>-talking.mp4`) and its job record (`<name>-talking.json`, with `result.speechDuration` and `result.quota.avatarVideo`),
- the speech (`<script file>.wav`) and its job record (`<script file>.json`),
- `talking_avatar_state.json`, the ids of every finished step.

Run `talking-avatar` again and it continues where it stopped: a finished avatar or video is not made again (it is downloaded again if its file is missing), and a video job that was still running is picked up by its `jobid` instead of being sent again. To make a new video with another script, delete `video` from `talking_avatar_state.json`. To make a new avatar too, delete `avatar` as well, and pass the photo again.

Generated files live in Google's temporary storage, videos for 24 hours, so the scripts download each one as soon as it is made. Every MP4 has Google's visible Gemini ✦ in the bottom-right corner and an invisible SynthID watermark, see [Watermark](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#watermark).

## Cleanup

The avatar stays in the account's Vids document, reusable by `avatarId` in more talking videos and as `avatar_1` in [`POST /videos`](https://useapi.net/docs/api-google-vids-v1/post-google-vids-videos?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api), until you delete it. To delete the avatar this script created (only that one, listed in `output/talking_avatar_state.json`), run it again with `--cleanup`:

```bash
node ./talking-avatar.mjs <API_TOKEN> <EMAIL> --cleanup
python3 ./talking-avatar.py <API_TOKEN> <EMAIL> --cleanup
```

It calls [`DELETE /avatars/{avatarId}`](https://useapi.net/docs/api-google-vids-v1/delete-google-vids-avatars-avatarId?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api).

## Retries and errors

The scripts send a request again only when nothing was made:

- a POST answered `429` because every `maxJobs` slot is busy (every 30 seconds), `503` (every 30 seconds), or `596` while the account is being re-checked (every 60 seconds),
- `502` from `POST /avatars` ("Google did not keep the avatar"),
- a job that failed with `429` because Google limits the account for a minute (after its `retryAt`).

Any other failure stops the script with the API's message. A talking video is never sent again automatically: Google counts a video it refused while making it. If a POST gets no answer at all, the script stops too, because the job may have been accepted.

| Error | What to do |
|---|---|
| `400` the script runs over 30 seconds when spoken | Shorten the script in `prompts.json`, or drop a `[slow pace]` tag, and run again. No AI avatar video was used, but the Gemini use for its speech was. |
| `422` Google refused the photo | A prominent person, a minor or content against Google's terms. Nothing is saved or charged. Use another photo. |
| `422` Google refused the finished video | Google's video check is stricter than its picture check: a photo avatar of someone who is not famous can still be refused as a celebrity (`FINISH_REASON_INPUT_IMAGE_CELEBRITY`), and Google still counts that video. Change `refine` and delete `avatar` from the state file, or start from another photo. |
| `422` Google refused the script | Nothing was charged. Change the words. |
| `403` no AI avatar videos or no speech on the plan | The account's Google plan has none of them (a monthly limit of 0), or its Google Workspace smart features are off. |
| `429` allowance used up | The month's AI avatar videos or Gemini uses are used up. `retryAt` is the reset, on the 1st of the month at 00:00 Pacific time. |
| `404` Account is not configured | Connect the account via [Setup Google Vids](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api), or pass the right `EMAIL`. |
| `504` Google did not finish the video in time | It may still count against the AI avatar videos. Run the script again to retry. |
| `596` signed out | Re-add the account via [Setup Google Vids](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api). |

Talking avatar videos are landscape only (1280×720): Google offers no portrait option for them. All codes are listed on [GET /jobs/{jobid}](https://useapi.net/docs/api-google-vids-v1/get-google-vids-jobs-jobid?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#model).

---

Support: [Discord](https://discord.gg/w28uK3cnmF) · [Telegram](https://t.me/use_api) · [YouTube](https://www.youtube.com/@useapi-net)
