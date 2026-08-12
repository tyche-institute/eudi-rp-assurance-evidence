#!/usr/bin/env bash
set -euo pipefail

census_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
packet_dir="$(cd "$census_dir/.." && pwd)"
results_dir="$census_dir/results"
work_dir="$(mktemp -d /tmp/tyche-decision-scope-XXXXXX)"
sdk_root="${TYCHE_ANDROID_SDK_ROOT:-${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}}"

if [[ -z "$sdk_root" || ! -d "$sdk_root" ]]; then
  echo "Set TYCHE_ANDROID_SDK_ROOT, ANDROID_SDK_ROOT or ANDROID_HOME to an installed Android SDK." >&2
  exit 2
fi

cleanup() {
  rm -rf "$work_dir"
}
trap cleanup EXIT

mkdir -p "$results_dir/receipts"
python3 "$census_dir/generate_corpus.py"

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

dependency_manifest() {
  local repository="$1"
  local output="$2"
  shift 2
  python3 - "$repository" "$output" "$@" <<'PY'
import hashlib, json, sys
from pathlib import Path
root, output, *relative = sys.argv[1:]
root = Path(root)
h = hashlib.sha256()
entries = []
for item in sorted(relative):
    path = root / item
    if not path.is_file():
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    entries.append({"path": item, "sha256": digest})
    h.update(item.encode() + b"\0" + bytes.fromhex(digest))
Path(output).write_text(json.dumps({
    "paths": [entry["path"] for entry in entries],
    "sha256": h.hexdigest(),
    "files": entries,
}, sort_keys=True) + "\n", encoding="utf-8")
PY
}

ec_repo="$work_dir/eudi-official"
ec_clone_log="$results_dir/decision-scope-eudi-official-clone-2026-08-12.log"
ec_run_log="$results_dir/decision-scope-eudi-official-2026-08-12.log"
clone_at \
  "https://github.com/eu-digital-identity-wallet/eudi-srv-verifier-endpoint" \
  "db5442501ea06907e614377a20d802748e8bfddb" \
  "$ec_repo" "$ec_clone_log"
dependency_manifest "$ec_repo" "$work_dir/ec-dependencies.json" \
  build.gradle.kts settings.gradle.kts gradle/libs.versions.toml gradle/wrapper/gradle-wrapper.properties
mkdir -p \
  "$ec_repo/src/test/kotlin/eu/europa/ec/eudi/verifier/endpoint/adapter/out/sdjwtvc" \
  "$ec_repo/src/test/resources"
cp "$census_dir/external-tests/eudi-official/TycheDecisionScopeCensusTest.kt" \
  "$ec_repo/src/test/kotlin/eu/europa/ec/eudi/verifier/endpoint/adapter/out/sdjwtvc/"
cp "$census_dir/corpus.json" "$ec_repo/src/test/resources/tyche-decision-scope-corpus.json"
(
  cd "$ec_repo"
  ./gradlew test \
    --tests 'eu.europa.ec.eudi.verifier.endpoint.adapter.out.sdjwtvc.TycheDecisionScopeCensusTest' \
    --no-daemon --console=plain
) >"$ec_run_log" 2>&1

mp_repo="$work_dir/multipaz"
mp_clone_log="$results_dir/decision-scope-multipaz-clone-2026-08-12.log"
mp_run_log="$results_dir/decision-scope-multipaz-2026-08-12.log"
clone_at \
  "https://github.com/openwallet-foundation/multipaz" \
  "570aa2475bd5b7e437d9041bf8ff1127bcf86cfb" \
  "$mp_repo" "$mp_clone_log"
dependency_manifest "$mp_repo" "$work_dir/mp-dependencies.json" \
  build.gradle.kts settings.gradle.kts gradle/libs.versions.toml \
  gradle/wrapper/gradle-wrapper.properties multipaz/build.gradle.kts
git -C "$mp_repo" apply --check "$packet_dir/build-isolation/multipaz-jvm-only.patch"
git -C "$mp_repo" apply "$packet_dir/build-isolation/multipaz-jvm-only.patch"
mkdir -p "$mp_repo/multipaz/src/jvmTest/kotlin/org/multipaz/sdjwt" \
  "$mp_repo/multipaz/src/jvmTest/resources"
cp "$census_dir/external-tests/multipaz/TycheDecisionScopeCensusTest.kt" \
  "$mp_repo/multipaz/src/jvmTest/kotlin/org/multipaz/sdjwt/"
cp "$census_dir/corpus.json" "$mp_repo/multipaz/src/jvmTest/resources/tyche-decision-scope-corpus.json"
(
  cd "$mp_repo"
  ANDROID_HOME="$sdk_root" ANDROID_SDK_ROOT="$sdk_root" \
    ./gradlew :multipaz:jvmTest \
      --tests 'org.multipaz.sdjwt.TycheDecisionScopeCensusTest' \
      -Pdisable.web.targets=true --no-daemon --console=plain
) >"$mp_run_log" 2>&1

walt_repo="$work_dir/waltid"
walt_clone_log="$results_dir/decision-scope-waltid-clone-2026-08-12.log"
walt_run_log="$results_dir/decision-scope-waltid-2026-08-12.log"
clone_at \
  "https://github.com/walt-id/waltid-identity" \
  "f773918a3ad226ba7c0908d58941f18a3b89591d" \
  "$walt_repo" "$walt_clone_log"
dependency_manifest "$walt_repo" "$work_dir/walt-dependencies.json" \
  build.gradle.kts settings.gradle.kts gradle/libs.versions.toml \
  gradle/wrapper/gradle-wrapper.properties \
  waltid-libraries/credentials/waltid-verification-policies2/build.gradle.kts
walt_module="$walt_repo/waltid-libraries/credentials/waltid-verification-policies2"
mkdir -p "$walt_module/src/jvmTest/kotlin/id/walt/policies2/vc" \
  "$walt_module/src/jvmTest/resources"
cp "$census_dir/external-tests/waltid/TycheDecisionScopeCensusTest.kt" \
  "$walt_module/src/jvmTest/kotlin/id/walt/policies2/vc/"
cp "$census_dir/corpus.json" "$walt_module/src/jvmTest/resources/tyche-decision-scope-corpus.json"
(
  cd "$walt_repo"
  ./gradlew ':waltid-libraries:credentials:waltid-verification-policies2:jvmTest' \
    --tests 'id.walt.policies2.vc.TycheDecisionScopeCensusTest' \
    --no-daemon --console=plain
) >"$walt_run_log" 2>&1

python3 "$census_dir/build_results.py" \
  "$ec_repo" "$ec_run_log" "$ec_clone_log" "$work_dir/ec-dependencies.json" \
  "$mp_repo" "$mp_run_log" "$mp_clone_log" "$work_dir/mp-dependencies.json" \
  "$walt_repo" "$walt_run_log" "$walt_clone_log" "$work_dir/walt-dependencies.json"
python3 "$census_dir/verify_results.py"
