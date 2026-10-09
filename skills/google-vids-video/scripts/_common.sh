# Shared helpers for the google-vids-video skill scripts. Sourced, not run.
# Needs: curl, jq. Env: USEAPI_TOKEN (required), USEAPI_EMAIL (optional, which connected Google account to use).
# Written for bash 3.2 and later (the macOS default), so no bash 4 features.
set -euo pipefail

API="${USEAPI_API:-https://api.useapi.net/v1/google-vids}"
: "${USEAPI_TOKEN:?Set USEAPI_TOKEN to your useapi.net API token (https://useapi.net/docs/start-here/setup-useapi)}"
command -v jq > /dev/null || { echo "jq is required (https://jqlang.org/download/)" >&2; exit 1; }

enc() { jq -rn --arg v "$1" '$v|@uri'; }
log() { echo "$(date +%H:%M:%S) $*" >&2; }

# acurl [curl args ...] -> curl with the Authorization header read from stdin (-H @-),
# so the token does not show up in the process list
acurl() { curl "$@" -H @- <<< "Authorization: Bearer $USEAPI_TOKEN"; }

# _call METHOD PATH [JSON_BODY] -> sets CODE (the HTTP status, 000 on a network error) and OUT (a temp file with the body)
_call() {
  local method="$1" path="$2" body="${3:-}"
  OUT=$(mktemp)
  if [ -n "$body" ]; then
    CODE=$(acurl -sS --max-time 320 -o "$OUT" -w '%{http_code}' -H "Content-Type: application/json" -X "$method" "$API/$path" -d "$body") || true
  else
    CODE=$(acurl -sS --max-time 320 -o "$OUT" -w '%{http_code}' -X "$method" "$API/$path") || true
  fi
  CODE="${CODE:-000}"
}

# hint CODE BODY_FILE -> one line on what to do about a failed request or a failed job (stderr).
# CODE is the HTTP status, or error.code of a failed job record.
hint() {
  local code="$1" body
  body=$(cat "$2" 2>/dev/null || true)
  case "$code" in
    000) echo "Hint: no answer from the API (network error or timeout). A generation may still have been accepted: do not resend it blindly; check GET /jobs or the allowance first." >&2 ;;
    400)
      if grep -q 'own photo' <<< "$body"; then
        echo "Hint: an avatar cannot be made from a user's own photo. Describe the person with appearance=..., or make a picture with image.sh and pass image=<mediaId>." >&2
      elif grep -q 'expired' <<< "$body"; then
        echo "Hint: a generated image lasts only a few hours. Make it again with image.sh." >&2
      elif grep -q 'older Vids narrator voice' <<< "$body"; then
        echo "Hint: that avatar uses an old web-app voice the API cannot send. Make a new one with avatar.sh." >&2
      else
        echo "Hint: a parameter was rejected (the error names it). Nothing was charged. See https://useapi.net/docs/api-google-vids-v1" >&2
      fi ;;
    401) echo "Hint: the API token is wrong or missing. Check USEAPI_TOKEN." >&2 ;;
    403)
      if grep -q 'does not belong' <<< "$body"; then
        echo "Hint: that id was made with a different useapi.net API token." >&2
      else
        echo "Hint: this account's Google plan has no Vids allowance for this kind of job (a free account makes avatars only). Use an account on Google AI Pro or Ultra. Nothing was charged." >&2
      fi ;;
    404)
      if grep -q 'expired' <<< "$body"; then
        echo "Hint: the file has expired at Google (videos last 24 h, images a few hours). It cannot be downloaded any more." >&2
      elif grep -q 'Avatar not found' <<< "$body"; then
        echo "Hint: that avatar is not in the account's Vids document (already deleted?). avatar.sh --list shows what is there." >&2
      elif grep -q '^Job \|"Job ' <<< "$body"; then
        echo "Hint: no such job, or its record is older than 15 days." >&2
      else
        echo "Hint: that Google account is not connected. Check USEAPI_EMAIL, or see https://useapi.net/docs/start-here/setup-google-vids" >&2
      fi ;;
    422) echo "Hint: Google refused the prompt or the inputs. Nothing was charged. Rephrase the prompt or change the inputs, then try again." >&2 ;;
    429)
      if grep -q 'left this month\|resets at\|allowance' <<< "$body"; then
        echo "Hint: the month's Vids allowance is used up; it resets at retryAt (1st of the month, 00:00 Pacific). Nothing was charged. Use another account or wait." >&2
      else
        echo "Hint: the account is busy (maxJobs running) or Google is limiting it for about a minute. Nothing was charged; it is safe to send again after a minute (or after retryAt). Do not loop on it." >&2
      fi ;;
    502)
      if grep -q 'please retry\|Retry shortly' <<< "$body"; then
        echo "Hint: Google did not complete the change. It is safe to try once more." >&2
      else
        echo "Hint: Google answered without a file the API could read. Google MAY HAVE CHARGED this job, so running it again is not free. Do not resubmit automatically: tell the user and report the jobid to useapi.net support." >&2
      fi ;;
    503) echo "Hint: Google answered with a server error or the job could not be queued. Try again in a minute or two. In rare cases a failed job was still charged, so check result.quota / the allowance before resubmitting several times." >&2 ;;
    504) echo "Hint: Google did not answer in time. Google may still have made and charged the clip, but it cannot be retrieved. Ask the user before running it again." >&2 ;;
    596)
      if grep -q 'Re-add it' <<< "$body"; then
        echo "Hint: the Google account was signed out and must be reconnected: https://useapi.net/docs/start-here/setup-google-vids" >&2
      else
        echo "Hint: Google reported the account as signed out and it is being re-checked. Retry in about a minute; if it stays that way, reconnect it: https://useapi.net/docs/start-here/setup-google-vids" >&2
      fi ;;
  esac
}

# _finish METHOD PATH -> prints the body of a 2xx answer; anything else prints the error, a hint, and exits 1
_finish() {
  if [ "${CODE:0:1}" != "2" ]; then
    echo "$1 /$2 -> HTTP $CODE: $(cat "$OUT")" >&2
    hint "$CODE" "$OUT"
    rm -f "$OUT"
    exit 1
  fi
  cat "$OUT"
  rm -f "$OUT"
}

# api METHOD PATH [JSON_BODY] -> response body on stdout; a non-2xx answer prints the error and exits 1.
# Never retried: a generation request sent twice could be charged twice.
api() {
  _call "$@"
  _finish "$1" "$2"
}

# api_poll METHOD PATH -> like api, for reads only: a network error, an HTTP 429 or a 5xx is retried
# up to 3 times, 10 s apart (except 596, which means the Google account needs attention)
api_poll() {
  local try=1
  while true; do
    _call "$@"
    case "$CODE" in
      000|429|5??)
        if [ "$CODE" != 596 ] && [ "$try" -le 3 ]; then
          log "$1 /$2 -> HTTP $CODE, retry $try of 3 in 10 s"
          rm -f "$OUT"
          try=$((try + 1))
          sleep 10
          continue
        fi ;;
    esac
    break
  done
  _finish "$1" "$2"
}

# add_kv BODY KEY=VALUE -> BODY with the option added; numbers for the numeric keys, strings otherwise
add_kv() {
  local body="$1" kv="$2" k v
  case "$kv" in *=*) ;; *) echo "Expected key=value, got: $kv" >&2; exit 1 ;; esac
  k="${kv%%=*}"
  v="${kv#*=}"
  case "$k" in
    duration)
      case "$v" in ''|*[!0-9]*) echo "duration must be a whole number of seconds, got: $v" >&2; exit 1 ;; esac
      jq --arg k "$k" --argjson v "$v" '.[$k] = $v' <<< "$body" ;;
    *) jq --arg k "$k" --arg v "$v" '.[$k] = $v' <<< "$body" ;;
  esac
}

# start_job PATH BODY -> POSTs an async job (once, never retried) and prints its job id
start_job() {
  local job id
  job=$(api POST "$1" "$(jq '.async = true' <<< "$2")")
  id=$(jq -r '.jobid // empty' <<< "$job")
  [ -n "$id" ] || { echo "No job id in the answer: $job" >&2; exit 1; }
  log "job $id"
  echo "$id"
}
