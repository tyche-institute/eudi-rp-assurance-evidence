#!/usr/bin/env bash
set -euo pipefail

kit_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
packet_dir="$(cd "$kit_dir/.." && pwd)"
image_name="tyche/eudi-independent-reproducer:0.2.0-candidate"
run_stamp="$(date -u +%Y%m%dT%H%M%SZ)"
output_dir="${REPRO_OUTPUT_DIR:-$kit_dir/results/return-$run_stamp}"

case "$output_dir" in
  /*) ;;
  *) output_dir="$PWD/$output_dir" ;;
esac

if [[ -e "$output_dir" ]]; then
  echo "Refusing to overwrite existing path: $output_dir" >&2
  exit 2
fi
mkdir -p "$output_dir"

docker build \
  --pull=false \
  --file "$kit_dir/Dockerfile" \
  --tag "$image_name" \
  "$packet_dir"

image_id="$(docker image inspect "$image_name" --format '{{.Id}}')"
printf '%s\n' "$image_id" >"$output_dir/CONTAINER-IMAGE-ID"

docker run --rm \
  --network bridge \
  --volume "$output_dir:/output" \
  --env "REPRO_CONTROL=${REPRO_CONTROL:-tyche-controlled-local-run}" \
  --env "REPRO_INDEPENDENT=${REPRO_INDEPENDENT:-false}" \
  --env "REPRO_CONTROLLER_ID=${REPRO_CONTROLLER_ID:-Tyche Institute local validation}" \
  --env "REPRO_RELATIONSHIP=${REPRO_RELATIONSHIP:-study author controlled the validation run}" \
  "$image_name"

"$kit_dir/verify-return.sh" "$output_dir"
printf 'Return package: %s\n' "$output_dir"
