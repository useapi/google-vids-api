#!/usr/bin/env bash
# Upscale a 720p Vids clip of up to 20 seconds to 1080p and print the job id.
# Usage: upscale.sh <video mediaId>
# It costs the clip's full length in seconds again. Upscale once, at the end, after any extends or edits.
# Docs: https://useapi.net/docs/api-google-vids-v1/post-google-vids-videos-upscale
# This spends Vids seconds and is never retried automatically.
source "$(dirname "$0")/_common.sh"
MEDIA="${1:?Usage: upscale.sh <video mediaId>}"
start_job videos/upscale "$(jq -n --arg m "$MEDIA" '{mediaId: $m}')"
