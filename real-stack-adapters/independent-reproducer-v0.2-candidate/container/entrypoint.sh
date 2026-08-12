#!/usr/bin/env bash
set -euo pipefail

output_dir=/output
work_dir="$(mktemp -d /tmp/tyche-independent-return-XXXXXX)"

cleanup() {
  rm -rf "$work_dir"
}
trap cleanup EXIT

if [[ ! -d "$output_dir" || ! -w "$output_dir" ]]; then
  echo "A writable /output mount is required." >&2
  exit 2
fi
if find "$output_dir" -mindepth 1 -maxdepth 1 ! -name CONTAINER-IMAGE-ID -print -quit | grep -q .; then
  echo "The return directory must be empty except for CONTAINER-IMAGE-ID." >&2
  exit 2
fi

control="${REPRO_CONTROL:-tyche-controlled-local-run}"
independent="${REPRO_INDEPENDENT:-false}"
controller_id="${REPRO_CONTROLLER_ID:-unattributed-local-controller}"
relationship="${REPRO_RELATIONSHIP:-not stated}"

case "$control" in
  tyche-controlled-local-run|independent-implementation-owner-run|independent-third-party-run|automated-public-ci-run|other-disclosed-controller) ;;
  *) echo "Unsupported REPRO_CONTROL: $control" >&2; exit 2 ;;
esac
case "$independent" in
  true|false) ;;
  *) echo "REPRO_INDEPENDENT must be true or false." >&2; exit 2 ;;
esac
case "$control:$independent" in
  independent-implementation-owner-run:true|independent-third-party-run:true) ;;
  independent-implementation-owner-run:false|independent-third-party-run:false)
    echo "Independent controller classes require REPRO_INDEPENDENT=true." >&2
    exit 2
    ;;
  *:true)
    echo "REPRO_INDEPENDENT=true requires an independent controller class." >&2
    exit 2
    ;;
esac
if [[ -z "$controller_id" || -z "$relationship" ]]; then
  echo "Controller and relationship labels must be non-empty." >&2
  exit 2
fi

if [[ -n "${ANDROID_HOME:-}" || -n "${ANDROID_SDK_ROOT:-}" ]] || command -v sdkmanager >/dev/null 2>&1; then
  echo "This no-Android kit refuses an Android SDK environment." >&2
  exit 2
fi

mkdir -p "$output_dir/raw" "$output_dir/receipts"

clone_at() {
  local url="$1"
  local commit="$2"
  local destination="$3"
  local log="$4"
  git clone --filter=blob:none --no-checkout "$url" "$destination" >"$log" 2>&1
  git -C "$destination" checkout --detach "$commit" >>"$log" 2>&1
  test "$(git -C "$destination" rev-parse HEAD)" = "$commit"
  test -z "$(git -C "$destination" status --porcelain)"
}

ec_repo="$work_dir/eudi-official"
ec_clone_log="$output_dir/raw/eudi-official-clone.log"
ec_run_log="$output_dir/raw/eudi-official-test.log"
clone_at \
  "https://github.com/eu-digital-identity-wallet/eudi-srv-verifier-endpoint" \
  "db5442501ea06907e614377a20d802748e8bfddb" \
  "$ec_repo" "$ec_clone_log"
mkdir -p \
  "$ec_repo/src/test/kotlin/eu/europa/ec/eudi/verifier/endpoint/adapter/out/sdjwtvc" \
  "$ec_repo/src/test/resources"
cp /kit/external-tests/eudi-official/TycheIndependentReturnTest.kt \
  "$ec_repo/src/test/kotlin/eu/europa/ec/eudi/verifier/endpoint/adapter/out/sdjwtvc/"
cp /kit/corpus.json "$ec_repo/src/test/resources/tyche-independent-return-corpus.json"
(
  cd "$ec_repo"
  ./gradlew test \
    --tests 'eu.europa.ec.eudi.verifier.endpoint.adapter.out.sdjwtvc.TycheIndependentReturnTest' \
    --no-daemon --console=plain
) >"$ec_run_log" 2>&1
ec_xml="$(find "$ec_repo/build/test-results/test" -type f -name 'TEST-*TycheIndependentReturnTest.xml' -print -quit)"
test -n "$ec_xml"
cp "$ec_xml" "$output_dir/raw/eudi-official-test.xml"

walt_repo="$work_dir/waltid"
walt_clone_log="$output_dir/raw/waltid-clone.log"
walt_run_log="$output_dir/raw/waltid-test.log"
clone_at \
  "https://github.com/walt-id/waltid-identity" \
  "f773918a3ad226ba7c0908d58941f18a3b89591d" \
  "$walt_repo" "$walt_clone_log"
walt_module="$walt_repo/waltid-libraries/credentials/waltid-verification-policies2"
mkdir -p "$walt_module/src/jvmTest/kotlin/id/walt/policies2/vc" \
  "$walt_module/src/jvmTest/resources"
cp /kit/external-tests/waltid/TycheIndependentReturnTest.kt \
  "$walt_module/src/jvmTest/kotlin/id/walt/policies2/vc/"
cp /kit/corpus.json "$walt_module/src/jvmTest/resources/tyche-independent-return-corpus.json"
(
  cd "$walt_repo"
  ./gradlew ':waltid-libraries:credentials:waltid-verification-policies2:jvmTest' \
    --tests 'id.walt.policies2.vc.TycheIndependentReturnTest' \
    --no-daemon --console=plain
) >"$walt_run_log" 2>&1
walt_xml="$(find "$walt_module/build/test-results/jvmTest" -type f -name 'TEST-*TycheIndependentReturnTest.xml' -print -quit)"
test -n "$walt_xml"
cp "$walt_xml" "$output_dir/raw/waltid-test.xml"

python3 /kit/emit_return.py \
  --output "$output_dir" \
  --ec-repo "$ec_repo" \
  --walt-repo "$walt_repo" \
  --control "$control" \
  --independent "$independent" \
  --controller-id "$controller_id" \
  --relationship "$relationship"

python3 /kit/verify_return.py \
  --return-dir "$output_dir" \
  --schema /kit/receipt.schema.json \
  --corpus /kit/corpus.json

(
  cd "$output_dir"
  find . -type f ! -name RETURN-SHA256SUMS -printf '%P\n' \
    | LC_ALL=C sort \
    | while IFS= read -r file; do sha256sum "$file"; done \
    >RETURN-SHA256SUMS
)
chmod -R a+rX "$output_dir"
