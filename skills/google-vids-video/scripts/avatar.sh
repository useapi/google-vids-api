#!/usr/bin/env bash
# Create, list or delete Google Vids avatars (a person's picture plus a fixed voice, used as avatar_1..3).
# Usage:
#   avatar.sh <name> <voice> appearance="<the person>" [outfit=...] [shot=close-up|upper-body|full-body] [expression=...] [details=...]
#   avatar.sh <name> <voice> image=<image mediaId from image.sh>
#   avatar.sh --list            one JSON line per avatar: avatarId, name, voice, email
#   avatar.sh --delete <avatarId>
#   avatar.sh --voices          the 30 voices: name, voice id, style
# Create prints the avatarId on stdout. From a description, Google draws the person (1 Vids image, about
# 20 s) and the picture is saved to OUT_DIR as avatar_<name>.jpg (path on stderr). From an image it is free.
# The voice is a Vids name (Holt) or a Google voice id (Charon), see --voices.
# An avatar cannot be made from a user's own photo (Google requires a live identity check).
# Avatars stay in the account's Vids document until deleted; reuse them by avatarId.
# USEAPI_EMAIL picks the account (for --list, only that account is read).
# Docs: https://useapi.net/docs/api-google-vids-v1/post-google-vids-avatars
DIR="$(dirname "$0")"
source "$DIR/_common.sh"
USAGE='Usage: avatar.sh <name> <voice> appearance="..." | image=<mediaId>  |  --list  |  --delete <avatarId>  |  --voices'

case "${1:-}" in
  "") echo "$USAGE" >&2; exit 1 ;;
  --voices)
    api_poll GET voices | jq -r '.voices[] | "\(.name)\t\(.voice)\t\(.style)"'
    exit 0 ;;
  --list)
    P=avatars
    if [ -n "${USEAPI_EMAIL:-}" ]; then P="avatars?email=$(enc "$USEAPI_EMAIL")"; fi
    R=$(api_poll GET "$P")
    jq -c '.avatars[] | {avatarId, name, voice, voiceStyle, email} + (if .note then {note} else {} end)' <<< "$R"
    jq -r '.errors[]? | "Could not read \(.email): \(.error)"' <<< "$R" >&2
    exit 0 ;;
  --delete)
    ID="${2:?Usage: avatar.sh --delete <avatarId>}"
    api DELETE "avatars/$(enc "$ID")" > /dev/null
    log "deleted avatar"
    exit 0 ;;
esac

NAME="$1"
VOICE="${2:?$USAGE}"
shift 2
BODY=$(jq -n --arg n "$NAME" --arg v "$VOICE" '{name: $n, voice: $v}')
if [ -n "${USEAPI_EMAIL:-}" ]; then BODY=$(jq --arg e "$USEAPI_EMAIL" '.email = $e' <<< "$BODY"); fi
for KV in "$@"; do BODY=$(add_kv "$BODY" "$KV"); done
jq -e 'has("appearance") or has("image")' <<< "$BODY" > /dev/null || { echo "Give appearance=\"<the person>\" or image=<mediaId>. $USAGE" >&2; exit 1; }

# Sent once: drawing the picture uses a Vids image, so it is never retried automatically
R=$(api POST avatars "$BODY")
ID=$(jq -r '.avatarId // empty' <<< "$R")
[ -n "$ID" ] || { echo "No avatarId in the answer: $R" >&2; exit 1; }
log "avatar $(jq -r '"\(.name), voice \(.voice) (\(.voiceId), \(.voiceStyle)), on \(.email)"' <<< "$R")"
PREVIEW=$(jq -r '.previewMediaId // empty' <<< "$R")
if [ -n "$PREVIEW" ]; then
  SAFE=$(printf '%s' "$NAME" | tr -c 'A-Za-z0-9_-' '_')
  FILE=$("$DIR/download.sh" "$PREVIEW" "${OUT_DIR:-.}" "avatar_$SAFE") && log "picture saved to $FILE" || log "could not download the picture (the avatar is fine)"
fi
echo "$ID"
