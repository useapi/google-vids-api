# n8n workflow for the Google Vids API

📖 Published on n8n: [Create talking avatar videos with Google Vids and Gemini Omni 1.1 Flash](https://n8n.io/workflows/20704)

[`google-vids-avatar-app.json`](./google-vids-avatar-app.json) is a ready-to-import [n8n](https://n8n.io) app that makes a **talking avatar video** with **Gemini Omni 1.1 Flash** in Google Vids, on your own Google account. It uses only core n8n nodes, with no community nodes.

![The form](./vids-avatar-app-01-form.png)

1. **The form.** Describe a new presenter or pick one of your saved presenters, choose one of the 30 Gemini voices, write the line and the scene, and pick the format, length (3 to 10 s) and resolution. Add up to 3 more segments, each with its own line, for a video of up to 40 s.
2. **The presenter.** Google Vids draws the presenter as an AI avatar. A page shows the portrait and plays the voice: use it, or re-draw it with a new description. Saved presenters show as a gallery with pictures and voice samples.
3. **The video.** Omni 1.1 Flash films the avatar saying your line at 720p. Each extra segment extends the clip, and a page previews each step and lets you stop early. The optional 1080p upscale runs last, for videos of up to 20 s. Pages carry a resume link.
4. **The result.** The page plays the MP4 with a download link and shows the seconds used, a cost estimate and the avatar ID to reuse.

![The result page](./vids-avatar-app-05-result.png)

Busy accounts and short rate limits are retried. Paid requests are never sent twice: a job that may already be charged stops with its job id.

## Setup

1. Get a [useapi.net API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api) and connect your Google account with the [Google Vids setup](https://useapi.net/docs/start-here/setup-google-vids?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api).
2. In n8n, import `google-vids-avatar-app.json`.
3. Create a **Header Auth** credential: Name `Authorization`, Value `Bearer <your API token>`. Select it on every HTTP Request node.
4. Create a **Basic Auth** credential (any username and password) and select it on **Make a talking avatar**, so only you can open the form and spend your allowance.
5. Publish (activate) the workflow and open the form URL.

**Requirements:** a useapi.net subscription and a Google account on a paid Google AI plan with Google Vids. A clip uses its seconds of the monthly Vids allowance, and a portrait uses 1 image.

Every endpoint is documented in the [Google Vids API reference](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-vids-api).
