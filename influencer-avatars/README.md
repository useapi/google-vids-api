# AI influencer video with voiced avatars — Google Vids API (Node.js & Python)

📖 Full walkthrough: **[How to Make AI Influencer Videos with Avatars via the Google Vids API](https://useapi.net/docs/articles/google-vids-influencer-avatars)** — October 7, 2026

Make a talking AI influencer video through the [Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) by [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api): two voiced avatars present a product on a stage in a Gemini Omni 1.1 Flash clip, which is then extended to 30 seconds and upscaled to 1080p.

`influencer-avatars.mjs` (Node.js) and `influencer-avatars.py` (Python) are equivalent implementations of the tutorial's pipeline. Each reads every step from `prompts.json`, runs each generation as an async job (`async: true`), polls [`GET /jobs/{jobid}`](https://useapi.net/docs/api-google-vids-v1/get-google-vids-jobs-jobid?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) every 10 seconds, and downloads every image and MP4 with [`GET /media/{mediaId}`](https://useapi.net/docs/api-google-vids-v1/get-google-vids-media-mediaId?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api).

## Prerequisites

- [Node.js](https://nodejs.org) v21 or newer (no dependencies to install — uses built-in `fetch`), or [Python](https://www.python.org) 3.x (standard library only — no dependencies to install)
- A useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)
- A Google account connected through [Setup Google Vids](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api), on a paid Google AI plan. Every call uses that account's monthly Vids allowance, in seconds of video and a count of images. Google's figures, from the [Plans and monthly allowances](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#plans-and-monthly-allowances) table:

| | Google AI Plus | Google AI Pro | Google AI Ultra 5x | Google AI Ultra 20x |
|---|---|---|---|---|
| AI video clips | 6 a month, combined with AI avatars | 500 seconds a month | 2,500 seconds a month | 10,000 seconds a month |
| Image generation and editing | 1 credit per image action | 30 a month | 300 a month | 1,000 a month |

Google AI Ultra $199 is the plan Google calls Ultra 20x. A free Google account gets no Vids allowance for video or images. useapi.net charges a flat [$15/month](https://useapi.net/docs/subscription?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) for every API, with no per-clip charge.

## Usage

```bash
node ./influencer-avatars.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]
python3 ./influencer-avatars.py <API_TOKEN> <EMAIL> [PROMPTS_FILE]
```

`EMAIL` is the connected Google account. Every step is pinned to it, since every input of one video must come from the same account. `PROMPTS_FILE` defaults to the `prompts.json` next to the script.

Before it spends anything, the script checks `prompts.json`, reads the account's allowance with [`GET /accounts/{email}`](https://useapi.net/docs/api-google-vids-v1/get-google-vids-accounts-email?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api), and stops if the account is unhealthy or has too little left for the steps still to run.

## The pipeline

What each step uses from the Vids allowance, as measured in the tutorial (["What it cost"](https://useapi.net/docs/articles/google-vids-influencer-avatars?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#what-it-cost)):

| Step | Endpoint | Allowance used | Saved as |
|---|---|--:|---|
| 1. Mia's portrait (`9:16`, `photography`) | [POST /images](https://useapi.net/docs/api-google-vids-v1/post-google-vids-images?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) | 1 image | `mia-portrait.jpg` |
| 2. The AeroLoop product shot (`16:9`, `photography`) | [POST /images](https://useapi.net/docs/api-google-vids-v1/post-google-vids-images?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) | 1 image | `aeroloop.jpg` |
| 3. Mia's avatar from her portrait, voice `Aoede` | [POST /avatars](https://useapi.net/docs/api-google-vids-v1/post-google-vids-avatars?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) | nothing | `mia-avatar.json` |
| 4. Leo's avatar from a description, voice `Puck` | [POST /avatars](https://useapi.net/docs/api-google-vids-v1/post-google-vids-avatars?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) | 1 image | `leo-avatar.jpg` |
| 5. The 10-second `720p` launch clip: `avatar_1` (Mia) + `avatar_2` (Leo) + `referenceImage_1` (the AeroLoop) | [POST /videos](https://useapi.net/docs/api-google-vids-v1/post-google-vids-videos?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) | 10 s | `launch-10s.mp4` |
| 6. Extend +10 s, a fan storms the stage | [POST /videos/extend](https://useapi.net/docs/api-google-vids-v1/post-google-vids-videos-extend?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) | 10 s | `launch-20s.mp4` |
| 7. Extend +10 s, the confetti finale | [POST /videos/extend](https://useapi.net/docs/api-google-vids-v1/post-google-vids-videos-extend?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) | 10 s | `launch-30s.mp4` |
| 8. Upscale the 20-second clip to `1080p` | [POST /videos/upscale](https://useapi.net/docs/api-google-vids-v1/post-google-vids-videos-upscale?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) | 20 s | `launch-20s-1080p.mp4` |
| Total | | 50 s of video, 3 images | |

An extend uses only the seconds it adds. An upscale uses the clip's full length again, and it takes `720p` clips of up to 20 seconds, so step 8 upscales the 20-second clip from step 6, as in the tutorial, not the 30-second one. A request Google refuses uses nothing.

An extend gets the clip and the prompt only, not the avatars, so its prompts name people by what they wear ("the man in the black puffer vest").

## prompts.json

The tutorial's exact prompts and settings. Each step's fields go to its endpoint as is, except `name` (the step's name and file name) and the names that link one step to another, which the script swaps for the ids the API returned.

- `images` — one [`POST /images`](https://useapi.net/docs/api-google-vids-v1/post-google-vids-images?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) call each: `name` (the file name), `prompt`, `aspectRatio` (`16:9`, `1:1`, `9:16`), `style` (`none`, `photography`, `sketch`, `background`, `watercolor`, `vector-art`, `cyberpunk`).
- `avatars` — one [`POST /avatars`](https://useapi.net/docs/api-google-vids-v1/post-google-vids-avatars?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) call each: `name`, `voice` (a name or voice id from [`GET /voices`](https://useapi.net/docs/api-google-vids-v1/get-google-vids-voices?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)), and either `image` (the `name` of an image above) or `appearance` (Google draws the person), with optional `outfit`, `shot` (`close-up`, `upper-body`, `full-body`), `expression` and `details`.
- `launch` — the [`POST /videos`](https://useapi.net/docs/api-google-vids-v1/post-google-vids-videos?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) clip: `name`, `prompt`, `duration` (3 to 10), `resolution` (`720p`, `1080p`), `aspectRatio` (`landscape`, `portrait`), `avatar_1`..`avatar_3` (avatar names) and `referenceImage_1`..`referenceImage_3` (image names), up to 3 in all. The prompt calls them `@avatar_1`, `@referenceImage_1` and so on, and each avatar speaks its quoted line in its own voice.
- `extends` — [`POST /videos/extend`](https://useapi.net/docs/api-google-vids-v1/post-google-vids-videos-extend?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) calls in order, each extending the clip before it: `name`, `prompt`, `duration` (seconds to add, 3 to 10). Leave the list empty to skip extends.
- `upscale` — [`POST /videos/upscale`](https://useapi.net/docs/api-google-vids-v1/post-google-vids-videos-upscale?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api): `name` and `clip`, the name of a `720p` clip of up to 20 seconds. Remove it to skip the upscale.

## Output

Everything lands in an `output/` folder in the current directory:

- the images and the drawn avatar picture (`.jpg`) and the clips (`.mp4`),
- each job record (`<name>.json`, with `result.quota` and `result.elapsedMs`) and each avatar (`mia-avatar.json`, `leo-avatar.json`),
- `influencer_state.json`, the ids of every finished step.

Run the script again and it continues where it stopped: finished steps are skipped (and downloaded again if their file is missing), and a job that was still running is picked up by its `jobid` instead of being sent again. To redo a step, delete its entry from `influencer_state.json`.

Generated files live in Google's temporary storage: images for a few hours, videos for at least half a day. The script downloads each one as soon as it is made.

Every MP4 has Google's visible Gemini ✦ in the bottom-right corner and an invisible SynthID watermark, see [Watermark](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#watermark).

## Cleanup

The avatars stay in the account's Vids document, reusable by `avatarId` in any later video, until you delete them. To delete the avatars the script created (only those listed in `output/influencer_state.json`, never others on the account), run it again with `--cleanup`:

```bash
node ./influencer-avatars.mjs <API_TOKEN> <EMAIL> --cleanup
python3 ./influencer-avatars.py <API_TOKEN> <EMAIL> --cleanup
```

It calls [`DELETE /avatars/{avatarId}`](https://useapi.net/docs/api-google-vids-v1/delete-google-vids-avatars-avatarId?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) for each one. [`GET /avatars`](https://useapi.net/docs/api-google-vids-v1/get-google-vids-avatars?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) lists every avatar on your accounts.

## Retries and errors

The script sends a request again only when nothing was made:

- a POST answered `429` because every `maxJobs` slot is busy (every 30 seconds), `503` (every 30 seconds), or `596` while the account is being re-checked (every 60 seconds),
- `502` from `POST /avatars` ("Google did not keep the avatar"),
- a job that failed with `429` because Google limits the account for a minute (after its `retryAt`).

A job that fails for any other reason stops the script, because Google may have made and charged the clip before the job failed. For example, a job that fails with `502` means Google answered but the API could not read the file: Google may already have made and charged it, so report the `jobid` to support rather than paying for it twice. Run the script again to retry that step. If a POST gets no answer at all, the script stops too, because the job may have been accepted. The script stops with the API's message:

| Error | What to do |
|---|---|
| `401` Unauthorized | Check the API token. |
| `404` Account is not configured | Connect the account via [Setup Google Vids](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api), or pass the right `EMAIL`. |
| `403` no Vids allowance (monthly limit 0) | The account's Google plan has no Vids allowance for this, as on a free account. Use an account on a paid Google AI plan. |
| `429` allowance used up | The month's seconds or images are used up. `retryAt` is the reset, on the 1st of the month at 00:00 Pacific time. |
| `422` Google refused this request | Google refused the prompt or the inputs. Nothing was charged. Change the prompt in `prompts.json` and run again. |
| `400` image expired | A generated image lasts a few hours. Delete its entry under `images` in `output/influencer_state.json` and run again. |
| `504` Google did not answer in time | Google may have charged it, so the script does not send it again. Run the script again to retry the step. |
| `596` signed out | Re-add the account via [Setup Google Vids](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api). |

All codes are listed on [GET /jobs/{jobid}](https://useapi.net/docs/api-google-vids-v1/get-google-vids-jobs-jobid?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#model).

---

Support: [Discord](https://discord.gg/w28uK3cnmF) · [Telegram](https://t.me/use_api) · [YouTube](https://www.youtube.com/@useapi-net)
