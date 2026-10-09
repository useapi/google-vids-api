#!/usr/bin/env bash
# Edit a generated Vids clip with a prompt (recolour, add an object, restyle) and print the job id.
# Usage: edit.sh <video mediaId> "<the change>" [key=value ...]
#   duration=3..10 (default: the clip's length, at most 10; no longer than the clip)
#   aspectRatio=landscape|portrait  resolution=720p|1080p   (default: the source clip's)
# An edit returns at most 10 seconds (the first 10 of a longer clip) and costs the seconds it returns.
# Google refuses edits of uploaded videos (422, nothing charged): edit clips the API generated.
# Docs: https://useapi.net/docs/api-google-vids-v1/post-google-vids-videos-edit
# This spends Vids seconds and is never retried automatically.
source "$(dirname "$0")/_common.sh"
MEDIA="${1:?Usage: edit.sh <video mediaId> \"<the change>\" [key=value ...]}"
PROMPT="${2:?Usage: edit.sh <video mediaId> \"<the change>\" [key=value ...]}"
shift 2

BODY=$(jq -n --arg m "$MEDIA" --arg p "$PROMPT" '{video: $m, prompt: $p}')
for KV in "$@"; do BODY=$(add_kv "$BODY" "$KV"); done
start_job videos/edit "$BODY"
