# Google Vids API examples (useapi.net): Gemini Omni 1.2 Flash video with voiced AI avatars

English · [中文](#中文说明) · [日本語](#日本語の説明) · [Português](#sobre-este-repositório) · [Tiếng Việt](#về-repo-này) · [Bahasa Indonesia](#tentang-repo-ini) · [ไทย](#เกี่ยวกับ-repo-นี้)

Runnable examples for the [Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) by [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api): make Gemini Omni 1.2 Flash video of up to 15 seconds in [Google Vids](https://docs.google.com/videos) with voiced avatars, your own reference images, extends up to about 34 seconds and a 1080p upscale, talking avatar videos of up to 30 seconds made from a photo, and speech in 30 Gemini voices, through a REST API that runs on your paid [Google AI subscription](https://gemini.google/subscriptions/): Plus $4.99, Pro $19.99, Ultra $99.99 or Ultra $199.99 a month (as of November 2026). Vids has its own monthly allowance, separate from Google Flow's credits, and asks for no captcha.

| Example | What it does | Tutorial | Tutorial date |
|---|---|---|---|
| [`influencer-avatars/`](./influencer-avatars) | Two voiced avatars (one from a portrait, one from a description) present a product in a 10-second clip, extended to 30 seconds, with the first 20 seconds upscaled to 1080p. Node.js and Python | [How to Make AI Influencer Videos with Avatars via the Google Vids API](https://useapi.net/docs/articles/google-vids-influencer-avatars?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) · [中文](https://useapi.net/docs/articles/google-vids-api-zh?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) | October 7, 2026 (October 20, 2026) |
| [`talking-avatar/`](./talking-avatar) | A photo becomes a voiced avatar, restyled in one sentence with `refine`, that reads your script in a 1280×720 talking-head video of up to 30 seconds (`POST /videos/avatar`). Plus speech on its own: a 2,426-character story read in a Gemini voice and saved as a WAV (`POST /speech`). Node.js and Python | [A talking avatar from a photo](https://useapi.net/docs/articles/google-vids-influencer-avatars?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#a-talking-avatar-from-a-photo) and [Speech on its own](https://useapi.net/docs/articles/google-vids-influencer-avatars?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#speech-on-its-own) | November 4, 2026 |
| [`skills/google-vids-video/`](./skills/google-vids-video) | Agent skill for Claude Code, Codex and other coding agents: ask for a clip and the agent makes it with Omni 1.2 Flash in Vids (voiced AI avatars, reference images, extend, 1080p upscale, edit) and downloads the `.mp4`, never paying twice for a request. Install: `npx skills add useapi/google-vids-api --skill google-vids-video`. Bash, curl, jq | [SKILL.md](./skills/google-vids-video/SKILL.md) | October 8, 2026 |
| [`n8n/`](./n8n) | Ready-to-import n8n app: describe or pick a presenter, choose a voice, write the lines, and get a talking avatar video of up to about 34 s with an optional 1080p upscale. No code | [n8n template #20704](https://n8n.io/workflows/20704) | October 12, 2026 |
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

A talking avatar from your own photo, and speech on its own:

```bash
cd google-vids-api/talking-avatar
node ./talking-avatar.mjs <API_TOKEN> <EMAIL> photo.jpg    # or: python3 ./talking-avatar.py …
node ./speech.mjs <API_TOKEN> <EMAIL>                      # or: python3 ./speech.py …
```

To take the ✦ off a downloaded clip (needs `numpy` and `ffmpeg`):

```bash
cd google-vids-api/watermark-remover
pip install numpy
python3 vids_watermark_remover.py my-clip.mp4    # → my-clip_clean.mp4
```

Each example's README lists its options. Every endpoint is documented in the [Google Vids API reference](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api).

## MCP server

useapi.net also runs a hosted [Model Context Protocol](https://modelcontextprotocol.io) server for Google Vids, so an AI assistant such as Claude Code, Cursor or VS Code Copilot can use it on your Google Vids account. It has 18 tools: Gemini Omni 1.2 Flash clips (3–15 s, 720p or 1080p, with sound and speech) from text, a start image or up to 3 references; extend (up to 10 s a call, on clips of up to 24 s), upscale and edit (up to 15 s); images in 7 styles; uploads; voiced avatars with 30 voices, made from a description or your own photo and restyled in words; talking avatar videos of up to 30 seconds that read your script; and speech from a script of up to 2,500 characters. Nothing to install or run locally.

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

## More articles

- [Can You Use Your Google AI Subscription Through an API? What Plus, Pro and Ultra Get You](https://useapi.net/docs/articles/google-ai-subscription-api?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) · Also in [中文](https://useapi.net/docs/articles/google-ai-subscription-api-zh?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) · [日本語](https://useapi.net/docs/articles/google-ai-subscription-api-ja?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) · [Português](https://useapi.net/docs/articles/google-ai-subscription-api-pt?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) · [Tiếng Việt](https://useapi.net/docs/articles/google-ai-subscription-api-vi?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) · [Bahasa Indonesia](https://useapi.net/docs/articles/google-ai-subscription-api-id?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) · [ไทย](https://useapi.net/docs/articles/google-ai-subscription-api-th?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)
- [How to Use the Gemini Omni 1.2 Flash API: 15-Second Videos in Google Flow and Google Vids](https://useapi.net/docs/articles/gemini-omni-1-2-flash-api?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) · Also in [中文](https://useapi.net/docs/articles/gemini-omni-1-2-flash-api-zh?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)
- All articles: [useapi.net articles](https://useapi.net/docs/articles?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)

## Common questions

<!-- Figures as on the useapi.net Google Vids API overview (docs/api-google-vids-v1/index.md). Official, re-read on the overview 2026-11-06: https://ai.google.dev/gemini-api/docs/pricing, now https://aistudio.google.com/docs/pricing (Omni 1.2 Flash $12.00 per 1M video output tokens at 5,792 tokens per 720p second = ~$0.70 per 10 s, the page's own figure, and $0.104 per 1080p second = $1.56 per 15 s. Was 1.1 Flash $17.50 = ~$1.01). Vids: Ultra $199.99 = 10,000 s/month = ~$0.20 per 10 s, ~$0.30 per 15 s at 720p or 1080p. Allowances (https://support.google.com/docs/answer/15609411, read 2026-10-21, re-read 2026-11-06): Plus 60 s and up to 50 images, Pro 500 s and 30, Ultra $99.99 2,500 s and 300, Ultra $199.99 10,000 s and 1,000. No public Google Vids developer API (Google Workspace developer docs). The useapi.net subscription is not part of the per-clip math. -->

- **Does Google Vids have an API?** Through useapi.net, yes. Google has published no Google Vids API (as of October 2026), and the useapi.net Google Vids API makes Gemini Omni 1.2 Flash video of up to 15 seconds at 720p or 1080p, images and talking avatars in Vids over REST, on your [Google AI subscription](https://gemini.google/subscriptions/). Google offers Vids avatars only in its web app, Vids asks for no captcha, and its allowance is separate from Google Flow's credits.
- **How much does the Google Vids API cost?** Through useapi.net, a 10-second Omni 1.2 Flash clip uses about $0.20 of a Google AI Ultra $199.99 subscription in Vids, against about $0.70 at 720p on Google's metered [Gemini API](https://ai.google.dev/gemini-api/docs/pricing). At 1080p, which uses the same seconds as 720p, a 15-second clip uses about $0.30 against $1.56 on the Gemini API (as of November 2026). Images and avatars use no video seconds, and there is no per-clip charge from useapi.net. The [price table](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#pricing) shows every subscription.
- **How much can I make?** Through useapi.net, as much as your Vids allowance holds: Google AI Plus gets 60 seconds of video a month, Pro 500 seconds, Ultra $99.99 (Ultra 5x) 2,500 seconds and Ultra $199.99 (Ultra 20x) 10,000 seconds, about 1,000 ten-second clips. A free Google account had no video or images in our tests, but can still make avatars at no cost. See [plans and allowances](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api#plans-and-monthly-allowances).
- **Google Vids or Google Flow?** Through useapi.net you can use both: they make Omni Flash video on the same Google AI subscription from separate allowances, so on Ultra $199.99 one Google account connected to both APIs gets about 2,666 ten-second Omni clips a month (about 1,000 with Omni 1.2 in Vids and 1,666 with Omni 1.1 in Flow). Vids adds voiced avatars and needs no captcha, and Flow adds Veo 3.1 and Nano Banana Pro, 2.1 and 2 Lite images. Flow examples: [useapi/google-flow-api](https://github.com/useapi/google-flow-api).
- **How do I connect my Google account?** Through the useapi.net [automated browser setup](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api): sign in with Google in a remote browser once, with no DevTools, cookie copying, Google Cloud project or Gemini API key, and the account is verified and added. To connect by hand, the [Google Account Setup](https://github.com/useapi/google-account-setup) scripts open a clean, single-use browser profile, so the session you copy keeps working.
- **Is the video watermarked?** Through useapi.net you get Google's file unchanged: every Vids clip carries an invisible SynthID watermark and a visible Gemini ✦ in a corner. The free useapi.net [`watermark-remover/`](./watermark-remover) takes the visible ✦ off clips as generated and their upscales (not extended or edited clips) and leaves SynthID untouched.

## 中文说明

这是 [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) 的 Google Vids API 示例代码。通过第三方 REST API 在 Google Vids 中调用 Gemini Omni 1.2 Flash 生成最长 15 秒的视频，支持带配音的虚拟形象（avatar）、参考图片、视频延长（最长约 34 秒）和 1080p 放大。

- 使用你的付费 Google AI 订阅（Plus $4.99、Pro $19.99、Ultra $99.99 或 Ultra $199.99 每月，2026 年 11 月价格），按 Vids 每月额度（视频秒数和图片数）计算，与 Google Flow 的积分分开。
- 无需验证码（captcha），无需 Google Cloud 项目或 API Key。
- 在 Ultra $199.99 上，一条 15 秒 Omni 1.2 Flash 视频约用 $0.30 的 Vids 额度，`720p` 和 `1080p` 相同，而 Google 的 Gemini API 上 720p 为 $1.04、1080p 为 $1.56（2026 年 11 月）。
- useapi.net 每月 15 美元，含所有 API，每个订阅可连接 3 个 Google 账号，不按条收费。
- `watermark-remover/` 可去除视频右下角可见的 Gemini ✦ 标记，不改动不可见的 SynthID 水印。

中文教程（数字人、视频延长、无需验证码，含 curl 示例）：[如何通过 Google Vids API 用 Gemini Omni 1.2 Flash 生成会说话的数字人视频](https://useapi.net/docs/articles/google-vids-api-zh?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)。完整文档：[Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)。

## 日本語の説明

[useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) の Google Vids API のサンプルです。サードパーティの REST API で、Google Vids の Gemini Omni 1.2 Flash を使って最長15秒の動画を生成し、声付きのアバター、参照画像、最長約34秒までの延長、1080p へのアップスケールに対応しています。

- 有料の Google AI のプランで動きます：Plus $4.99、Pro $19.99、Ultra $99.99、Ultra $199.99（月額、2026年11月時点）。使うのは Vids の月間利用枠（動画の秒数と画像）で、Google Flow のクレジットとは別枠です。
- CAPTCHA も、Google Cloud プロジェクトも、API キーも不要です。
- Google アカウントは、自動化されたブラウザーの手順で接続します。リモートのブラウザーで Google に一度ログインするだけで、Cookie をコピーする必要はありません。
- コスト：Ultra $199.99 では、15秒の Omni 1.2 Flash 動画1本が Vids の利用枠で約 $0.30 で、`720p` でも `1080p` でも同じです。Google の Gemini API では 720p で $1.04、1080p で $1.56 です（2026年11月時点）。useapi.net は月 $15 で、すべての API と、サブスクリプションごとに3つの Google アカウントが含まれ、動画ごとの料金はかかりません。
- サンプルでは、2体の声付きアバターが商品を紹介する30秒の動画を作り、写真から作ったアバターに最長30秒の台本を読ませ、30種類の Gemini の声で音声を作ります。`watermark-remover/` は、動画の右下に見える Gemini の ✦ を消します（目に見えない SynthID の透かしには手を加えません）。

日本語の記事：[Google Vids API でアバターを使った AI インフルエンサー動画を作る方法](https://useapi.net/docs/articles/google-vids-influencer-avatars-ja?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)、[Gemini Omni 1.2 Flash API の使い方：Google Flow と Google Vids で15秒の動画を生成](https://useapi.net/docs/articles/gemini-omni-1-2-flash-api-ja?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)。ドキュメント全体：[Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)。

## Sobre este repositório

Exemplos da Google Vids API da [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api), uma API REST de terceiros que gera no Google Vids vídeos Gemini Omni 1.2 Flash de até 15 segundos, com avatares com voz, imagens de referência, extensões até cerca de 34 segundos e upscale para 1080p.

- Roda na sua assinatura paga do Google AI: Plus $4,99, Pro $19,99, Ultra $99,99 ou Ultra $199,99 por mês (preços de novembro de 2026). Gasta a cota mensal do Vids (segundos de vídeo e imagens), separada dos créditos do Google Flow.
- Sem captcha, sem projeto no Google Cloud e sem chave de API.
- A conta Google é conectada por um fluxo automatizado no navegador: você entra no Google uma vez, sem copiar cookies.
- Custo: no Ultra $199,99, um vídeo Omni 1.2 Flash de 15 segundos gasta cerca de $0,30 da cota do Vids, igual em `720p` e `1080p`, contra $1,04 em 720p e $1,56 em 1080p na Gemini API do Google (novembro de 2026). A useapi.net custa $15 por mês, com todas as APIs e 3 contas Google por assinatura, sem cobrança por vídeo.
- Os exemplos fazem dois avatares com voz apresentarem um produto em um clipe estendido até 30 segundos, transformam uma foto em um avatar falante que lê o seu roteiro em até 30 segundos, geram voz em 30 vozes do Gemini, e `watermark-remover/` tira o ✦ visível do Gemini sem tocar na marca d'água invisível SynthID.

Artigos em português: [Como fazer vídeos de influenciador com IA usando avatares pela Google Vids API](https://useapi.net/docs/articles/google-vids-influencer-avatars-pt?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) e [Como usar a API do Gemini Omni 1.2 Flash](https://useapi.net/docs/articles/gemini-omni-1-2-flash-api-pt?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api). Documentação completa: [Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api).

## Về repo này

Ví dụ cho Google Vids API của [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api), một REST API của bên thứ ba chạy Gemini Omni 1.2 Flash trong Google Vids: video dài tới 15 giây với avatar có giọng nói, ảnh tham chiếu, kéo dài tới khoảng 34 giây và upscale lên 1080p, video avatar biết nói từ một bức ảnh, và giọng nói với 30 giọng Gemini.

- Chạy trên gói Google AI trả phí của bạn: Ultra $199,99, Ultra $99,99, Pro $19,99 hoặc Plus $4,99 mỗi tháng (giá tháng 11/2026), dùng hạn mức Vids hằng tháng (giây video và ảnh), tách biệt với credit Google Flow.
- Không có captcha, không cần dự án Google Cloud hay API key.
- Tài khoản Google được kết nối bằng quy trình trình duyệt tự động: đăng nhập Google một lần trong trình duyệt từ xa, không cần chép cookie.
- Chi phí: trên Ultra $199,99, một video Omni 1.2 Flash dài 15 giây dùng khoảng $0,30 hạn mức Vids, ở `720p` hay `1080p` đều như nhau, so với $1,04 ở 720p và $1,56 ở 1080p trên Gemini API của Google (tháng 11/2026). useapi.net giá $15 mỗi tháng, gồm mọi API và 3 tài khoản Google mỗi gói đăng ký, không tính phí theo clip.
- Các ví dụ cho hai avatar có giọng nói giới thiệu sản phẩm trong một clip kéo dài lên 30 giây, biến một bức ảnh thành avatar đọc kịch bản của bạn trong video 30 giây, đọc một câu chuyện thành file giọng nói, và gỡ dấu ✦ Gemini nhìn thấy được khỏi video (không động tới watermark SynthID vô hình).

Bài viết tiếng Việt: [Cách làm video người có ảnh hưởng AI với avatar qua Google Vids API](https://useapi.net/docs/articles/google-vids-influencer-avatars-vi?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) và [Cách dùng Gemini Omni 1.2 Flash API: video 15 giây trong Google Flow và Google Vids](https://useapi.net/docs/articles/gemini-omni-1-2-flash-api-vi?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api). Tài liệu đầy đủ: [Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api).

## Tentang repo ini

Ini adalah contoh kode Google Vids API dari [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api), API pihak ketiga untuk membuat video Gemini Omni 1.2 Flash hingga 15 detik di Google Vids lewat REST API, dengan avatar bersuara, gambar referensi, perpanjangan hingga sekitar 34 detik, upscale 1080p, video avatar bicara dari foto hingga 30 detik, dan speech dengan 30 suara Gemini.

- Berjalan di paket Google AI berbayar Anda (Plus $4,99, Pro $19,99, Ultra $99,99 atau Ultra $199,99 per bulan, harga per November 2026) dan memakai kuota bulanan Vids (detik video dan gambar), terpisah dari kredit Google Flow.
- Tanpa captcha, tanpa project Google Cloud atau API key. Google tidak menerbitkan API untuk Google Vids.
- Akun dihubungkan lewat [setup browser otomatis](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api): login ke Google sekali di browser jarak jauh, tanpa menyalin cookie.
- Harga: di Ultra $199,99, satu video Omni 1.2 Flash 15 detik memakai kuota Vids senilai sekitar $0,30, sama untuk `720p` dan `1080p`, dibanding $1,04 (720p) dan $1,56 (1080p) di Gemini API Google (per November 2026). Langganan useapi.net $15 per bulan untuk semua API, dengan 3 akun Google per langganan, tanpa biaya per video.
- Contoh di repo: `influencer-avatars/` membuat dua avatar bersuara yang memperkenalkan produk dalam klip 10 detik yang diperpanjang ke 30 detik, `talking-avatar/` membuat avatar bicara dari foto dan speech saja, ditambah aplikasi n8n, agent skill untuk Claude Code dan Codex, serta `watermark-remover/` yang menghapus tanda ✦ Gemini yang terlihat tanpa menyentuh watermark SynthID.

Artikel bahasa Indonesia: [Cara Membuat Video Influencer AI dengan Avatar lewat Google Vids API](https://useapi.net/docs/articles/google-vids-influencer-avatars-id?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) dan [Cara Memakai Gemini Omni 1.2 Flash API: Video 15 Detik di Google Flow dan Google Vids](https://useapi.net/docs/articles/gemini-omni-1-2-flash-api-id?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api). Dokumentasi lengkap: [Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api).

## เกี่ยวกับ repo นี้

นี่คือตัวอย่างโค้ด Node.js และ Python สำหรับ Google Vids API ของ [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) ซึ่งเป็น API ของบุคคลที่สาม ใช้สร้างวิดีโอ Gemini Omni 1.2 Flash ยาวสูงสุด 15 วินาทีใน Google Vids พร้อมอวตารที่มีเสียงพูด ภาพอ้างอิง การต่อความยาว (ยาวได้ราว 34 วินาที) และการอัปสเกลเป็น 1080p

- ใช้แพ็กเกจ Google AI แบบเสียเงินของคุณ (Plus $4.99, Pro $19.99, Ultra $99.99 หรือ Ultra $199.99 ต่อเดือน ราคา ณ พฤศจิกายน 2026) โดยใช้โควตา Vids รายเดือน (วินาทีวิดีโอและจำนวนภาพ) ซึ่งแยกจากเครดิต Google Flow
- ไม่ต้องมี captcha ไม่ต้องมีโปรเจกต์ Google Cloud หรือ API key
- เชื่อมบัญชี Google ครั้งเดียวผ่าน[หน้าตั้งค่า Google Vids](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) แล้วเรียก API ด้วย API token ของ useapi.net
- ราคา: บน Ultra $199.99 วิดีโอ Omni 1.2 Flash ยาว 15 วินาทีใช้โควตา Vids ราว $0.30 ทั้ง `720p` และ `1080p` เทียบกับ $1.04 (720p) และ $1.56 (1080p) บน Gemini API ของ Google (ข้อมูล ณ พฤศจิกายน 2026) ค่าบริการ useapi.net คือ $15 ต่อเดือน รวมทุก API ไม่คิดเงินต่อคลิป
- ตัวอย่างใน repo: `influencer-avatars/` อวตารมีเสียงสองตัวนำเสนอสินค้าในคลิป 10 วินาทีที่ต่อเป็น 30 วินาที `talking-avatar/` เปลี่ยนรูปถ่ายเป็นอวตารที่อ่านสคริปต์ของคุณได้ยาวสูงสุด 30 วินาที พร้อมตัวอย่างเสียงพูดแยก และยังมี agent skill, แอป n8n และ `watermark-remover/` ที่ลบเครื่องหมาย ✦ ของ Gemini ที่มองเห็นได้

บทความภาษาไทย: [วิธีสร้างวิดีโอ AI Influencer ด้วยอวตารผ่าน Google Vids API](https://useapi.net/docs/articles/google-vids-influencer-avatars-th?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) และ [วิธีใช้ Gemini Omni 1.2 Flash API: วิดีโอ 15 วินาทีใน Google Flow และ Google Vids](https://useapi.net/docs/articles/gemini-omni-1-2-flash-api-th?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) เอกสารฉบับเต็ม: [Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api)

## About useapi.net

[useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) is a third-party REST API for AI services, not affiliated with Google. The [Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) runs on your Google AI subscription, so you spend its monthly Vids allowance instead of paying metered developer-API prices.

Visit our [Discord Server](https://discord.gg/w28uK3cnmF) or [Telegram Channel](https://t.me/use_api) for any support questions and concerns.

Latest video: [Gemini Omni 1.2 Flash in Google Vids: 15 seconds from one prompt, extended to 25](https://www.youtube.com/watch?v=eJ3js18XCBM). We regularly post guides and tutorials on the [YouTube Channel](https://www.youtube.com/@useapi-net).

## License

The example code in this repository is released under the [MIT License](./LICENSE). It covers the example scripts only, not the useapi.net service or API.
