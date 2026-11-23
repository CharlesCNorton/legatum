#!/bin/bash
# Encode a complete pilot. Defaults: 168 frames, 1920x1080, 24 fps.
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <frames dir> <out basename (without extension)>" >&2
  exit 2
fi
frames=$1
base=$2
count=${FRAMES:-168}
expected_size=${SIZE:-1920x1080}
[[ "$count" =~ ^[1-9][0-9]*$ && "$expected_size" =~ ^[1-9][0-9]*x[1-9][0-9]*$ ]] || {
  echo 'FRAMES must be a positive integer; SIZE must be WIDTHxHEIGHT.' >&2; exit 2;
}
width=${expected_size%x*}
height=${expected_size#*x}
[[ $((width % 2)) -eq 0 && $((height % 2)) -eq 0 ]] || {
  echo 'SIZE dimensions must be even for yuv420p.' >&2; exit 2;
}
for tool in ffmpeg ffprobe; do
  command -v "$tool" >/dev/null || { echo "Missing $tool" >&2; exit 1; }
done
for ((frame=1; frame<=count; frame++)); do
  printf -v file '%s/frame_%04d.png' "$frames" "$frame"
  [[ -f "$file" ]] || { echo "Missing frame: $file" >&2; exit 1; }
done
size=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$frames/frame_0001.png")
[[ "$size" = "$expected_size" ]] || { echo "Expected $expected_size frames, found $size" >&2; exit 1; }
mkdir -p "$(dirname "$base")"
# Six encoder workers, single-thread decode/filter; run codecs serially.
for crf in 23 26 29 32 35; do
  nice -n 15 ffmpeg -hide_banner -loglevel warning -y -threads 1 -filter_threads 1 \
    -framerate 24 -start_number 1 -i "$frames/frame_%04d.png" -frames:v "$count" -an \
    -vf 'scale=out_color_matrix=bt709:out_range=tv' \
    -c:v libx264 -threads 6 -preset slow -crf "$crf" -pix_fmt yuv420p \
    -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart "$base.mp4"
  bytes=$(wc -c < "$base.mp4")
  echo "H.264 CRF $crf: $bytes bytes"
  [[ "$bytes" -le 2000000 ]] && break
done
[[ "$bytes" -le 2000000 ]] || echo 'H.264 exceeds 2 MB; inspect quality before increasing CRF further.' >&2
for crf in 33 36 39 42 45; do
  nice -n 15 ffmpeg -hide_banner -loglevel warning -y -threads 1 -filter_threads 1 \
    -framerate 24 -start_number 1 -i "$frames/frame_%04d.png" -frames:v "$count" -an \
    -vf 'scale=out_color_matrix=bt709:out_range=tv' \
    -c:v libvpx-vp9 -threads 6 -row-mt 1 -tile-columns 1 -cpu-used 3 -b:v 0 -crf "$crf" \
    -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "$base.webm"
  bytes=$(wc -c < "$base.webm")
  echo "VP9 CRF $crf: $bytes bytes"
  [[ "$bytes" -le 2000000 ]] && break
done
[[ "$bytes" -le 2000000 ]] || echo 'VP9 exceeds 2 MB; inspect quality before increasing CRF further.' >&2
# Verify delivered codecs, frame count, dimensions and timing; refuse false success.
for file in "$base.mp4" "$base.webm"; do
  details=$(ffprobe -v error -count_frames -select_streams v:0 \
    -show_entries stream=codec_name,width,height,pix_fmt,r_frame_rate,nb_read_frames -of csv=p=0 "$file")
  echo "$file: $details"
  case "$details" in
    "h264,$width,$height,yuv420p,24/1,$count"|"vp9,$width,$height,yuv420p,24/1,$count") ;;
    *) echo 'Unexpected output stream; inspect with ffprobe.' >&2; exit 1 ;;
  esac
done
