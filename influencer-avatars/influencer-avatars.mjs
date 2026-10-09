/*

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

You need Node.js v21 or newer installed to run this script. Download and install Node.js from:

- Windows, macOS, Linux: https://nodejs.org/

After installation, verify by running the following command in a terminal:

   node -v

Running the Script:
===================

Usage: node influencer-avatars.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE] [--cleanup]

Replace API_TOKEN with your actual useapi.net API token, see https://useapi.net/docs/start-here/setup-useapi
Replace EMAIL with the Google account connected to the Google Vids API, see https://useapi.net/docs/start-here/setup-google-vids
If optional PROMPTS_FILE not provided, prompts.json next to this script will be used.

Results are saved to the output folder in the current directory. To redo one step, delete its entry from
output/influencer_state.json and run again.

The avatars stay in your account's Vids document, ready for more videos, until you delete them. Run the script
again with --cleanup to delete the avatars this script created (only those, listed in output/influencer_state.json).

Example:
--------

node influencer-avatars.mjs user:1234-abcdefhijklmnopqrstuv my@email.com
node influencer-avatars.mjs user:1234-abcdefhijklmnopqrstuv my@email.com --cleanup

Changelog:
==========

- October 8, 2026: Initial release.

*/

import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Readable } from 'node:stream';

// Constants
const API = 'https://api.useapi.net/v1/google-vids';
const DEFAULT_PROMPTS_FILE = path.join(path.dirname(fileURLToPath(import.meta.url)), 'prompts.json');
const OUTPUT_DIR = 'output';
const STATE_FILE = path.join(OUTPUT_DIR, 'influencer_state.json');
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
    console.error(`🛑 ${message}`);
    process.exit(1);
};

// --- saved progress -----------------------------------------------------------
// images: name → { mediaId }   avatars: name → { avatarId, previewMediaId? }
// clips: name → { mediaId, duration, resolution }   jobs: name → jobid of a submitted job not yet finished
let state = { email: null, images: {}, avatars: {}, clips: {}, jobs: {} };

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
const retryWait = ({ code, message, retryAt }, avatar = false) => {
    if (code == 429) {
        if (retryAt) {
            // Google limiting the account for a minute: retryAt is close. A used-up allowance: retryAt is the monthly reset.
            const ms = Date.parse(retryAt) - Date.now();
            return ms <= MAX_RATE_LIMIT_WAIT ? Math.max(ms, 0) + 5000 : null;
        }
        if (/allowance|resets at/i.test(message)) return null;
        return avatar ? SLEEP_SIGNED_OUT : SLEEP_RETRY; // every maxJobs slot busy, or a short limit
    }
    if (code == 503) return SLEEP_RETRY; // Google server error, or the job could not be queued
    if (code == 596) return /Re-add it at/.test(message) ? null : SLEEP_SIGNED_OUT; // the account is being re-checked
    if (code == 502 && avatar) return SLEEP_RETRY; // "Google did not keep the avatar in the Vids document, please retry"
    return null;
};

const hint = (message) => /expired/i.test(message)
    ? `\n   A generated image lasts a few hours only. Delete its entry under "images" in ${STATE_FILE} and run again to make it again.`
    : '';

// POST with retries on the answers the docs say to retry. If no answer arrives at all, it is unclear whether the API
// accepted the request, so it is never sent again automatically: a paid step must not run twice.
const post = async (url, body, what, avatar = false) => {
    for (let attempt = 1; ; attempt++) {
        let response;
        try {
            response = await request('POST', url, body);
        } catch (error) {
            fail(`${what} — no answer from the API (${error.message}). It may have been accepted, so it is not sent again.\n` +
                `   Check ${avatar ? 'GET /avatars' : 'GET /jobs'} before running the script again.`);
        }
        if (response.status >= 200 && response.status < 300) return response.json;

        const error = errorOf(response.status, response.json);
        const wait = retryWait(error, avatar);
        if (wait == null || attempt >= MAX_RETRIES)
            fail(`${what} — HTTP ${response.status}: ${error.message}${hint(error.message)}`);
        console.log(`🔄️ ${what} — HTTP ${response.status}, retry ${attempt}/${MAX_RETRIES - 1} in ${Math.round(wait / 1000)}s: ${error.message}`);
        await sleep(wait);
    }
};

// Submit a job with async: true (or pick up the job a stopped run left behind), then poll GET /jobs/{jobid} until it
// completes. A failed job is sent again only when Google refused it with a short rate limit (429 with retryAt about a
// minute away), which makes nothing and costs nothing. Any other failure stops the script: a job can fail after Google
// made and charged the clip (we saw 503 "Google answered without a video" use the clip's seconds), so it is not sent
// again automatically. Running the script again retries the step.
const runJob = async (name, url, body) => {
    const startTime = Date.now();
    for (let attempt = 1; ; attempt++) {
        let jobid = state.jobs[name];
        if (jobid)
            console.log(`   ♻️  ${name} — picking up job ${jobid}`);
        else {
            const job = await post(url, { ...body, async: true }, `POST /${url} (${name})`);
            jobid = job.jobid;
            state.jobs[name] = jobid;
            await saveState();
            console.log(`   ⏳ ${name} — job ${jobid}`);
        }

        let job;
        while (true) {
            await sleep(SLEEP_POLL);
            let response;
            try {
                response = await request('GET', `jobs/${enc(jobid)}`);
            } catch {
                continue; // a passing network hiccup: reading the job is free, read it again
            }
            if (response.status == 429 || response.status >= 500) continue;
            if (response.status != 200)
                fail(`GET /jobs (${name}) — HTTP ${response.status}: ${errorOf(response.status, response.json).message}`);
            job = response.json;
            if (job.status != 'processing') break;
            console.log(`   ⌛ ${name} — processing (${elapsedSec(startTime)}s)`);
        }

        delete state.jobs[name];
        await saveState();
        await fs.writeFile(path.join(OUTPUT_DIR, `${name}.json`), JSON.stringify(job, null, 2) + '\n');

        if (job.status == 'completed') {
            const { result } = job;
            const left = result.quota?.video ? `${result.quota.video.left}s of video left` : result.quota?.image ? `${result.quota.image.left} images left` : '';
            console.log(`✅ ${name} — completed in ${elapsedSec(startTime)}s (Google ${Math.round(result.elapsedMs / 1000)}s)` +
                (result.duration ? `, ${result.duration}s at ${result.resolution} ${result.width}×${result.height}` : `, ${result.width}×${result.height}`) +
                (left ? `, ${left}` : ''));
            return job;
        }

        const error = errorOf(0, job);
        const wait = error.code == 429 && error.retryAt ? retryWait(error) : null;
        if (wait == null || attempt >= MAX_RETRIES)
            fail(`${name} — job failed (${error.code}): ${error.message}${hint(error.message)}` +
                ([502, 503, 504].includes(error.code) ? `\n   Google may have made and charged it, so the script does not send it again. Run the script again to retry this step.` : ''));
        console.log(`🔄️ ${name} — job failed (${error.code}), submitting again in ${Math.round(wait / 1000)}s: ${error.message}`);
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
                console.log(`   💾 ${file}`);
                return;
            }
            const message = errorOf(response.status, await response.json().catch(() => ({}))).message;
            if (response.status != 502) {
                console.error(`⛔ Unable to download ${file} (HTTP ${response.status}): ${message}`);
                return;
            }
        } catch (error) {
            await fs.rm(temp, { force: true });
            console.error(`⛔ Download of ${file} broke off: ${error.message}`);
        }
        await sleep(SLEEP_POLL);
    }
    console.error(`⛔ Unable to download ${file}. Run the script again to retry the download.`);
};

// --- prompts.json -------------------------------------------------------------
const AVATAR_KEYS = ['avatar_1', 'avatar_2', 'avatar_3'];
const IMAGE_KEYS = ['referenceImage_1', 'referenceImage_2', 'referenceImage_3'];

// Check prompts.json before anything is spent. Returns { images, seconds } the steps not yet done will use.
const validate = (config) => {
    const warnings = [];
    const images = config.images ?? [];
    const avatars = config.avatars ?? [];
    const extendsList = config.extends ?? [];
    const { launch, upscale } = config;
    const names = new Set();
    const named = (what, name) => {
        if (!name) warnings.push(`${what} has no name`);
        else if (names.has(name)) warnings.push(`the name "${name}" is used twice`);
        names.add(name);
    };
    const checkDuration = (what, d) => {
        if (d != null && !(Number.isInteger(d) && d >= 3 && d <= 10)) warnings.push(`${what}: duration must be 3 to 10 seconds`);
    };

    for (const image of images) {
        named('an image', image.name);
        if (!image.prompt) warnings.push(`image ${image.name}: prompt is required`);
    }
    for (const avatar of avatars) {
        if (!avatar.name) warnings.push('an avatar has no name');
        if (!avatar.voice) warnings.push(`avatar ${avatar.name}: voice is required`);
        if (!!avatar.image == !!avatar.appearance) warnings.push(`avatar ${avatar.name}: give either image or appearance`);
        if (avatar.image && !images.some((i) => i.name == avatar.image)) warnings.push(`avatar ${avatar.name}: no image named "${avatar.image}"`);
    }
    if (!launch) fail('launch is required in the prompts file');
    named('launch', launch.name);
    if (!launch.prompt) warnings.push('launch: prompt is required');
    checkDuration('launch', launch.duration);
    const allowed = ['name', 'prompt', 'duration', 'resolution', 'aspectRatio', ...AVATAR_KEYS, ...IMAGE_KEYS];
    const unknown = Object.keys(launch).filter((key) => !allowed.includes(key));
    if (unknown.length) warnings.push(`launch: parameters not supported by this script: ${unknown.join(', ')}`);
    for (const key of AVATAR_KEYS)
        if (launch[key] && !avatars.some((a) => a.name == launch[key])) warnings.push(`launch: ${key} names no avatar "${launch[key]}"`);
    for (const key of IMAGE_KEYS)
        if (launch[key] && !images.some((i) => i.name == launch[key])) warnings.push(`launch: ${key} names no image "${launch[key]}"`);
    if ([...AVATAR_KEYS, ...IMAGE_KEYS].filter((key) => launch[key]).length > 3) warnings.push('launch: up to 3 avatars and reference images in all');

    // Length and resolution of every clip, to check the upscale and count the seconds.
    const clips = { [launch.name]: { duration: launch.duration ?? 8, resolution: launch.resolution ?? '720p' } };
    let previous = launch.name;
    for (const extend of extendsList) {
        named('an extend', extend.name);
        if (!extend.prompt) warnings.push(`extend ${extend.name}: prompt is required`);
        checkDuration(`extend ${extend.name}`, extend.duration);
        const source = clips[previous];
        clips[extend.name] = { duration: source.duration + (extend.duration ?? 8), resolution: extend.resolution ?? source.resolution };
        previous = extend.name;
    }
    if (upscale) {
        named('upscale', upscale.name);
        const clip = clips[upscale.clip];
        if (!clip) warnings.push(`upscale: no clip named "${upscale.clip}"`);
        else if (clip.duration > 20) warnings.push(`upscale: ${upscale.clip} is ${clip.duration}s, upscale takes clips of up to 20 seconds`);
        else if (clip.resolution != '720p') warnings.push(`upscale: ${upscale.clip} is not 720p`);
    }

    if (warnings.length) {
        warnings.forEach((warning) => console.warn(`⚠️  ${warning}`));
        fail('Execution stopped due to warnings in the prompts file.');
    }

    // What the steps not yet done will use: an image per image and per drawn avatar, a clip's seconds, an extend's
    // added seconds, and the whole clip's seconds again for the upscale.
    const needImages = images.filter((i) => !state.images[i.name]).length +
        avatars.filter((a) => a.appearance && !state.avatars[a.name]).length;
    let needSeconds = 0;
    if (!state.clips[launch.name]) needSeconds += clips[launch.name].duration;
    for (const extend of extendsList) if (!state.clips[extend.name]) needSeconds += extend.duration ?? 8;
    if (upscale && !state.clips[upscale.name]) needSeconds += clips[upscale.clip].duration;
    return { images: needImages, seconds: needSeconds };
};

// GET /accounts/{email} reads the account's allowance live from Google.
const checkAccount = async (email, need) => {
    let response;
    try {
        response = await request('GET', `accounts/${enc(email)}`);
    } catch (error) {
        fail(`GET /accounts — no answer from the API (${error.message})`);
    }
    if (response.status != 200)
        fail(`Account ${email} — HTTP ${response.status}: ${errorOf(response.status, response.json).message}. See https://useapi.net/docs/start-here/setup-google-vids`);
    const { health, quota, session } = response.json;
    if (health && health != 'OK')
        fail(`Account ${email} health is '${health}'. See https://useapi.net/docs/start-here/setup-google-vids`);
    console.log(`👤 ${email}: ${quota?.video?.left ?? '?'}s of video and ${quota?.image?.left ?? '?'} images left this month` +
        `, this run needs ${need.seconds}s and ${need.images} images`);
    if (quota?.video == null || quota?.image == null)
        console.warn(`⚠️  Could not read the whole allowance (session: ${session}), continuing`);
    if (quota?.video && quota.video.left < need.seconds)
        fail(`Not enough video seconds left (${quota.video.left} < ${need.seconds}). It resets at ${quota.video.resetAt}`);
    if (quota?.image && quota.image.left < need.images)
        fail(`Not enough images left (${quota.image.left} < ${need.images}). It resets at ${quota.image.resetAt}`);
};

// --- the pipeline ---------------------------------------------------------------
const execute = async (email, promptsFile) => {
    const config = JSON.parse(await fs.readFile(promptsFile, 'utf8'));
    const need = validate(config);
    await checkAccount(email, need);

    // Step 1 — images, one JPEG per call, pinned to EMAIL: every input of one video must come from the same account.
    for (const { name, ...image } of config.images ?? []) {
        if (!state.images[name]) {
            console.log(`\n🖼️  Image ${name}`);
            const job = await runJob(name, 'images', { ...image, email });
            state.images[name] = { mediaId: job.result.mediaId };
            await saveState();
        }
        await download(state.images[name].mediaId, `${name}.jpg`);
    }

    // Step 2 — avatars: a picture plus a fixed voice, saved in the account's Vids document. With `image` (an image from
    // step 1) the avatar is saved on that image's account; with `appearance` Google draws the person.
    // POST /avatars answers when the avatar is saved and is not a job.
    for (const { name, image, ...avatar } of config.avatars ?? []) {
        if (!state.avatars[name]) {
            console.log(`\n🧑 Avatar ${name}`);
            const startTime = Date.now();
            const body = image ? { name, ...avatar, image: state.images[image].mediaId } : { name, ...avatar, email };
            const json = await post('avatars', body, `POST /avatars (${name})`, true);
            state.avatars[name] = { avatarId: json.avatarId, ...(json.previewMediaId ? { previewMediaId: json.previewMediaId } : {}) };
            await saveState();
            await fs.writeFile(path.join(OUTPUT_DIR, `${name.toLowerCase()}-avatar.json`), JSON.stringify(json, null, 2) + '\n');
            console.log(`✅ ${name} — saved in ${elapsedSec(startTime)}s, voice ${json.voice} (${json.voiceId}, ${json.voiceStyle})`);
        }
        if (state.avatars[name].previewMediaId)
            await download(state.avatars[name].previewMediaId, `${name.toLowerCase()}-avatar.jpg`);
    }

    // Step 3 — the launch clip. In prompts.json avatar_N names an avatar and referenceImage_N an image from the steps
    // above; the prompt calls them @avatar_N and @referenceImage_N. The image's mediaId goes in directly.
    const { name: launchName, ...launch } = config.launch;
    if (!state.clips[launchName]) {
        console.log(`\n🎬 Clip ${launchName}`);
        const body = { ...launch };
        for (const key of AVATAR_KEYS) if (body[key]) body[key] = state.avatars[body[key]].avatarId;
        for (const key of IMAGE_KEYS) if (body[key]) body[key] = state.images[body[key]].mediaId;
        const { result } = await runJob(launchName, 'videos', body);
        state.clips[launchName] = { mediaId: result.mediaId, duration: result.duration, resolution: result.resolution };
        await saveState();
    }
    await download(state.clips[launchName].mediaId, `${launchName}.mp4`);

    // Step 4 — extends. Each adds `duration` seconds and returns the whole clip with a new mediaId. An extend gets the
    // clip and the prompt only, not the avatars, so the prompts name people by what they wear.
    let previous = launchName;
    for (const { name, ...extend } of config.extends ?? []) {
        if (!state.clips[name]) {
            console.log(`\n➕ Extend ${previous} → ${name}`);
            const { result } = await runJob(name, 'videos/extend', { mediaId: state.clips[previous].mediaId, ...extend });
            state.clips[name] = { mediaId: result.mediaId, duration: result.duration, resolution: result.resolution };
            await saveState();
        }
        await download(state.clips[name].mediaId, `${name}.mp4`);
        previous = name;
    }

    // Step 5 — upscale to 1080p. It takes 720p clips of up to 20 seconds and uses the clip's seconds again.
    if (config.upscale) {
        const { name, clip } = config.upscale;
        if (!state.clips[name]) {
            console.log(`\n⬆️  Upscale ${clip} → ${name}`);
            const { result } = await runJob(name, 'videos/upscale', { mediaId: state.clips[clip].mediaId });
            state.clips[name] = { mediaId: result.mediaId, duration: result.duration, resolution: result.resolution };
            await saveState();
        }
        await download(state.clips[name].mediaId, `${name}.mp4`);
    }

    console.log(`\n🎉 Done. Files are in ${path.resolve(OUTPUT_DIR)}`);
    for (const [name, clip] of Object.entries(state.clips)) console.log(`   ${name}.mp4 — ${clip.duration}s, ${clip.resolution}`);
    console.log(`\n🧑 Avatars kept in the account's Vids document, reusable as avatar_1..avatar_3 in POST /videos:`);
    for (const [name, { avatarId }] of Object.entries(state.avatars)) console.log(`   ${name}: ${avatarId}`);
    console.log(`   To delete them, run the script again with --cleanup.`);
};

// DELETE /avatars/{avatarId} for every avatar this script created (as listed in the state file).
const cleanup = async () => {
    const names = Object.keys(state.avatars);
    if (!names.length) {
        console.log(`Nothing to delete: ${STATE_FILE} lists no avatars.`);
        return;
    }
    for (const name of names) {
        const { avatarId } = state.avatars[name];
        let response;
        try {
            response = await request('DELETE', `avatars/${enc(avatarId)}`);
        } catch (error) {
            console.error(`⛔ ${name} — no answer from the API (${error.message})`);
            continue;
        }
        if (response.status == 204 || response.status == 404) {
            console.log(`🗑️  ${name} — ${response.status == 204 ? 'deleted' : 'already gone'}`);
            delete state.avatars[name];
            await saveState();
        } else
            console.error(`⛔ ${name} — HTTP ${response.status}: ${errorOf(response.status, response.json).message}. Run --cleanup again.`);
    }
};

const main = async () => {
    const args = process.argv.slice(2);
    const isCleanup = args.includes('--cleanup');
    const [token, email, promptsFile = DEFAULT_PROMPTS_FILE] = args.filter((arg) => arg != '--cleanup');
    apiToken = token;

    if (!apiToken || !email) {
        console.error('Usage: node influencer-avatars.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE] [--cleanup]');
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
        else await execute(email, promptsFile);
    } catch (error) {
        console.error('⛔ Error during execution:', error.stack || error);
        process.exitCode = 1;
    } finally {
        console.info('COMPLETED', new Date());
        console.info('EXECUTION ELAPSED', `${elapsedSec(start)} seconds`);
    }
};

main();
