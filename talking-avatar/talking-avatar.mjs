/*

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

You need Node.js v21 or newer installed to run this script. Download and install Node.js from:

- Windows, macOS, Linux: https://nodejs.org/

After installation, verify by running the following command in a terminal:

   node -v

Running the Script:
===================

Usage: node talking-avatar.mjs <API_TOKEN> <EMAIL> <PHOTO> [PROMPTS_FILE] [--cleanup]

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

node talking-avatar.mjs user:1234-abcdefhijklmnopqrstuv my@email.com photo.jpg
node talking-avatar.mjs user:1234-abcdefhijklmnopqrstuv my@email.com --cleanup

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
const DEFAULT_PROMPTS_FILE = path.join(path.dirname(fileURLToPath(import.meta.url)), 'prompts.json');
const OUTPUT_DIR = 'output';
const STATE_FILE = path.join(OUTPUT_DIR, 'talking_avatar_state.json');
const SLEEP_POLL = 10 * 1000; // in milliseconds, how often GET /jobs/{jobid} is read
const SLEEP_RETRY = 30 * 1000; // in milliseconds, before retrying 429 (busy) or 503
const SLEEP_SIGNED_OUT = 60 * 1000; // in milliseconds, before retrying 596 (account being re-checked)
const MAX_RATE_LIMIT_WAIT = 5 * 60 * 1000; // in milliseconds, a 429 with a later retryAt is a used-up allowance
const MAX_RETRIES = 10;
const PHOTO_TYPES = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp' };

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const elapsedSec = (start) => Math.round((Date.now() - start) / 1000);

// Ids contain ':' and '@', so they are URL-encoded whenever they go into a URL path.
const enc = encodeURIComponent;

const fail = (message) => {
    console.error(`STOP: ${message}`);
    process.exit(1);
};

// --- saved progress -----------------------------------------------------------
// avatar: { avatarId, previewMediaId }   job: jobid of a submitted video not yet finished
// video: { mediaId, duration, speechDuration }
let state = { email: null, avatar: null, job: null, video: null };

const loadState = async () => {
    try {
        state = { ...state, ...JSON.parse(await fs.readFile(STATE_FILE, 'utf8')) };
    } catch {
        // no state file yet: a fresh run
    }
};

const saveState = () => fs.writeFile(STATE_FILE, JSON.stringify(state, null, 2) + '\n');

// --- HTTP ---------------------------------------------------------------------
let apiToken;

// Returns { status, json }. Throws only when no answer arrived at all (network error).
// A JSON body is sent as JSON, a Buffer as the raw request body with its contentType (POST /assets).
const request = async (method, url, body, contentType) => {
    const raw = Buffer.isBuffer(body);
    const response = await fetch(`${API}/${url}`, {
        method,
        headers: {
            'Accept': 'application/json',
            'Authorization': `Bearer ${apiToken}`,
            ...(body ? { 'Content-Type': raw ? contentType : 'application/json' } : {})
        },
        body: body ? (raw ? body : JSON.stringify(body)) : undefined
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
const retryWait = ({ code, message, retryAt }, avatar = false) => {
    if (code == 429) {
        if (retryAt) {
            // Google limiting the account for a minute: retryAt is close. A used-up allowance: retryAt is the monthly reset.
            const ms = Date.parse(retryAt) - Date.now();
            return ms <= MAX_RATE_LIMIT_WAIT ? Math.max(ms, 0) + 5000 : null;
        }
        if (/allowance|resets at/i.test(message)) return null;
        return SLEEP_RETRY; // every maxJobs slot busy, or a short limit
    }
    if (code == 503) return SLEEP_RETRY; // Google server error, or the job could not be queued
    if (code == 596) return /Re-add it at/.test(message) ? null : SLEEP_SIGNED_OUT; // the account is being re-checked
    if (code == 502 && avatar) return SLEEP_RETRY; // "Google did not keep the avatar in the Vids document, please retry"
    return null;
};

// What to do about the refusals people meet most with talking avatars.
const hint = ({ code, message }) => {
    if (code == 400 && /seconds when spoken/i.test(message))
        return '\n   Shorten the script in prompts.json (or drop a [slow pace] tag) and run again. No AI avatar video was used,' +
            '\n   the Gemini use for its speech was. POST /speech in the same voice (speech.mjs) tells you how long it runs.';
    if (code == 422 && /still counts/i.test(message))
        return '\n   Google refused the finished video and still counts it against the AI avatar videos. Restyle the avatar' +
            '\n   (change "refine" and delete "avatar" from the state file) or start from another photo.';
    if (code == 422)
        return '\n   Google refused the photo, the avatar or the script. Nothing was charged. Try another photo or other words.';
    if (/expired|HTTP 404 for this image/i.test(message))
        return '\n   The upload expired. Run the script again: it uploads the photo again before it makes the avatar.';
    return '';
};

// POST with retries on the answers the docs say to retry. If no answer arrives at all, it is unclear whether the API
// accepted the request, so it is never sent again automatically: a paid step must not run twice.
const post = async (url, body, what, { avatar = false, contentType } = {}) => {
    for (let attempt = 1; ; attempt++) {
        let response;
        try {
            response = await request('POST', url, body, contentType);
        } catch (error) {
            fail(`${what} — no answer from the API (${error.message}). It may have been accepted, so it is not sent again.\n` +
                `   Check ${avatar ? 'GET /avatars' : 'GET /jobs'} before running the script again.`);
        }
        if (response.status >= 200 && response.status < 300) return response.json;

        const error = errorOf(response.status, response.json);
        const wait = retryWait(error, avatar);
        if (wait == null || attempt >= MAX_RETRIES)
            fail(`${what} — HTTP ${response.status}: ${error.message}${hint(error)}`);
        console.log(`${what} — HTTP ${response.status}, retry ${attempt}/${MAX_RETRIES - 1} in ${Math.round(wait / 1000)}s: ${error.message}`);
        await sleep(wait);
    }
};

const fileExists = (file) => fs.access(file).then(() => true, () => false);

// GET /media/{mediaId} streams the file itself (video/mp4 or image/jpeg). It is saved under its final name only once
// it has fully arrived, so a broken download leaves no partial file behind.
const download = async (mediaId, filename) => {
    const file = path.join(OUTPUT_DIR, filename);
    if (await fileExists(file)) return;
    for (let attempt = 1; attempt <= 3; attempt++) {
        const temp = `${file}.part`;
        try {
            const response = await fetch(`${API}/media/${enc(mediaId)}`, { headers: { 'Authorization': `Bearer ${apiToken}` } });
            if (response.ok) {
                await fs.writeFile(temp, Readable.fromWeb(response.body));
                await fs.rename(temp, file);
                console.log(`   saved ${file}`);
                return;
            }
            const message = errorOf(response.status, await response.json().catch(() => ({}))).message;
            if (response.status != 502) {
                console.error(`Unable to download ${file} (HTTP ${response.status}): ${message}`);
                return;
            }
        } catch (error) {
            await fs.rm(temp, { force: true });
            console.error(`Download of ${file} broke off: ${error.message}`);
        }
        await sleep(SLEEP_POLL);
    }
    console.error(`Unable to download ${file}. Run the script again to retry the download.`);
};

// --- checks before anything is spent --------------------------------------------
const validate = (config, photo) => {
    const warnings = [];
    const { avatar, script } = config;
    if (!avatar) fail('avatar is required in the prompts file');
    if (!avatar.name || avatar.name.length > 40) warnings.push('avatar: name is required, 1 to 40 characters');
    if (!avatar.voice) warnings.push('avatar: voice is required (a name or voice id from GET /voices)');
    if (avatar.refine && avatar.refine.length > 1000) warnings.push('avatar: refine is up to 1000 characters');
    if (!script || script.length > 400) warnings.push(`script is required, 1 to 400 characters (it has ${script?.length ?? 0})`);
    if (!state.avatar && !photo) warnings.push('PHOTO is required to make the avatar');
    if (photo && !PHOTO_TYPES[path.extname(photo).toLowerCase()]) warnings.push('PHOTO must be a .jpg, .jpeg, .png or .webp file');
    if (warnings.length) {
        warnings.forEach((warning) => console.warn(`WARNING: ${warning}`));
        fail('Execution stopped due to warnings in the prompts file or the arguments.');
    }
};

// GET /accounts/{email} reads the account's allowance live from Google. A talking avatar video needs 1 AI avatar video
// (avatarVideo) and 1 Gemini use (speech).
const checkAccount = async (email) => {
    let response;
    try {
        response = await request('GET', `accounts/${enc(email)}`);
    } catch (error) {
        fail(`GET /accounts — no answer from the API (${error.message})`);
    }
    if (response.status != 200)
        fail(`Account ${email} — HTTP ${response.status}: ${errorOf(response.status, response.json).message}. See https://useapi.net/docs/start-here/setup-google-vids`);
    const { health, quota, limits, session } = response.json;
    if (health && health != 'OK')
        fail(`Account ${email} health is '${health}'. See https://useapi.net/docs/start-here/setup-google-vids`);
    if (limits?.avatarVideo === 0)
        fail(`Account ${email} has no AI avatar videos on its Google plan (monthly limit 0).`);
    console.log(`Account ${email}: ${quota?.avatarVideo?.left ?? '?'} AI avatar videos, ${quota?.speech?.left ?? '?'} Gemini uses` +
        ` and ${quota?.image?.left ?? '?'} images left this month`);
    if (!quota) console.warn(`WARNING: Could not read the allowance (session: ${session}), continuing`);
    if (!state.video && !state.job) {
        if (quota?.avatarVideo && quota.avatarVideo.left < 1)
            fail(`No AI avatar videos left. They reset at ${quota.avatarVideo.resetAt}`);
        if (quota?.speech && quota.speech.left < 1)
            fail(`No Gemini uses (speech) left. They reset at ${quota.speech.resetAt}`);
    }
};

// --- the steps ----------------------------------------------------------------------
const execute = async (email, photo, promptsFile) => {
    const config = JSON.parse(await fs.readFile(promptsFile, 'utf8'));
    validate(config, photo);
    await checkAccount(email);
    const { avatar, script } = config;
    const slug = avatar.name.toLowerCase().replace(/[^a-z0-9]+/g, '-');

    // Steps 1 and 2 — upload the photo, then make the avatar from it. An upload is free and temporary, so the photo is
    // uploaded again whenever the avatar still has to be made. POST /avatars answers when the avatar is saved and is
    // not a job. Google reframes the photo into a 16:9 avatar picture, then applies refine.
    if (!state.avatar) {
        console.log(`\nUpload ${photo}`);
        const bytes = await fs.readFile(photo);
        const asset = await post(`assets?email=${enc(email)}`, bytes, 'POST /assets', { contentType: PHOTO_TYPES[path.extname(photo).toLowerCase()] });
        console.log(`   ${asset.assetId} (${asset.bytes} bytes)`);

        console.log(`\nAvatar ${avatar.name}`);
        const startTime = Date.now();
        const json = await post('avatars', { ...avatar, image: asset.assetId, email }, `POST /avatars (${avatar.name})`, { avatar: true });
        state.avatar = { avatarId: json.avatarId, previewMediaId: json.previewMediaId };
        await saveState();
        await fs.writeFile(path.join(OUTPUT_DIR, `${slug}-avatar.json`), JSON.stringify(json, null, 2) + '\n');
        console.log(`   saved in ${elapsedSec(startTime)}s, voice ${json.voice} (${json.voiceId}, ${json.voiceStyle})`);
    }
    if (state.avatar.previewMediaId) await download(state.avatar.previewMediaId, `${slug}-avatar.jpg`);

    // Step 3 — the talking video. Submitted with async: true (or a job a stopped run left behind is picked up), then
    // GET /jobs/{jobid} is polled until it is done. A failed job is sent again only after a short rate limit (429 with
    // retryAt about a minute away), which made nothing. Any other failure stops the script: Google counts a video it
    // refused while making it (422), so it is never sent again automatically.
    const startTime = Date.now();
    for (let attempt = 1; !state.video; attempt++) {
        if (state.job)
            console.log(`\nVideo — picking up job ${state.job}`);
        else {
            console.log(`\nVideo — ${script.length} characters`);
            const job = await post('videos/avatar', { avatar: state.avatar.avatarId, script, async: true }, 'POST /videos/avatar');
            state.job = job.jobid;
            await saveState();
            console.log(`   job ${state.job}`);
        }

        let job;
        while (true) {
            await sleep(SLEEP_POLL);
            let response;
            try {
                response = await request('GET', `jobs/${enc(state.job)}`);
            } catch {
                continue; // a passing network hiccup: reading the job is free, read it again
            }
            if (response.status == 429 || response.status >= 500) continue;
            if (response.status != 200)
                fail(`GET /jobs — HTTP ${response.status}: ${errorOf(response.status, response.json).message}`);
            job = response.json;
            if (job.status != 'processing') break;
            console.log(`   processing (${elapsedSec(startTime)}s)`);
        }

        state.job = null;
        await saveState();
        await fs.writeFile(path.join(OUTPUT_DIR, `${slug}-talking.json`), JSON.stringify(job, null, 2) + '\n');

        if (job.status == 'completed') {
            const { result } = job;
            state.video = { mediaId: result.mediaId, duration: result.duration, speechDuration: result.speechDuration };
            await saveState();
            console.log(`   completed in ${elapsedSec(startTime)}s: ${result.duration}s (speech ${result.speechDuration}s), ${result.width}×${result.height}` +
                (result.quota?.avatarVideo ? `, ${result.quota.avatarVideo.left} AI avatar videos left` : ''));
            break;
        }

        const error = errorOf(0, job);
        const wait = error.code == 429 && error.retryAt ? retryWait(error) : null;
        if (wait == null || attempt >= MAX_RETRIES)
            fail(`Video — job failed (${error.code}): ${error.message}${hint(error)}` +
                ([502, 503, 504].includes(error.code) ? `\n   Google may have made and counted it, so the script does not send it again. Run the script again to retry.` : ''));
        console.log(`Video — job failed (${error.code}), submitting again in ${Math.round(wait / 1000)}s: ${error.message}`);
        await sleep(wait);
    }
    await download(state.video.mediaId, `${slug}-talking.mp4`);

    console.log(`\nDone. Files are in ${path.resolve(OUTPUT_DIR)}`);
    console.log(`The avatar is kept in the account's Vids document, reusable in POST /videos/avatar and as avatar_1 in POST /videos:`);
    console.log(`   ${avatar.name}: ${state.avatar.avatarId}`);
    console.log(`   To delete it, run the script again with --cleanup.`);
};

// DELETE /avatars/{avatarId} for the avatar this script created (as listed in the state file).
const cleanup = async () => {
    if (!state.avatar) {
        console.log(`Nothing to delete: ${STATE_FILE} lists no avatar.`);
        return;
    }
    let response;
    try {
        response = await request('DELETE', `avatars/${enc(state.avatar.avatarId)}`);
    } catch (error) {
        fail(`DELETE /avatars — no answer from the API (${error.message})`);
    }
    if (response.status != 204 && response.status != 404)
        fail(`DELETE /avatars — HTTP ${response.status}: ${errorOf(response.status, response.json).message}. Run --cleanup again.`);
    console.log(`Avatar ${response.status == 204 ? 'deleted' : 'already gone'}`);
    state.avatar = null;
    await saveState();
};

const main = async () => {
    const args = process.argv.slice(2);
    const isCleanup = args.includes('--cleanup');
    const [token, email, photo, promptsFile = DEFAULT_PROMPTS_FILE] = args.filter((arg) => arg != '--cleanup');
    apiToken = token;

    if (!apiToken || !email) {
        console.error('Usage: node talking-avatar.mjs <API_TOKEN> <EMAIL> <PHOTO> [PROMPTS_FILE] [--cleanup]');
        process.exit(1);
    }

    console.info('Script v1.0');
    console.info('Node version is: ' + process.version);

    await fs.mkdir(OUTPUT_DIR, { recursive: true });
    await loadState();
    if (state.email && state.email != email)
        fail(`${STATE_FILE} belongs to ${state.email}. Use that email, or move the output folder away to start fresh.`);
    state.email = email;

    const start = Date.now();
    try {
        console.info('START EXECUTION', new Date(start));
        if (isCleanup) await cleanup();
        else await execute(email, photo, promptsFile);
    } catch (error) {
        console.error('Error during execution:', error.stack || error);
        process.exitCode = 1;
    } finally {
        console.info('COMPLETED', new Date());
        console.info('EXECUTION ELAPSED', `${elapsedSec(start)} seconds`);
    }
};

main();
