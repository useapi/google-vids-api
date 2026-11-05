/*

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

You need Node.js v21 or newer installed to run this script. Download and install Node.js from:

- Windows, macOS, Linux: https://nodejs.org/

After installation, verify by running the following command in a terminal:

   node -v

Running the Script:
===================

Usage: node speech.mjs <API_TOKEN> <EMAIL> [SCRIPT_FILE] [VOICE]

Replace API_TOKEN with your actual useapi.net API token, see https://useapi.net/docs/start-here/setup-useapi
Replace EMAIL with the Google account connected to the Google Vids API, see https://useapi.net/docs/start-here/setup-google-vids
If optional SCRIPT_FILE not provided, smart-fridge.txt next to this script will be used.
If optional VOICE not provided, Vira is used. GET /voices lists all 30 (a name such as Vira, or a voice id such as Pulcherrima).

The WAV and the job record are saved to the output folder in the current directory, named after the script file.

Example:
--------

node speech.mjs user:1234-abcdefhijklmnopqrstuv my@email.com
node speech.mjs user:1234-abcdefhijklmnopqrstuv my@email.com my-script.txt Holt

Changelog:
==========

- November 4, 2026: Initial release.

*/

import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Readable } from 'node:stream';

// Constants
const API = 'https://api.useapi.net/v1/google-vids';
const DEFAULT_SCRIPT_FILE = path.join(path.dirname(fileURLToPath(import.meta.url)), 'smart-fridge.txt');
const DEFAULT_VOICE = 'Vira';
const OUTPUT_DIR = 'output';
const MAX_SCRIPT = 2500;
const SLEEP_POLL = 10 * 1000; // in milliseconds, how often GET /jobs/{jobid} is read
const SLEEP_RETRY = 30 * 1000; // in milliseconds, before retrying 429 (busy) or 503
const SLEEP_SIGNED_OUT = 60 * 1000; // in milliseconds, before retrying 596 (account being re-checked)
const MAX_RATE_LIMIT_WAIT = 5 * 60 * 1000; // in milliseconds, a 429 with a later retryAt is a used-up allowance
const MAX_RETRIES = 10;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const elapsedSec = (start) => Math.round((Date.now() - start) / 1000);

// Ids contain ':' and '@', so they are URL-encoded whenever they go into a URL path.
const enc = encodeURIComponent;

const fail = (message) => {
    console.error(`STOP: ${message}`);
    process.exit(1);
};

let apiToken;

// Returns { status, json }. Throws only when no answer arrived at all (network error).
const request = async (method, url, body) => {
    const response = await fetch(`${API}/${url}`, {
        method,
        headers: {
            'Accept': 'application/json',
            'Authorization': `Bearer ${apiToken}`,
            ...(body ? { 'Content-Type': 'application/json' } : {})
        },
        body: body ? JSON.stringify(body) : undefined
    });
    const text = await response.text();
    let json;
    try { json = text ? JSON.parse(text) : {}; } catch { json = { error: text }; }
    return { status: response.status, json };
};

// An error answer is { error: "…", code } or a failed job record { …, error: { code, message, retryAt } }.
const errorOf = (status, json) => ({
    code: json?.error?.code ?? status,
    message: typeof json?.error === 'string' ? json.error : json?.error?.message ?? JSON.stringify(json),
    retryAt: json?.error?.retryAt
});

// How long to wait before sending a refused request again, or null when sending it again won't help.
// Every case below is one the docs say to retry: nothing was made, so nothing was charged.
const retryWait = ({ code, message, retryAt }) => {
    if (code == 429) {
        if (retryAt) {
            // Google limiting the account for a minute: retryAt is close. A used-up allowance: retryAt is the monthly reset.
            const ms = Date.parse(retryAt) - Date.now();
            return ms <= MAX_RATE_LIMIT_WAIT ? Math.max(ms, 0) + 5000 : null;
        }
        if (/allowance|resets at|used up/i.test(message)) return null;
        return SLEEP_RETRY; // every maxJobs slot busy, or Google's speech service failing for a while
    }
    if (code == 503) return SLEEP_RETRY; // Google server error, or the job could not be queued
    if (code == 596) return /Re-add it at/.test(message) ? null : SLEEP_SIGNED_OUT; // the account is being re-checked
    return null;
};

const hint = ({ code }) => code == 422
    ? '\n   Google refused the script. Nothing was charged. Change the words and run again.'
    : code == 403
        ? '\n   The account\'s Google plan has no speech, or its Google Workspace smart features are off.'
        : '';

// POST /speech, sent again only on the answers the docs say to retry (nothing was made). A failed job record comes
// back with the HTTP status in error.code. If no answer arrives at all, it is not sent again: it may have been accepted.
const submit = async (body) => {
    for (let attempt = 1; ; attempt++) {
        let response;
        try {
            response = await request('POST', 'speech', body);
        } catch (error) {
            fail(`POST /speech — no answer from the API (${error.message}). It may have been accepted, so it is not sent again.`);
        }
        if (response.status >= 200 && response.status < 300) return response.json;

        const error = errorOf(response.status, response.json);
        const wait = retryWait(error);
        if (wait == null || attempt >= MAX_RETRIES)
            fail(`POST /speech — HTTP ${response.status}: ${error.message}${hint(error)}`);
        console.log(`POST /speech — HTTP ${response.status}, retry ${attempt}/${MAX_RETRIES - 1} in ${Math.round(wait / 1000)}s: ${error.message}`);
        await sleep(wait);
    }
};

// A 202 answer is a job still running: read GET /jobs/{jobid} until it is done.
const waitFor = async (job, startTime) => {
    while (job.status == 'processing') {
        await sleep(SLEEP_POLL);
        let response;
        try {
            response = await request('GET', `jobs/${enc(job.jobid)}`);
        } catch {
            continue; // a passing network hiccup: reading the job is free, read it again
        }
        if (response.status == 429 || response.status >= 500) continue;
        if (response.status != 200)
            fail(`GET /jobs — HTTP ${response.status}: ${errorOf(response.status, response.json).message}`);
        job = response.json;
        console.log(`   ${job.status} (${elapsedSec(startTime)}s)`);
    }
    return job;
};

// GET /media/{mediaId} streams the WAV. It is saved under its final name only once it has fully arrived.
const download = async (mediaId, file) => {
    const temp = `${file}.part`;
    const response = await fetch(`${API}/media/${enc(mediaId)}`, { headers: { 'Authorization': `Bearer ${apiToken}` } });
    if (!response.ok)
        fail(`GET /media — HTTP ${response.status}: ${errorOf(response.status, await response.json().catch(() => ({}))).message}`);
    await fs.writeFile(temp, Readable.fromWeb(response.body));
    await fs.rename(temp, file);
    console.log(`   saved ${file}`);
};

const main = async () => {
    const [token, email, scriptFile = DEFAULT_SCRIPT_FILE, voice = DEFAULT_VOICE] = process.argv.slice(2);
    apiToken = token;

    if (!apiToken || !email) {
        console.error('Usage: node speech.mjs <API_TOKEN> <EMAIL> [SCRIPT_FILE] [VOICE]');
        process.exit(1);
    }

    console.info('Script v1.0');
    console.info('Node version is: ' + process.version);

    const script = (await fs.readFile(scriptFile, 'utf8')).trim();
    if (!script || script.length > MAX_SCRIPT)
        fail(`${scriptFile} has ${script.length} characters. A script is 1 to ${MAX_SCRIPT} characters.`);

    await fs.mkdir(OUTPUT_DIR, { recursive: true });
    const name = path.basename(scriptFile, path.extname(scriptFile));
    const start = Date.now();
    console.log(`\nSpeech — ${script.length} characters from ${scriptFile}, voice ${voice}`);

    const job = await waitFor(await submit({ script, voice, email }), start);
    await fs.writeFile(path.join(OUTPUT_DIR, `${name}.json`), JSON.stringify(job, null, 2) + '\n');
    if (job.status != 'completed') {
        const error = errorOf(0, job);
        fail(`Speech — job failed (${error.code}): ${error.message}${hint(error)}`);
    }

    const { result } = job;
    console.log(`   completed in ${elapsedSec(start)}s: ${result.duration}s of speech` +
        (result.quota?.speech ? `, ${result.quota.speech.left} Gemini uses left` : ''));
    await download(result.mediaId, path.join(OUTPUT_DIR, `${name}.wav`));
};

main().catch((error) => {
    console.error('Error during execution:', error.stack || error);
    process.exitCode = 1;
});
