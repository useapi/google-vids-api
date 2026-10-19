# Google Vids via useapi.net

This extension connects the hosted useapi.net Google Vids MCP server (`useapi-google-vids`, 16 tools). The tools make Gemini Omni 1.1 Flash video, images and voiced AI avatars in Google Vids, extend, edit and upscale clips, on your own Google AI Pro or Ultra plan.

- Endpoint: https://api.useapi.net/v1/google-vids/mcp (Streamable HTTP), authorized with the user's useapi.net API token in `USEAPI_TOKEN`.
- Before the tools work, the user needs a useapi.net API token (https://useapi.net/docs/start-here/setup-useapi) and an account connected at https://useapi.net/docs/start-here/setup-google-vids.
- If a tool returns 401, ask the user to check `USEAPI_TOKEN` (`gemini extensions config useapi-google-vids`). If it says no account is configured, point them to the setup page above.
- Generations spend the user's own plan credits. Ask before starting paid or long jobs, and report job status and links when they finish.
- Full tool list and limits: https://useapi.net/docs/api-google-vids-v1/mcp

The extension also ships the `google-vids-video` agent skill from `skills/`, which calls the same API with curl and reads `USEAPI_TOKEN` from the environment.

useapi.net is a paid third-party API service ($15/month, covers every useapi.net API), not affiliated with Google.
