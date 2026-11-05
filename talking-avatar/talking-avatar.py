"""

Script version 1.0, November 4, 2026

Script to make a talking avatar video of up to 30 seconds from a photo, using the Google Vids API by useapi.net

Runs the talking avatar steps of the tutorial
https://useapi.net/docs/articles/google-vids-influencer-avatars#a-talking-avatar-from-a-photo
1. Upload the photo with POST /assets to the account EMAIL.
2. Make a voiced avatar from it with POST /avatars: image + refine (a change in words) + name + voice.
3. Have the avatar read the script with POST /videos/avatar: a 1280x720 talking-head MP4 with sound, as long as the
   speech (up to 30 seconds). It runs async: the script submits it with async: true, polls GET /jobs/{jobid} every
   10 seconds and downloads the MP4 with GET /media/{mediaId}.

The avatar and the script are read from prompts.json. Every finished step is saved to output/talking_avatar_state.json,
so running the script again continues where it stopped instead of paying for a finished step again.

What it uses: the avatar takes 2 images on a plan with images (the reframed photo and the refine), nothing on a plan
without them. The video takes 1 AI avatar video and 1 Gemini use (for its speech), and no video seconds.

Installation Instructions:
==========================

You need Python 3.x installed to run this script (standard library only). Download and install Python from:

- Windows, macOS, Linux: https://www.python.org/

After installation, verify by running the following command in a terminal:

   python3 --version

Running the Script:
===================

Usage: python3 talking-avatar.py <API_TOKEN> <EMAIL> <PHOTO> [PROMPTS_FILE] [--cleanup]

Replace API_TOKEN with your actual useapi.net API token, see https://useapi.net/docs/start-here/setup-useapi
Replace EMAIL with the Google account connected to the Google Vids API, see https://useapi.net/docs/start-here/setup-google-vids
Replace PHOTO with a JPEG, PNG or WebP photo of one person facing the camera (not a famous person, not a minor).
If optional PROMPTS_FILE not provided, prompts.json next to this script will be used.

Results are saved to the output folder in the current directory. To redo a step, delete its entry ("avatar" or
"video") from output/talking_avatar_state.json and run again.

The avatar stays in your account's Vids document until you delete it. Run the script again with --cleanup to delete
the avatar this script created (only that one, listed in output/talking_avatar_state.json).

Example:
--------

python3 talking-avatar.py user:1234-abcdefhijklmnopqrstuv my@email.com photo.jpg
python3 talking-avatar.py user:1234-abcdefhijklmnopqrstuv my@email.com --cleanup

Changelog:
==========

- November 4, 2026: Initial release.

"""

import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


# Constants
API = 'https://api.useapi.net/v1/google-vids'
DEFAULT_PROMPTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prompts.json')
OUTPUT_DIR = 'output'
STATE_FILE = os.path.join(OUTPUT_DIR, 'talking_avatar_state.json')
SLEEP_POLL = 10  # in seconds, how often GET /jobs/{jobid} is read
SLEEP_RETRY = 30  # in seconds, before retrying 429 (busy) or 503
SLEEP_SIGNED_OUT = 60  # in seconds, before retrying 596 (account being re-checked)
MAX_RATE_LIMIT_WAIT = 5 * 60  # in seconds, a 429 with a later retryAt is a used-up allowance
MAX_RETRIES = 10
PHOTO_TYPES = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
# api.useapi.net's Cloudflare edge rejects urllib's default User-Agent (error 1010), so send a browser-like one.
USER_AGENT = 'Mozilla/5.0 (compatible; talking-avatar.py)'


def elapsed_sec(start):
    return round(time.time() - start)


# Ids contain ':' and '@', so they are URL-encoded whenever they go into a URL path.
def enc(value):
    return urllib.parse.quote(value, safe='')


def fail(message):
    print(f'STOP: {message}', file=sys.stderr)
    sys.exit(1)


# --- saved progress -----------------------------------------------------------
# avatar: { avatarId, previewMediaId }   job: jobid of a submitted video not yet finished
# video: { mediaId, duration, speechDuration }
state = {'email': None, 'avatar': None, 'job': None, 'video': None}


def load_state():
    try:
        with open(STATE_FILE, encoding='utf-8') as f:
            state.update(json.load(f))
    except FileNotFoundError:
        pass  # no state file yet: a fresh run


def save_state():
    write_json(STATE_FILE, state)


def write_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


# --- HTTP ---------------------------------------------------------------------
api_token = None


# Returns (status, json). Raises urllib.error.URLError / OSError only when no answer arrived at all (network error).
# A dict body is sent as JSON, bytes as the raw request body with its content_type (POST /assets).
def request(method, url, body=None, content_type=None):
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {api_token}', 'User-Agent': USER_AGENT}
    data = None
    if isinstance(body, bytes):
        headers['Content-Type'] = content_type
        data = body
    elif body is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(f'{API}/{url}', data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            status, text = response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read().decode('utf-8', errors='replace')
    try:
        parsed = json.loads(text) if text else {}
    except ValueError:
        parsed = {'error': text}
    return status, parsed


# An error answer is { error: "…", code } or a failed job record { …, error: { code, message, retryAt } }.
def error_of(status, body):
    error = body.get('error') if isinstance(body, dict) else None
    if isinstance(error, dict):
        return {'code': error.get('code', status), 'message': error.get('message', ''), 'retryAt': error.get('retryAt')}
    return {'code': status, 'message': error if isinstance(error, str) else json.dumps(body), 'retryAt': None}


def parse_iso(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


# How long to wait before sending a refused request again, or None when sending it again won't help.
# Every case below is one the docs say to retry: nothing was made, so nothing was charged.
def retry_wait(error, avatar=False):
    code, message, retry_at = error['code'], error['message'], error['retryAt']
    if code == 429:
        if retry_at:
            # Google limiting the account for a minute: retryAt is close. A used-up allowance: retryAt is the monthly reset.
            seconds = parse_iso(retry_at) - time.time()
            return max(seconds, 0) + 5 if seconds <= MAX_RATE_LIMIT_WAIT else None
        if re.search(r'allowance|resets at', message, re.I):
            return None
        return SLEEP_RETRY  # every maxJobs slot busy, or a short limit
    if code == 503:
        return SLEEP_RETRY  # Google server error, or the job could not be queued
    if code == 596:
        return None if 'Re-add it at' in message else SLEEP_SIGNED_OUT  # the account is being re-checked
    if code == 502 and avatar:
        return SLEEP_RETRY  # "Google did not keep the avatar in the Vids document, please retry"
    return None


# What to do about the refusals people meet most with talking avatars.
def hint(error):
    code, message = error['code'], error['message']
    if code == 400 and re.search(r'seconds when spoken', message, re.I):
        return ('\n   Shorten the script in prompts.json (or drop a [slow pace] tag) and run again. No AI avatar video was used,'
                '\n   the Gemini use for its speech was. POST /speech in the same voice (speech.py) tells you how long it runs.')
    if code == 422 and re.search(r'still counts', message, re.I):
        return ('\n   Google refused the finished video and still counts it against the AI avatar videos. Restyle the avatar'
                '\n   (change "refine" and delete "avatar" from the state file) or start from another photo.')
    if code == 422:
        return '\n   Google refused the photo, the avatar or the script. Nothing was charged. Try another photo or other words.'
    if re.search(r'expired|HTTP 404 for this image', message, re.I):
        return '\n   The upload expired. Run the script again: it uploads the photo again before it makes the avatar.'
    return ''


# POST with retries on the answers the docs say to retry. If no answer arrives at all, it is unclear whether the API
# accepted the request, so it is never sent again automatically: a paid step must not run twice.
def post(url, body, what, avatar=False, content_type=None):
    attempt = 0
    while True:
        attempt += 1
        try:
            status, response = request('POST', url, body, content_type)
        except (urllib.error.URLError, OSError) as e:
            fail(f'{what} — no answer from the API ({e}). It may have been accepted, so it is not sent again.\n'
                 f'   Check {"GET /avatars" if avatar else "GET /jobs"} before running the script again.')
        if 200 <= status < 300:
            return response

        error = error_of(status, response)
        wait = retry_wait(error, avatar)
        if wait is None or attempt >= MAX_RETRIES:
            fail(f'{what} — HTTP {status}: {error["message"]}{hint(error)}')
        print(f'{what} — HTTP {status}, retry {attempt}/{MAX_RETRIES - 1} in {round(wait)}s: {error["message"]}')
        time.sleep(wait)


# GET /media/{mediaId} streams the file itself (video/mp4 or image/jpeg). It is saved under its final name only once
# it has fully arrived, so a broken download leaves no partial file behind.
def download(media_id, filename):
    file = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file):
        return
    for _ in range(3):
        temp = f'{file}.part'
        req = urllib.request.Request(f'{API}/media/{enc(media_id)}',
                                     headers={'Authorization': f'Bearer {api_token}', 'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=300) as response, open(temp, 'wb') as f:
                shutil.copyfileobj(response, f)
            os.replace(temp, file)
            print(f'   saved {file}')
            return
        except urllib.error.HTTPError as e:
            try:
                message = error_of(e.code, json.loads(e.read().decode('utf-8')))['message']
            except ValueError:
                message = ''
            if os.path.exists(temp):
                os.remove(temp)
            if e.code != 502:
                print(f'Unable to download {file} (HTTP {e.code}): {message}', file=sys.stderr)
                return
        except (urllib.error.URLError, OSError) as e:
            if os.path.exists(temp):
                os.remove(temp)
            print(f'Download of {file} broke off: {e}', file=sys.stderr)
        time.sleep(SLEEP_POLL)
    print(f'Unable to download {file}. Run the script again to retry the download.', file=sys.stderr)


# --- checks before anything is spent --------------------------------------------
def validate(config, photo):
    warnings = []
    avatar = config.get('avatar')
    script = config.get('script') or ''
    if not avatar:
        fail('avatar is required in the prompts file')
    if not avatar.get('name') or len(avatar['name']) > 40:
        warnings.append('avatar: name is required, 1 to 40 characters')
    if not avatar.get('voice'):
        warnings.append('avatar: voice is required (a name or voice id from GET /voices)')
    if len(avatar.get('refine') or '') > 1000:
        warnings.append('avatar: refine is up to 1000 characters')
    if not script or len(script) > 400:
        warnings.append(f'script is required, 1 to 400 characters (it has {len(script)})')
    if not state['avatar'] and not photo:
        warnings.append('PHOTO is required to make the avatar')
    if photo and os.path.splitext(photo)[1].lower() not in PHOTO_TYPES:
        warnings.append('PHOTO must be a .jpg, .jpeg, .png or .webp file')
    if warnings:
        for warning in warnings:
            print(f'WARNING: {warning}', file=sys.stderr)
        fail('Execution stopped due to warnings in the prompts file or the arguments.')


# GET /accounts/{email} reads the account's allowance live from Google. A talking avatar video needs 1 AI avatar video
# (avatarVideo) and 1 Gemini use (speech).
def check_account(email):
    try:
        status, account = request('GET', f'accounts/{enc(email)}')
    except (urllib.error.URLError, OSError) as e:
        fail(f'GET /accounts — no answer from the API ({e})')
    if status != 200:
        fail(f'Account {email} — HTTP {status}: {error_of(status, account)["message"]}. See https://useapi.net/docs/start-here/setup-google-vids')
    health = account.get('health')
    quota = account.get('quota') or {}
    limits = account.get('limits') or {}
    if health and health != 'OK':
        fail(f"Account {email} health is '{health}'. See https://useapi.net/docs/start-here/setup-google-vids")
    if limits.get('avatarVideo') == 0:
        fail(f'Account {email} has no AI avatar videos on its Google plan (monthly limit 0).')

    def left(key):
        return (quota.get(key) or {}).get('left', '?')

    print(f'Account {email}: {left("avatarVideo")} AI avatar videos, {left("speech")} Gemini uses'
          f' and {left("image")} images left this month')
    if not quota:
        print(f'WARNING: Could not read the allowance (session: {account.get("session")}), continuing', file=sys.stderr)
    if not state['video'] and not state['job']:
        if quota.get('avatarVideo') and quota['avatarVideo']['left'] < 1:
            fail(f'No AI avatar videos left. They reset at {quota["avatarVideo"]["resetAt"]}')
        if quota.get('speech') and quota['speech']['left'] < 1:
            fail(f'No Gemini uses (speech) left. They reset at {quota["speech"]["resetAt"]}')


# --- the steps ----------------------------------------------------------------------
def execute(email, photo, prompts_file):
    with open(prompts_file, encoding='utf-8') as f:
        config = json.load(f)
    validate(config, photo)
    check_account(email)
    avatar, script = config['avatar'], config['script']
    slug = re.sub(r'[^a-z0-9]+', '-', avatar['name'].lower())

    # Steps 1 and 2 — upload the photo, then make the avatar from it. An upload is free and temporary, so the photo is
    # uploaded again whenever the avatar still has to be made. POST /avatars answers when the avatar is saved and is
    # not a job. Google reframes the photo into a 16:9 avatar picture, then applies refine.
    if not state['avatar']:
        print(f'\nUpload {photo}')
        with open(photo, 'rb') as f:
            data = f.read()
        asset = post(f'assets?email={enc(email)}', data, 'POST /assets',
                     content_type=PHOTO_TYPES[os.path.splitext(photo)[1].lower()])
        print(f'   {asset["assetId"]} ({asset["bytes"]} bytes)')

        print(f'\nAvatar {avatar["name"]}')
        start = time.time()
        made = post('avatars', {**avatar, 'image': asset['assetId'], 'email': email}, f'POST /avatars ({avatar["name"]})', avatar=True)
        state['avatar'] = {'avatarId': made['avatarId'], 'previewMediaId': made.get('previewMediaId')}
        save_state()
        write_json(os.path.join(OUTPUT_DIR, f'{slug}-avatar.json'), made)
        print(f'   saved in {elapsed_sec(start)}s, voice {made["voice"]} ({made["voiceId"]}, {made["voiceStyle"]})')
    if state['avatar'].get('previewMediaId'):
        download(state['avatar']['previewMediaId'], f'{slug}-avatar.jpg')

    # Step 3 — the talking video. Submitted with async: true (or a job a stopped run left behind is picked up), then
    # GET /jobs/{jobid} is polled until it is done. A failed job is sent again only after a short rate limit (429 with
    # retryAt about a minute away), which made nothing. Any other failure stops the script: Google counts a video it
    # refused while making it (422), so it is never sent again automatically.
    start = time.time()
    attempt = 0
    while not state['video']:
        attempt += 1
        if state['job']:
            print(f'\nVideo — picking up job {state["job"]}')
        else:
            print(f'\nVideo — {len(script)} characters')
            job = post('videos/avatar', {'avatar': state['avatar']['avatarId'], 'script': script, 'async': True}, 'POST /videos/avatar')
            state['job'] = job['jobid']
            save_state()
            print(f'   job {state["job"]}')

        while True:
            time.sleep(SLEEP_POLL)
            try:
                status, job = request('GET', f'jobs/{enc(state["job"])}')
            except (urllib.error.URLError, OSError):
                continue  # a passing network hiccup: reading the job is free, read it again
            if status == 429 or status >= 500:
                continue
            if status != 200:
                fail(f'GET /jobs — HTTP {status}: {error_of(status, job)["message"]}')
            if job.get('status') != 'processing':
                break
            print(f'   processing ({elapsed_sec(start)}s)')

        state['job'] = None
        save_state()
        write_json(os.path.join(OUTPUT_DIR, f'{slug}-talking.json'), job)

        if job['status'] == 'completed':
            result = job['result']
            state['video'] = {'mediaId': result['mediaId'], 'duration': result.get('duration'),
                              'speechDuration': result.get('speechDuration')}
            save_state()
            quota = (result.get('quota') or {}).get('avatarVideo')
            print(f'   completed in {elapsed_sec(start)}s: {result.get("duration")}s (speech {result.get("speechDuration")}s), '
                  f'{result.get("width")}×{result.get("height")}'
                  + (f', {quota["left"]} AI avatar videos left' if quota else ''))
            break

        error = error_of(0, job)
        wait = retry_wait(error) if error['code'] == 429 and error['retryAt'] else None
        if wait is None or attempt >= MAX_RETRIES:
            fail(f'Video — job failed ({error["code"]}): {error["message"]}{hint(error)}'
                 + ('\n   Google may have made and counted it, so the script does not send it again. Run the script again to retry.'
                    if error['code'] in (502, 503, 504) else ''))
        print(f'Video — job failed ({error["code"]}), submitting again in {round(wait)}s: {error["message"]}')
        time.sleep(wait)
    download(state['video']['mediaId'], f'{slug}-talking.mp4')

    print(f'\nDone. Files are in {os.path.abspath(OUTPUT_DIR)}')
    print("The avatar is kept in the account's Vids document, reusable in POST /videos/avatar and as avatar_1 in POST /videos:")
    print(f'   {avatar["name"]}: {state["avatar"]["avatarId"]}')
    print('   To delete it, run the script again with --cleanup.')


# DELETE /avatars/{avatarId} for the avatar this script created (as listed in the state file).
def cleanup():
    if not state['avatar']:
        print(f'Nothing to delete: {STATE_FILE} lists no avatar.')
        return
    try:
        status, response = request('DELETE', f'avatars/{enc(state["avatar"]["avatarId"])}')
    except (urllib.error.URLError, OSError) as e:
        fail(f'DELETE /avatars — no answer from the API ({e})')
    if status not in (204, 404):
        fail(f'DELETE /avatars — HTTP {status}: {error_of(status, response)["message"]}. Run --cleanup again.')
    print(f'Avatar {"deleted" if status == 204 else "already gone"}')
    state['avatar'] = None
    save_state()


def main():
    global api_token
    args = sys.argv[1:]
    is_cleanup = '--cleanup' in args
    args = [arg for arg in args if arg != '--cleanup']
    if len(args) < 2:
        print('Usage: python3 talking-avatar.py <API_TOKEN> <EMAIL> <PHOTO> [PROMPTS_FILE] [--cleanup]', file=sys.stderr)
        sys.exit(1)
    api_token, email = args[0], args[1]
    photo = args[2] if len(args) > 2 else None
    prompts_file = args[3] if len(args) > 3 else DEFAULT_PROMPTS_FILE

    print('Script v1.0')
    print('Python version is: ' + sys.version.split()[0])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    load_state()
    if state['email'] and state['email'] != email:
        fail(f'{STATE_FILE} belongs to {state["email"]}. Use that email, or move the output folder away to start fresh.')
    state['email'] = email

    start = time.time()
    print('START EXECUTION', datetime.now(timezone.utc).isoformat())
    try:
        if is_cleanup:
            cleanup()
        else:
            execute(email, photo, prompts_file)
    finally:
        print('COMPLETED', datetime.now(timezone.utc).isoformat())
        print('EXECUTION ELAPSED', f'{elapsed_sec(start)} seconds')


if __name__ == '__main__':
    main()
