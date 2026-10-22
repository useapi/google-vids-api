# Google Vids API examples (useapi.net): Gemini Omni 1.1 Flash video with voiced AI avatars

Runnable examples for the [Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) by [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api): make Gemini Omni 1.1 Flash video in [Google Vids](https://docs.google.com/videos) with voiced avatars, your own reference images, extends up to about 41 seconds and a 1080p upscale, through a REST API that runs on your paid [Google AI subscription](https://gemini.google/subscriptions/): Plus $4.99, Pro $19.99, Ultra $99.99 or Ultra $199.99 a month (as of October 2026). Vids has its own monthly allowance, separate from Google Flow's credits, and asks for no captcha.

| Example | What it does | Tutorial | Tutorial date |
|---|---|---|---|
| [`influencer-avatars/`](./influencer-avatars) | Two voiced avatars (one from a portrait, one from a description) present a product in a 10-second clip, extended to 30 seconds, with the first 20 seconds upscaled to 1080p. Node.js and Python | [How to Make AI Influencer Videos with Avatars via the Google Vids API](https://useapi.net/docs/articles/google-vids-influencer-avatars?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) | October 7, 2026 (October 20, 2026) |
| [`skills/google-vids-video/`](./skills/google-vids-video) | Agent skill for Claude Code, Codex and other coding agents: ask for a clip and the agent makes it with Omni 1.1 Flash in Vids (voiced AI avatars, reference images, extend, 1080p upscale, edit) and downloads the `.mp4`, never paying twice for a request. Install: `npx skills add useapi/google-vids-api --skill google-vids-video`. Bash, curl, jq | [SKILL.md](./skills/google-vids-video/SKILL.md) | October 8, 2026 |
| [`n8n/`](./n8n) | Ready-to-import n8n app: describe or pick a presenter, choose a voice, write the lines, and get a talking avatar video of up to 40 s with an optional 1080p upscale. No code | [n8n template #20704](https://n8n.io/workflows/20704) | October 12, 2026 |
| [`watermark-remover/`](./watermark-remover) | Removes the visible Gemini ✦ sparkle from Vids videos by reverse alpha blending, in all four Vids formats, for clips as generated and their upscales (not extended or edited clips). Python | [Google Vids API › Watermark](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#watermark) | October 8, 2026 |

## Quick start

You need [Node.js](https://nodejs.org) v21 or newer or [Python](https://www.python.org) 3.x (no dependencies to install), a useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api), and a Google account on a paid Google AI subscription connected with the [Google Vids setup](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api).

```bash
git clone https://github.com/useapi/google-vids-api.git
cd google-vids-api/influencer-avatars
node ./influencer-avatars.mjs <API_TOKEN> <EMAIL>
# or, equivalently, with Python:
python3 ./influencer-avatars.py <API_TOKEN> <EMAIL>
```

To take the ✦ off a downloaded clip (needs `numpy` and `ffmpeg`):

```bash
cd google-vids-api/watermark-remover
pip install numpy
python3 vids_watermark_remover.py my-clip.mp4    # → my-clip_clean.mp4
```

Each example's README lists its options. Every endpoint is documented in the [Google Vids API reference](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api).

## MCP server

useapi.net also runs a hosted [Model Context Protocol](https://modelcontextprotocol.io) server for Google Vids, so an AI assistant such as Claude Code, Cursor or VS Code Copilot can use it on your Google Vids account. It has 16 tools: Gemini Omni 1.1 Flash clips (3–10 s, 720p or 1080p, with sound and speech) from text, a start image or up to 3 references; extend, upscale and edit; images in 7 styles; uploads; and voiced avatars with 30 voices that speak the lines in your prompt. Nothing to install or run locally.

- Endpoint: `https://api.useapi.net/v1/google-vids/mcp`
- Transport: Streamable HTTP
- Authorization: your useapi.net API token in the `Authorization: Bearer …` header, and an account connected with the [Google Vids setup](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)
- Listed in the official MCP Registry as `net.useapi/google-vids`

Claude Code:

```bash
claude mcp add --transport http useapi-google-vids https://api.useapi.net/v1/google-vids/mcp --header "Authorization: Bearer YOUR_API_TOKEN"
```

Cursor, VS Code, Windsurf and the full tool list: [Google Vids MCP server docs](https://useapi.net/docs/api-google-vids-v1/mcp?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api). useapi.net is a third-party API, not affiliated with Google.

## Use with Claude Code

This repo is also a Claude Code plugin marketplace. The plugin adds the hosted Google Vids MCP server and the `google-vids-video` agent skill, and reads your token from the `USEAPI_TOKEN` environment variable, so set it before you start Claude Code:

```bash
export USEAPI_TOKEN=user:12345-...      # your useapi.net API token
```

Then, inside Claude Code:

```
/plugin marketplace add useapi/google-vids-api
/plugin install google-vids@useapi-google-vids
```

On Claude Code 2.1.275 or later, `/plugin install google-vids --marketplace useapi/google-vids-api` does both in one step. Run `/mcp` to check that `useapi-google-vids` is connected.

## Use with Gemini CLI

This repo is also a Gemini CLI extension with the same MCP server and the `google-vids-video` agent skill:

```bash
gemini extensions install https://github.com/useapi/google-vids-api
```

The install asks for your useapi.net API token and keeps it in the system keychain. Change it later with `gemini extensions config useapi-google-vids`, and check the connection with `gemini mcp list`. The `google-vids-video` skill's scripts read `USEAPI_TOKEN` from your shell, so export it as well if you use the skill.

## Common questions

<!-- Figures as on the useapi.net Google Vids API overview (docs/api-google-vids-v1/index.md). Official, re-read on the overview 2026-10-21: https://ai.google.dev/gemini-api/docs/pricing (Omni 1.1 Flash $17.50 per 1M output tokens at 5,792 tokens per 720p second = ~$1.01 per 10 s). Vids: Ultra $199.99 = 10,000 s/month = ~$0.20 per 10 s. Allowances (https://support.google.com/docs/answer/15609411, read 2026-10-21): Plus 60 s and up to 50 images, Pro 500 s and 30, Ultra $99.99 2,500 s and 300, Ultra $199.99 10,000 s and 1,000. No public Google Vids developer API (Google Workspace developer docs). The useapi.net subscription is not part of the per-clip math. -->

- **Does Google Vids have an API?** Through useapi.net, yes. Google has published no Google Vids API (as of October 2026), and the useapi.net Google Vids API makes Gemini Omni 1.1 Flash video at 720p or 1080p, images and talking avatars in Vids over REST, on your [Google AI subscription](https://gemini.google/subscriptions/). Google offers Vids avatars only in its web app, Vids asks for no captcha, and its allowance is separate from Google Flow's credits.
- **How much does the Google Vids API cost?** Through useapi.net, a 10-second Omni 1.1 Flash clip uses about $0.20 of a Google AI Ultra $199.99 subscription in Vids, against about $1.01 at 720p on Google's metered [Gemini API](https://ai.google.dev/gemini-api/docs/pricing), and 1080p uses the same seconds as 720p (as of October 2026). Images and avatars use no video seconds, and there is no per-clip charge from useapi.net. The [price table](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#pricing) shows every subscription.
- **How much can I make?** Through useapi.net, as much as your Vids allowance holds: Google AI Plus gets 60 seconds of video a month, Pro 500 seconds, Ultra $99.99 (Ultra 5x) 2,500 seconds and Ultra $199.99 (Ultra 20x) 10,000 seconds, about 1,000 ten-second clips. A free Google account gets no video or images, but can still make avatars at no cost. See [plans and allowances](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#plans-and-monthly-allowances).
- **Google Vids or Google Flow?** Through useapi.net you can use both: they make Omni 1.1 Flash video on the same Google AI subscription from separate allowances, so on Ultra $199.99 one Google account connected to both APIs gets about 2,666 ten-second Omni clips a month. Vids extends Omni clips and needs no captcha, and Flow adds Veo 3.1 and Nano Banana Pro, 2.1 and 2 Lite images. Flow examples: [useapi/google-flow-api](https://github.com/useapi/google-flow-api).
- **How do I connect my Google account?** Through the useapi.net [automated browser setup](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api): sign in with Google in a remote browser once, with no DevTools, cookie copying, Google Cloud project or Gemini API key, and the account is verified and added. To connect by hand, the [Google Account Setup](https://github.com/useapi/google-account-setup) scripts open a clean, single-use browser profile, so the session you copy keeps working.
- **Is the video watermarked?** Through useapi.net you get Google's file unchanged: every Vids clip carries an invisible SynthID watermark and a visible Gemini ✦ in a corner. The free useapi.net [`watermark-remover/`](./watermark-remover) takes the visible ✦ off clips as generated and their upscales (not extended or edited clips) and leaves SynthID untouched.

## 中文说明

这是 [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) 的 Google Vids API 示例代码。通过第三方 REST API 在 Google Vids 中调用 Gemini Omni 1.1 Flash 生成视频，支持带配音的虚拟形象（avatar）、参考图片、视频延长（最长约 41 秒）和 1080p 放大。

- 使用你的付费 Google AI 订阅（Plus $4.99、Pro $19.99、Ultra $99.99 或 Ultra $199.99 每月，2026 年 10 月价格），按 Vids 每月额度（视频秒数和图片数）计算，与 Google Flow 的积分分开。
- 无需验证码（captcha），无需 Google Cloud 项目或 API Key。
- useapi.net 每月 15 美元，含所有 API，每个订阅可连接 3 个 Google 账号，不按条收费。
- `watermark-remover/` 可去除视频右下角可见的 Gemini ✦ 标记，不改动不可见的 SynthID 水印。

中文教程（数字人、视频延长、无需验证码，含 curl 示例）：[如何通过 Google Vids API 用 Gemini Omni 1.1 Flash 生成会说话的数字人视频](https://useapi.net/docs/articles/google-vids-api-zh?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)。完整文档：[Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)。

## About useapi.net

[useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) is a third-party REST API for AI services, not affiliated with Google. The [Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) runs on your Google AI subscription, so you spend its monthly Vids allowance instead of paying metered developer-API prices.

Visit our [Discord Server](https://discord.gg/w28uK3cnmF) or [Telegram Channel](https://t.me/use_api) for any support questions and concerns.

We regularly post guides and tutorials on the [YouTube Channel](https://www.youtube.com/@useapi-net).

## License

The example code in this repository is released under the [MIT License](./LICENSE). It covers the example scripts only, not the useapi.net service or API.
