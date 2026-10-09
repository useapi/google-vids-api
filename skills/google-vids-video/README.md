# Google Vids video and AI avatars: an agent skill

An [Agent Skill](https://agentskills.io) that lets Claude Code, Codex and other coding agents make AI video in **Google Vids** with **Gemini Omni 1.1 Flash**: talking **AI avatars** (a person drawn from a description, with one of 30 voices) as an AI influencer, spokesperson or UGC ad presenter, text-to-video, reference images, extends up to about 41 seconds, a 1080p upscale, edits by prompt and Vids images, and download the `.mp4`. Ask your agent "make a 6-second portrait clip of a friendly barista avatar holding up our mug and saying it's the best coffee she's had" and it runs the scripts in this folder.

It calls the [Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=skill&utm_campaign=google-vids-skill) by [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=skill&utm_campaign=google-vids-skill), a third-party REST API that runs on your own Google Vids account. Each clip spends seconds of the monthly Vids allowance of your Google AI plan, separate from Google Flow credits, and no captcha is involved.

## Install

With the [skills CLI](https://github.com/vercel-labs/skills) (asks which agents to install for):

```bash
npx skills add useapi/google-vids-api --skill google-vids-video
# add -g to install for your user instead of the current project
```

Or copy the folder yourself:

```bash
git clone https://github.com/useapi/google-vids-api.git
cp -r google-vids-api/skills/google-vids-video ~/.claude/skills/     # Claude Code, every project
cp -r google-vids-api/skills/google-vids-video .claude/skills/       # Claude Code, this project only
cp -r google-vids-api/skills/google-vids-video ~/.codex/skills/      # Codex
```

Then give the agent your token in the environment it runs in:

```bash
export USEAPI_TOKEN=user:12345-...      # your useapi.net API token
export USEAPI_EMAIL=you@gmail.com       # optional: which connected Google account to use
```

You need:

1. A useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=skill&utm_campaign=google-vids-skill). One [$15/month subscription](https://useapi.net/docs/subscription?utm_source=github.com&utm_medium=skill&utm_campaign=google-vids-skill) covers every useapi.net API.
2. A Google account on a paid Google AI plan, connected with the [Google Vids setup](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=skill&utm_campaign=google-vids-skill). A clip uses its length in seconds of the Vids allowance (Pro 500 s a month, Ultra $199 10,000 s), the same at `720p` and `1080p`. See [plans and allowances](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=skill&utm_campaign=google-vids-skill#plans-and-monthly-allowances).
3. `bash`, `curl` and [`jq`](https://jqlang.org/download/).

## Use it without an agent

The scripts work on their own too:

```bash
AV=$(./scripts/avatar.sh "Maya" Kaci appearance="a woman in her late twenties with a curly brown bob" outfit="cream knit sweater" shot=upper-body)
./scripts/video.sh "@avatar_1 holds up the mug and says: \"Best coffee I've had all year.\" Handheld phone camera." \
  avatar_1="$AV" aspectRatio=portrait duration=6
```

| Script | What it does |
|---|---|
| `scripts/video.sh` | Generate, wait and download in one command: prompt in, `.mp4` out |
| `scripts/avatar.sh` | Create an avatar from a description or a generated image, print its `avatarId`; `--list`, `--delete`, `--voices` |
| `scripts/image.sh` | Generate one Vids image, save the JPEG, print its `mediaId` |
| `scripts/generate.sh` | Start a clip (avatars, reference images, start image, duration, resolution, aspect ratio), print the job id |
| `scripts/extend.sh` | Add 3 to 10 seconds to a clip, print the job id |
| `scripts/upscale.sh` | Upscale a `720p` clip of up to 20 seconds to `1080p`, print the job id |
| `scripts/edit.sh` | Change a clip with a prompt, print the job id |
| `scripts/wait-job.sh` | Poll the job until it is done, print the final record |
| `scripts/download.sh` | Download the finished `.mp4` or `.jpg` |

To take the visible Gemini ✦ off a clip, use the [watermark remover](../../watermark-remover) in this repo. It works on clips as generated and on their upscales, not on extended or edited clips.

[`SKILL.md`](./SKILL.md) is what the agent reads: the options, allowance costs, the 720p-then-upscale rule, prompting rules for avatars and extends, and what to do on each error without paying twice. The full API reference is at [useapi.net/docs/api-google-vids-v1](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=skill&utm_campaign=google-vids-skill).
