#!/usr/bin/env bash
# Everything in one command: generate a Vids clip, wait for it, download it. Prints the saved .mp4 path.
# Usage: video.sh "<prompt>" [key=value ...]     (options as in generate.sh)
# Example: video.sh "@avatar_1 holds up the mug, smiles and says: \"Best coffee all year.\" Handheld phone camera." \
#            avatar_1=<avatarId> aspectRatio=portrait duration=6
# OUT_DIR sets the folder (default: the current one); the final job record is saved next to the video as .json.
# If the run is interrupted after "job ..." was logged, do NOT run it again (that pays twice). Resume with:
#   wait-job.sh <jobid> > job.json && download.sh job.json
DIR="$(dirname "$0")"
source "$DIR/_common.sh"
PROMPT="${1:?Usage: video.sh \"<prompt>\" [key=value ...]}"
shift

JOBID=$("$DIR/generate.sh" "$PROMPT" ${1+"$@"})
JOB=$("$DIR/wait-job.sh" "$JOBID") || { echo "Not resubmitted. Job id: $JOBID" >&2; exit 1; }
FILE=$("$DIR/download.sh" - "${OUT_DIR:-.}" <<< "$JOB") || { echo "Resume the download with: download.sh <job.json> (job id $JOBID)" >&2; exit 1; }
echo "$JOB" > "${FILE%.*}.json"
echo "$FILE"
