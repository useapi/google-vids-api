# Google Vids API examples (useapi.net): Gemini Omni 1.1 Flash video with voiced AI avatars

Runnable examples for the [Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) by [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api): make **Gemini Omni 1.1 Flash** video in [Google Vids](https://docs.google.com/videos) with voiced **avatars**, your own reference images, extends up to about 41 seconds and a 1080p upscale, through a REST API that runs on your own Google AI plan. Vids has its own monthly allowance, separate from Google Flow's credits, and asks for no captcha.

| Example | What it does | Tutorial | Tutorial date |
|---|---|---|---|
| [`influencer-avatars/`](./influencer-avatars) | Two voiced avatars (one from a portrait, one from a description) present a product in a 10-second clip, extended to 30 seconds, with the first 20 seconds upscaled to 1080p. Node.js and Python | [How to Make AI Influencer Videos with Avatars via the Google Vids API](https://useapi.net/docs/articles/google-vids-influencer-avatars) | October 7, 2026 |
| [`watermark-remover/`](./watermark-remover) | Removes the visible Gemini ✦ sparkle from Vids videos by reverse alpha blending, in all four Vids formats, for clips as generated and their upscales (not extended or edited clips). Python | [Google Vids API › Watermark](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#watermark) | October 8, 2026 |

## Quick start

You need [Node.js](https://nodejs.org) v21 or newer **or** [Python](https://www.python.org) 3.x (no dependencies to install), a useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api), and a Google account on a paid Google AI plan connected with the [Google Vids setup](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api).

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

## Common questions

- **Does Google Vids have an API?** Not for generating video. Vids is a Google Workspace app, and Google doesn't offer an API for it. Omni 1.1 Flash itself is sold on the metered Gemini API at about $0.10 per second of 720p video. useapi.net drives your own Google account in Vids instead, so clips come out of the monthly Vids allowance of your Google AI plan.
- **How much can I make?** Google meters Vids per month: Google AI Pro gets 500 seconds of video, Ultra 5x 2,500 seconds and Ultra 20x (Ultra $199) 10,000 seconds, about 1,000 ten-second clips. A free Google account gets no video or images, but can still make avatars. See [plans and allowances](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#plans-and-monthly-allowances).
- **What does it cost?** A flat [$15/month](https://useapi.net/docs/subscription?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) to useapi.net, which covers every useapi.net API, plus the Google AI plan you already have. There is no per-clip charge from us.
- **Google Vids or Google Flow?** Both make Omni 1.1 Flash video on the same Google AI plan, from separate allowances, so one Google account connected to both APIs gets both. Vids extends Omni clips and needs no captcha; Flow also has Veo 3.1 and Nano Banana images. Flow examples: [useapi/google-flow-api](https://github.com/useapi/google-flow-api).
- **Is the video watermarked?** Every Vids clip has an invisible SynthID watermark and a visible Gemini ✦ in the corner. [`watermark-remover/`](./watermark-remover) removes the visible sparkle from clips as generated and their upscales (not from extended or edited clips); SynthID is untouched.
- **Connecting an account by hand?** The [Google Account Setup](https://github.com/useapi/google-account-setup) scripts open a clean, single-use browser profile, so the session you copy keeps working.

## 中文说明

这是 [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) 的 Google Vids API 示例代码。通过 REST API 在 Google Vids 中调用 **Gemini Omni 1.1 Flash** 生成视频，支持带配音的虚拟形象（avatar）、参考图片、视频延长（最长约 41 秒）和 1080p 放大。

- 使用你自己的 Google 账号和付费 Google AI 订阅，按 Vids 每月额度（视频秒数和图片数）计算，与 Google Flow 的积分分开。
- 无需验证码（captcha），无需 Google Cloud 项目或 API Key。
- 价格：useapi.net 每月 15 美元（含所有 API），加上你已有的 Google AI 订阅。
- `watermark-remover/` 可去除视频右下角可见的 Gemini ✦ 标记，不改动不可见的 SynthID 水印。

中文教程（数字人、视频延长、无需验证码，含 curl 示例）：[如何通过 Google Vids API 用 Gemini Omni 1.1 Flash 生成会说话的数字人视频](https://useapi.net/docs/articles/google-vids-api-zh)。完整文档：[Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)。

## About useapi.net

[useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) is an experimental REST API for AI services. The Google Vids API drives your own Google account on your Google AI plan, so you spend your plan's monthly Vids allowance instead of paying metered developer-API prices.

Visit our [Discord Server](https://discord.gg/w28uK3cnmF) or [Telegram Channel](https://t.me/use_api) for any support questions and concerns.

We regularly post guides and tutorials on the [YouTube Channel](https://www.youtube.com/@useapi-net).

## License

The example code in this repository is released under the [MIT License](./LICENSE). It covers the example scripts only, not the useapi.net service or API.
