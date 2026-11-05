"""

Script version 1.0, November 4, 2026

Script to turn a script of up to 2,500 characters into speech in one of 30 Gemini voices, using the Google Vids API
by useapi.net

Runs the speech step of the tutorial https://useapi.net/docs/articles/google-vids-influencer-avatars#speech-on-its-own
1. POST /speech with the script and the voice. Speech is usually ready in seconds (20 seconds for the 2,426-character
   smart-fridge.txt), so the request waits for the finished job. If it answers 202 (still running), the script polls
   GET /jobs/{jobid} every 10 seconds.
2. GET /media/{mediaId} downloads the WAV (24 kHz, mono).

Each run uses 1 Gemini use of the account (speech in GET /accounts/{email}). Audio tags in square brackets, such as
[whisper], [short pause] or [sarcasm], are performed, not read aloud.

Installation Instructions:
==========================

You need Python 3.x installed to run this script (standard library only). Download and install Python from:

- Windows, macOS, Linux: https://www.python.org/

After installation, verify by running the following command in a terminal:

   python3 --version

Running the Script:
===================

Usage: python3 speech.py <API_TOKEN> <EMAIL> [SCRIPT_FILE] [VOICE]

Replace API_TOKEN with your actual useapi.net API token, see https://useapi.net/docs/start-here/setup-useapi
Replace EMAIL with the Google account connected to the Google Vids API, see https://useapi.net/docs/start-here/setup-google-vids
If optional SCRIPT_FILE not provided, smart-fridge.txt next to this script will be used.
If optional VOICE not provided, Vira is used. GET /voices lists all 30 (a name such as Vira, or a voice id such as Pulcherrima).

The WAV and the job record are saved to the output folder in the current directory, named after the script file.

Example:
--------

python3 speech.py user:1234-abcdefhijklmnopqrstuv my@email.com
python3 speech.py user:1234-abcdefhijklmnopqrstuv my@email.com my-script.txt Holt

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
from datetime import datetime


# Constants
API = 'https://api.useapi.net/v1/google-vids'
DEFAULT_SCRIPT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'smart-fridge.txt')
DEFAULT_VOICE = 'Vira'
OUTPUT_DIR = 'output'
MAX_SCRIPT = 2500
SLEEP_POLL = 10  # in seconds, how often GET /jobs/{jobid} is read
SLEEP_RETRY = 30  # in seconds, before retrying 429 (busy) or 503
SLEEP_SIGNED_OUT = 60  # in seconds, before retrying 596 (account being re-checked)
MAX_RATE_LIMIT_WAIT = 5 * 60  # in seconds, a 429 with a later retryAt is a used-up allowance
MAX_RETRIES = 10
# api.useapi.net's Cloudflare edge rejects urllib's default User-Agent (error 1010), so send a browser-like one.
USER_AGENT = 'Mozilla/5.0 (compatible; speech.py)'

api_token = None


def elapsed_sec(start):
    return round(time.time() - start)


# Ids contain ':' and '@', so they are URL-encoded whenever they go into a URL path.
def enc(value):
    return urllib.parse.quote(value, safe='')


def fail(message):
    print(f'STOP: {message}', file=sys.stderr)
    sys.exit(1)


def write_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


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
def retry_wait(error):
    code, message, retry_at = error['code'], error['message'], error['retryAt']
    if code == 429:
        if retry_at:
            # Google limiting the account for a minute: retryAt is close. A used-up allowance: retryAt is the monthly reset.
            seconds = parse_iso(retry_at) - time.time()
            return max(seconds, 0) + 5 if seconds <= MAX_RATE_LIMIT_WAIT else None
        if re.search(r'allowance|resets at|used up', message, re.I):
            return None
        return SLEEP_RETRY  # every maxJobs slot busy, or Google's speech service failing for a while
    if code == 503:
        return SLEEP_RETRY  # Google server error, or the job could not be queued
    if code == 596:
        return None if 'Re-add it at' in message else SLEEP_SIGNED_OUT  # the account is being re-checked
    return None


def hint(error):
    if error['code'] == 422:
        return '\n   Google refused the script. Nothing was charged. Change the words and run again.'
    if error['code'] == 403:
        return "\n   The account's Google plan has no speech, or its Google Workspace smart features are off."
    return ''


# POST /speech, sent again only on the answers the docs say to retry (nothing was made). A failed job record comes
# back with the HTTP status in error.code. If no answer arrives at all, it is not sent again: it may have been accepted.
def submit(body):
    attempt = 0
    while True:
        attempt += 1
        try:
            status, response = request('POST', 'speech', body)
        except (urllib.error.URLError, OSError) as e:
            fail(f'POST /speech — no answer from the API ({e}). It may have been accepted, so it is not sent again.')
        if 200 <= status < 300:
            return response

        error = error_of(status, response)
        wait = retry_wait(error)
        if wait is None or attempt >= MAX_RETRIES:
            fail(f'POST /speech — HTTP {status}: {error["message"]}{hint(error)}')
        print(f'POST /speech — HTTP {status}, retry {attempt}/{MAX_RETRIES - 1} in {round(wait)}s: {error["message"]}')
        time.sleep(wait)


# A 202 answer is a job still running: read GET /jobs/{jobid} until it is done.
def wait_for(job, start):
    while job.get('status') == 'processing':
        time.sleep(SLEEP_POLL)
        try:
            status, read = request('GET', f'jobs/{enc(job["jobid"])}')
        except (urllib.error.URLError, OSError):
            continue  # a passing network hiccup: reading the job is free, read it again
        if status == 429 or status >= 500:
            continue
        if status != 200:
            fail(f'GET /jobs — HTTP {status}: {error_of(status, read)["message"]}')
        job = read
        print(f'   {job.get("status")} ({elapsed_sec(start)}s)')
    return job


# GET /media/{mediaId} streams the WAV. It is saved under its final name only once it has fully arrived.
def download(media_id, file):
    temp = f'{file}.part'
    req = urllib.request.Request(f'{API}/media/{enc(media_id)}',
                                 headers={'Authorization': f'Bearer {api_token}', 'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=300) as response, open(temp, 'wb') as f:
            shutil.copyfileobj(response, f)
    except urllib.error.HTTPError as e:
        try:
            message = error_of(e.code, json.loads(e.read().decode('utf-8')))['message']
        except ValueError:
            message = ''
        if os.path.exists(temp):
            os.remove(temp)
        fail(f'GET /media — HTTP {e.code}: {message}')
    os.replace(temp, file)
    print(f'   saved {file}')


def main():
    global api_token
    args = sys.argv[1:]
    if len(args) < 2:
        print('Usage: python3 speech.py <API_TOKEN> <EMAIL> [SCRIPT_FILE] [VOICE]', file=sys.stderr)
        sys.exit(1)
    api_token, email = args[0], args[1]
    script_file = args[2] if len(args) > 2 else DEFAULT_SCRIPT_FILE
    voice = args[3] if len(args) > 3 else DEFAULT_VOICE

    print('Script v1.0')
    print('Python version is: ' + sys.version.split()[0])

    with open(script_file, encoding='utf-8') as f:
        script = f.read().strip()
    if not script or len(script) > MAX_SCRIPT:
        fail(f'{script_file} has {len(script)} characters. A script is 1 to {MAX_SCRIPT} characters.')

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    name = os.path.splitext(os.path.basename(script_file))[0]
    start = time.time()
    print(f'\nSpeech — {len(script)} characters from {script_file}, voice {voice}')

    job = wait_for(submit({'script': script, 'voice': voice, 'email': email}), start)
    write_json(os.path.join(OUTPUT_DIR, f'{name}.json'), job)
    if job.get('status') != 'completed':
        error = error_of(0, job)
        fail(f'Speech — job failed ({error["code"]}): {error["message"]}{hint(error)}')

    result = job['result']
    quota = (result.get('quota') or {}).get('speech')
    print(f'   completed in {elapsed_sec(start)}s: {result.get("duration")}s of speech'
          + (f', {quota["left"]} Gemini uses left' if quota else ''))
    download(result['mediaId'], os.path.join(OUTPUT_DIR, f'{name}.wav'))


if __name__ == '__main__':
    main()
