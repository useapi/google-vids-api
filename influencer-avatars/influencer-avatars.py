"""

Script version 1.0, October 8, 2026

Script to make a talking AI influencer video with voiced avatars using the Google Vids API v1 by useapi.net 🚀

Runs the pipeline of the tutorial https://useapi.net/docs/articles/google-vids-influencer-avatars
1. Two images with POST /images: Mia's portrait and the AeroLoop product shot.
2. Two voiced avatars with POST /avatars: Mia from her portrait, Leo drawn by Google from a description.
3. A 10-second Gemini Omni 1.1 Flash launch clip with POST /videos: avatar_1 + avatar_2 + referenceImage_1 (the product).
4. Two 10-second extends with POST /videos/extend, to 20 and to 30 seconds.
5. A 1080p upscale of the 20-second clip with POST /videos/upscale (it takes clips of up to 20 seconds).

Every generation runs async: the script submits it with async: true, polls GET /jobs/{jobid} every 10 seconds and
downloads the result with GET /media/{mediaId}. Every step is read from prompts.json.

Every finished step is saved to output/influencer_state.json, so running the script again continues where it stopped
instead of spending your Vids allowance on the finished steps again. The full run uses 50 seconds of video
(10 + 10 + 10, plus 20 for the upscale) and 3 images (the two images and Leo's drawn avatar).

Installation Instructions:
==========================

You need Python 3.x installed to run this script (standard library only). Download and install Python from:

- Windows, macOS, Linux: https://www.python.org/

After installation, verify by running the following command in a terminal:

   python3 --version

Running the Script:
===================

Usage: python3 influencer-avatars.py <API_TOKEN> <EMAIL> [PROMPTS_FILE] [--cleanup]

Replace API_TOKEN with your actual useapi.net API token, see https://useapi.net/docs/start-here/setup-useapi
Replace EMAIL with the Google account connected to the Google Vids API, see https://useapi.net/docs/start-here/setup-google-vids
If optional PROMPTS_FILE not provided, prompts.json next to this script will be used.

Results are saved to the output folder in the current directory. To redo one step, delete its entry from
output/influencer_state.json and run again.

The avatars stay in your account's Vids document, ready for more videos, until you delete them. Run the script
again with --cleanup to delete the avatars this script created (only those, listed in output/influencer_state.json).

Example:
--------

python3 influencer-avatars.py user:1234-abcdefhijklmnopqrstuv my@email.com
python3 influencer-avatars.py user:1234-abcdefhijklmnopqrstuv my@email.com --cleanup

Changelog:
==========

- October 8, 2026: Initial release.

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
STATE_FILE = os.path.join(OUTPUT_DIR, 'influencer_state.json')
SLEEP_POLL = 10  # in seconds, how often GET /jobs/{jobid} is read
SLEEP_RETRY = 30  # in seconds, before retrying 429 (busy) or 503
SLEEP_SIGNED_OUT = 60  # in seconds, before retrying 596 (account being re-checked)
MAX_RATE_LIMIT_WAIT = 5 * 60  # in seconds, a 429 with a later retryAt is a used-up allowance
MAX_RETRIES = 10
# api.useapi.net's Cloudflare edge rejects urllib's default User-Agent (error 1010), so send a browser-like one.
USER_AGENT = 'Mozilla/5.0 (compatible; influencer-avatars.py)'

AVATAR_KEYS = ['avatar_1', 'avatar_2', 'avatar_3']
IMAGE_KEYS = ['referenceImage_1', 'referenceImage_2', 'referenceImage_3']


def elapsed_sec(start):
    return round(time.time() - start)


# Ids contain ':' and '@', so they are URL-encoded whenever they go into a URL path.
def enc(value):
    return urllib.parse.quote(value, safe='')


def fail(message):
    print(f'🛑 {message}', file=sys.stderr)
    sys.exit(1)


# --- saved progress -----------------------------------------------------------
# images: name → { mediaId }   avatars: name → { avatarId, previewMediaId? }
# clips: name → { mediaId, duration, resolution }   jobs: name → jobid of a submitted job not yet finished
state = {'email': None, 'images': {}, 'avatars': {}, 'clips': {}, 'jobs': {}}


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
def request(method, url, body=None):
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {api_token}', 'User-Agent': USER_AGENT}
    data = None
    if body is not None:
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
        return SLEEP_SIGNED_OUT if avatar else SLEEP_RETRY  # every maxJobs slot busy, or a short limit
    if code == 503:
        return SLEEP_RETRY  # Google server error, or the job could not be queued
    if code == 596:
        return None if 'Re-add it at' in message else SLEEP_SIGNED_OUT  # the account is being re-checked
    if code == 502 and avatar:
        return SLEEP_RETRY  # "Google did not keep the avatar in the Vids document, please retry"
    return None


def hint(message):
    if re.search(r'expired', message, re.I):
        return f'\n   A generated image lasts a few hours only. Delete its entry under "images" in {STATE_FILE} and run again to make it again.'
    return ''


# POST with retries on the answers the docs say to retry. If no answer arrives at all, it is unclear whether the API
# accepted the request, so it is never sent again automatically: a paid step must not run twice.
def post(url, body, what, avatar=False):
    attempt = 0
    while True:
        attempt += 1
        try:
            status, response = request('POST', url, body)
        except (urllib.error.URLError, OSError) as e:
            fail(f'{what} — no answer from the API ({e}). It may have been accepted, so it is not sent again.\n'
                 f'   Check {"GET /avatars" if avatar else "GET /jobs"} before running the script again.')
        if 200 <= status < 300:
            return response

        error = error_of(status, response)
        wait = retry_wait(error, avatar)
        if wait is None or attempt >= MAX_RETRIES:
            fail(f'{what} — HTTP {status}: {error["message"]}{hint(error["message"])}')
        print(f'🔄️ {what} — HTTP {status}, retry {attempt}/{MAX_RETRIES - 1} in {round(wait)}s: {error["message"]}')
        time.sleep(wait)


# Submit a job with async: true (or pick up the job a stopped run left behind), then poll GET /jobs/{jobid} until it
# completes. A failed job is sent again only when Google refused it with a short rate limit (429 with retryAt about a
# minute away), which makes nothing and costs nothing. Any other failure stops the script: a job can fail after Google
# made and charged the clip (we saw 503 "Google answered without a video" use the clip's seconds), so it is not sent
# again automatically. Running the script again retries the step.
def run_job(name, url, body):
    start = time.time()
    attempt = 0
    while True:
        attempt += 1
        jobid = state['jobs'].get(name)
        if jobid:
            print(f'   ♻️  {name} — picking up job {jobid}')
        else:
            job = post(url, {**body, 'async': True}, f'POST /{url} ({name})')
            jobid = job['jobid']
            state['jobs'][name] = jobid
            save_state()
            print(f'   ⏳ {name} — job {jobid}')

        while True:
            time.sleep(SLEEP_POLL)
            try:
                status, job = request('GET', f'jobs/{enc(jobid)}')
            except (urllib.error.URLError, OSError):
                continue  # a passing network hiccup: reading the job is free, read it again
            if status == 429 or status >= 500:
                continue
            if status != 200:
                fail(f'GET /jobs ({name}) — HTTP {status}: {error_of(status, job)["message"]}')
            if job.get('status') != 'processing':
                break
            print(f'   ⌛ {name} — processing ({elapsed_sec(start)}s)')

        del state['jobs'][name]
        save_state()
        write_json(os.path.join(OUTPUT_DIR, f'{name}.json'), job)

        if job['status'] == 'completed':
            result = job['result']
            quota = result.get('quota') or {}
            left = f'{quota["video"]["left"]}s of video left' if quota.get('video') else \
                f'{quota["image"]["left"]} images left' if quota.get('image') else ''
            size = f'{result["width"]}×{result["height"]}'
            print(f'✅ {name} — completed in {elapsed_sec(start)}s (Google {round(result["elapsedMs"] / 1000)}s)'
                  + (f', {result["duration"]}s at {result["resolution"]} {size}' if result.get('duration') else f', {size}')
                  + (f', {left}' if left else ''))
            return job

        error = error_of(0, job)
        wait = retry_wait(error) if error['code'] == 429 and error['retryAt'] else None
        if wait is None or attempt >= MAX_RETRIES:
            fail(f'{name} — job failed ({error["code"]}): {error["message"]}{hint(error["message"])}'
                 + ('\n   Google may have made and charged it, so the script does not send it again. Run the script again to retry this step.'
                    if error['code'] in (502, 503, 504) else ''))
        print(f'🔄️ {name} — job failed ({error["code"]}), submitting again in {round(wait)}s: {error["message"]}')
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
            print(f'   💾 {file}')
            return
        except urllib.error.HTTPError as e:
            try:
                message = error_of(e.code, json.loads(e.read().decode('utf-8')))['message']
            except ValueError:
                message = ''
            if os.path.exists(temp):
                os.remove(temp)
            if e.code != 502:
                print(f'⛔ Unable to download {file} (HTTP {e.code}): {message}', file=sys.stderr)
                return
        except (urllib.error.URLError, OSError) as e:
            if os.path.exists(temp):
                os.remove(temp)
            print(f'⛔ Download of {file} broke off: {e}', file=sys.stderr)
        time.sleep(SLEEP_POLL)
    print(f'⛔ Unable to download {file}. Run the script again to retry the download.', file=sys.stderr)


# --- prompts.json -------------------------------------------------------------

# Check prompts.json before anything is spent. Returns (images, seconds) the steps not yet done will use.
def validate(config):
    warnings = []
    images = config.get('images') or []
    avatars = config.get('avatars') or []
    extends_list = config.get('extends') or []
    launch = config.get('launch')
    upscale = config.get('upscale')
    names = set()

    def named(what, name):
        if not name:
            warnings.append(f'{what} has no name')
        elif name in names:
            warnings.append(f'the name "{name}" is used twice')
        names.add(name)

    def check_duration(what, d):
        if d is not None and not (isinstance(d, int) and 3 <= d <= 10):
            warnings.append(f'{what}: duration must be 3 to 10 seconds')

    image_names = [i.get('name') for i in images]
    avatar_names = [a.get('name') for a in avatars]
    for image in images:
        named('an image', image.get('name'))
        if not image.get('prompt'):
            warnings.append(f'image {image.get("name")}: prompt is required')
    for avatar in avatars:
        if not avatar.get('name'):
            warnings.append('an avatar has no name')
        if not avatar.get('voice'):
            warnings.append(f'avatar {avatar.get("name")}: voice is required')
        if bool(avatar.get('image')) == bool(avatar.get('appearance')):
            warnings.append(f'avatar {avatar.get("name")}: give either image or appearance')
        if avatar.get('image') and avatar['image'] not in image_names:
            warnings.append(f'avatar {avatar.get("name")}: no image named "{avatar["image"]}"')
    if not launch:
        fail('launch is required in the prompts file')
    named('launch', launch.get('name'))
    if not launch.get('prompt'):
        warnings.append('launch: prompt is required')
    check_duration('launch', launch.get('duration'))
    allowed = ['name', 'prompt', 'duration', 'resolution', 'aspectRatio'] + AVATAR_KEYS + IMAGE_KEYS
    unknown = [key for key in launch if key not in allowed]
    if unknown:
        warnings.append(f'launch: parameters not supported by this script: {", ".join(unknown)}')
    for key in AVATAR_KEYS:
        if launch.get(key) and launch[key] not in avatar_names:
            warnings.append(f'launch: {key} names no avatar "{launch[key]}"')
    for key in IMAGE_KEYS:
        if launch.get(key) and launch[key] not in image_names:
            warnings.append(f'launch: {key} names no image "{launch[key]}"')
    if len([key for key in AVATAR_KEYS + IMAGE_KEYS if launch.get(key)]) > 3:
        warnings.append('launch: up to 3 avatars and reference images in all')

    # Length and resolution of every clip, to check the upscale and count the seconds.
    clips = {launch.get('name'): {'duration': launch.get('duration', 8), 'resolution': launch.get('resolution', '720p')}}
    previous = launch.get('name')
    for extend in extends_list:
        named('an extend', extend.get('name'))
        if not extend.get('prompt'):
            warnings.append(f'extend {extend.get("name")}: prompt is required')
        check_duration(f'extend {extend.get("name")}', extend.get('duration'))
        source = clips[previous]
        clips[extend.get('name')] = {'duration': source['duration'] + extend.get('duration', 8),
                                     'resolution': extend.get('resolution', source['resolution'])}
        previous = extend.get('name')
    if upscale:
        named('upscale', upscale.get('name'))
        clip = clips.get(upscale.get('clip'))
        if not clip:
            warnings.append(f'upscale: no clip named "{upscale.get("clip")}"')
        elif clip['duration'] > 20:
            warnings.append(f'upscale: {upscale["clip"]} is {clip["duration"]}s, upscale takes clips of up to 20 seconds')
        elif clip['resolution'] != '720p':
            warnings.append(f'upscale: {upscale["clip"]} is not 720p')

    if warnings:
        for warning in warnings:
            print(f'⚠️  {warning}', file=sys.stderr)
        fail('Execution stopped due to warnings in the prompts file.')

    # What the steps not yet done will use: an image per image and per drawn avatar, a clip's seconds, an extend's
    # added seconds, and the whole clip's seconds again for the upscale.
    need_images = len([i for i in images if i['name'] not in state['images']]) + \
        len([a for a in avatars if a.get('appearance') and a['name'] not in state['avatars']])
    need_seconds = 0
    if launch['name'] not in state['clips']:
        need_seconds += clips[launch['name']]['duration']
    for extend in extends_list:
        if extend['name'] not in state['clips']:
            need_seconds += extend.get('duration', 8)
    if upscale and upscale['name'] not in state['clips']:
        need_seconds += clips[upscale['clip']]['duration']
    return need_images, need_seconds


# GET /accounts/{email} reads the account's allowance live from Google.
def check_account(email, need_images, need_seconds):
    try:
        status, account = request('GET', f'accounts/{enc(email)}')
    except (urllib.error.URLError, OSError) as e:
        fail(f'GET /accounts — no answer from the API ({e})')
    if status != 200:
        fail(f'Account {email} — HTTP {status}: {error_of(status, account)["message"]}. '
             'See https://useapi.net/docs/start-here/setup-google-vids')
    health = account.get('health')
    if health and health != 'OK':
        fail(f"Account {email} health is '{health}'. See https://useapi.net/docs/start-here/setup-google-vids")
    quota = account.get('quota') or {}
    video, image = quota.get('video'), quota.get('image')
    print(f'👤 {email}: {video["left"] if video else "?"}s of video and {image["left"] if image else "?"} images left this month'
          f', this run needs {need_seconds}s and {need_images} images')
    if not video or not image:
        print(f'⚠️  Could not read the whole allowance (session: {account.get("session")}), continuing', file=sys.stderr)
    if video and video['left'] < need_seconds:
        fail(f'Not enough video seconds left ({video["left"]} < {need_seconds}). It resets at {video["resetAt"]}')
    if image and image['left'] < need_images:
        fail(f'Not enough images left ({image["left"]} < {need_images}). It resets at {image["resetAt"]}')


# --- the pipeline ---------------------------------------------------------------
def execute(email, prompts_file):
    with open(prompts_file, encoding='utf-8') as f:
        config = json.load(f)
    need_images, need_seconds = validate(config)
    check_account(email, need_images, need_seconds)

    # Step 1 — images, one JPEG per call, pinned to EMAIL: every input of one video must come from the same account.
    for image in config.get('images') or []:
        name = image['name']
        if name not in state['images']:
            print(f'\n🖼️  Image {name}')
            body = {key: value for key, value in image.items() if key != 'name'}
            job = run_job(name, 'images', {**body, 'email': email})
            state['images'][name] = {'mediaId': job['result']['mediaId']}
            save_state()
        download(state['images'][name]['mediaId'], f'{name}.jpg')

    # Step 2 — avatars: a picture plus a fixed voice, saved in the account's Vids document. With `image` (an image from
    # step 1) the avatar is saved on that image's account; with `appearance` Google draws the person.
    # POST /avatars answers when the avatar is saved and is not a job.
    for avatar in config.get('avatars') or []:
        name = avatar['name']
        if name not in state['avatars']:
            print(f'\n🧑 Avatar {name}')
            start = time.time()
            body = dict(avatar)
            if avatar.get('image'):
                body['image'] = state['images'][avatar['image']]['mediaId']
            else:
                body['email'] = email
            saved = post('avatars', body, f'POST /avatars ({name})', avatar=True)
            state['avatars'][name] = {'avatarId': saved['avatarId']}
            if saved.get('previewMediaId'):
                state['avatars'][name]['previewMediaId'] = saved['previewMediaId']
            save_state()
            write_json(os.path.join(OUTPUT_DIR, f'{name.lower()}-avatar.json'), saved)
            print(f'✅ {name} — saved in {elapsed_sec(start)}s, voice {saved["voice"]} ({saved["voiceId"]}, {saved["voiceStyle"]})')
        if state['avatars'][name].get('previewMediaId'):
            download(state['avatars'][name]['previewMediaId'], f'{name.lower()}-avatar.jpg')

    # Step 3 — the launch clip. In prompts.json avatar_N names an avatar and referenceImage_N an image from the steps
    # above; the prompt calls them @avatar_N and @referenceImage_N. The image's mediaId goes in directly.
    launch = dict(config['launch'])
    launch_name = launch.pop('name')
    if launch_name not in state['clips']:
        print(f'\n🎬 Clip {launch_name}')
        for key in AVATAR_KEYS:
            if launch.get(key):
                launch[key] = state['avatars'][launch[key]]['avatarId']
        for key in IMAGE_KEYS:
            if launch.get(key):
                launch[key] = state['images'][launch[key]]['mediaId']
        result = run_job(launch_name, 'videos', launch)['result']
        state['clips'][launch_name] = {'mediaId': result['mediaId'], 'duration': result['duration'], 'resolution': result['resolution']}
        save_state()
    download(state['clips'][launch_name]['mediaId'], f'{launch_name}.mp4')

    # Step 4 — extends. Each adds `duration` seconds and returns the whole clip with a new mediaId. An extend gets the
    # clip and the prompt only, not the avatars, so the prompts name people by what they wear.
    previous = launch_name
    for extend in config.get('extends') or []:
        name = extend['name']
        if name not in state['clips']:
            print(f'\n➕ Extend {previous} → {name}')
            body = {key: value for key, value in extend.items() if key != 'name'}
            result = run_job(name, 'videos/extend', {'mediaId': state['clips'][previous]['mediaId'], **body})['result']
            state['clips'][name] = {'mediaId': result['mediaId'], 'duration': result['duration'], 'resolution': result['resolution']}
            save_state()
        download(state['clips'][name]['mediaId'], f'{name}.mp4')
        previous = name

    # Step 5 — upscale to 1080p. It takes 720p clips of up to 20 seconds and uses the clip's seconds again.
    upscale = config.get('upscale')
    if upscale:
        name, clip = upscale['name'], upscale['clip']
        if name not in state['clips']:
            print(f'\n⬆️  Upscale {clip} → {name}')
            result = run_job(name, 'videos/upscale', {'mediaId': state['clips'][clip]['mediaId']})['result']
            state['clips'][name] = {'mediaId': result['mediaId'], 'duration': result['duration'], 'resolution': result['resolution']}
            save_state()
        download(state['clips'][name]['mediaId'], f'{name}.mp4')

    print(f'\n🎉 Done. Files are in {os.path.abspath(OUTPUT_DIR)}')
    for name, clip in state['clips'].items():
        print(f'   {name}.mp4 — {clip["duration"]}s, {clip["resolution"]}')
    print("\n🧑 Avatars kept in the account's Vids document, reusable as avatar_1..avatar_3 in POST /videos:")
    for name, avatar in state['avatars'].items():
        print(f'   {name}: {avatar["avatarId"]}')
    print('   To delete them, run the script again with --cleanup.')


# DELETE /avatars/{avatarId} for every avatar this script created (as listed in the state file).
def cleanup():
    if not state['avatars']:
        print(f'Nothing to delete: {STATE_FILE} lists no avatars.')
        return
    for name in list(state['avatars']):
        avatar_id = state['avatars'][name]['avatarId']
        try:
            status, response = request('DELETE', f'avatars/{enc(avatar_id)}')
        except (urllib.error.URLError, OSError) as e:
            print(f'⛔ {name} — no answer from the API ({e})', file=sys.stderr)
            continue
        if status in (204, 404):
            print(f'🗑️  {name} — {"deleted" if status == 204 else "already gone"}')
            del state['avatars'][name]
            save_state()
        else:
            print(f'⛔ {name} — HTTP {status}: {error_of(status, response)["message"]}. Run --cleanup again.', file=sys.stderr)


def main():
    global api_token
    args = sys.argv[1:]
    is_cleanup = '--cleanup' in args
    args = [arg for arg in args if arg != '--cleanup']
    if len(args) < 2:
        print('Usage: python3 influencer-avatars.py <API_TOKEN> <EMAIL> [PROMPTS_FILE] [--cleanup]', file=sys.stderr)
        sys.exit(1)
    api_token, email = args[0], args[1]
    prompts_file = args[2] if len(args) > 2 else DEFAULT_PROMPTS_FILE

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
            execute(email, prompts_file)
    finally:
        print('COMPLETED', datetime.now(timezone.utc).isoformat())
        print('EXECUTION ELAPSED', f'{elapsed_sec(start)} seconds')


if __name__ == '__main__':
    main()
