#!/usr/bin/env bash
set -euo pipefail

packet_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
corpus_dir="$packet_dir/common-presentation-corpus"
results_dir="$packet_dir/results"
receipt_dir="$results_dir/common-presentation-provenance"
work_dir="$(mktemp -d /tmp/tyche-common-presentation-XXXXXX)"
sdk_root="${TYCHE_ANDROID_SDK_ROOT:-$work_dir/android-sdk}"

cleanup() {
  rm -rf "$work_dir"
}
trap cleanup EXIT

mkdir -p "$receipt_dir"
python3 "$corpus_dir/generate_fixture.py"
(
  cd "$corpus_dir"
  sha256sum -c SHA256SUMS
)

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
    "paths": [e["path"] for e in entries], "sha256": h.hexdigest(), "files": entries
}, sort_keys=True) + "\n")
PY
}

ec_repo="$work_dir/eudi-official"
ec_clone_log="$results_dir/common-presentation-eudi-official-clone-2026-08-12.log"
ec_log="$results_dir/common-presentation-eudi-official-2026-08-12.log"
clone_at \
  "https://github.com/eu-digital-identity-wallet/eudi-srv-verifier-endpoint" \
  "db5442501ea06907e614377a20d802748e8bfddb" \
  "$ec_repo" "$ec_clone_log"
dependency_manifest "$ec_repo" "$work_dir/ec-dependencies.json" \
  build.gradle.kts settings.gradle.kts gradle/libs.versions.toml gradle/wrapper/gradle-wrapper.properties
mkdir -p \
  "$ec_repo/src/test/kotlin/eu/europa/ec/eudi/verifier/endpoint/adapter/out/sdjwtvc" \
  "$ec_repo/src/test/resources"
cp "$packet_dir/external-tests/eudi-official/TycheCommonSdJwtNegativeTest.kt" \
  "$ec_repo/src/test/kotlin/eu/europa/ec/eudi/verifier/endpoint/adapter/out/sdjwtvc/"
cp "$corpus_dir/corpus.json" "$ec_repo/src/test/resources/tyche-common-sdjwt-corpus.json"
(
  cd "$ec_repo"
  ./gradlew test \
    --tests 'eu.europa.ec.eudi.verifier.endpoint.adapter.out.sdjwtvc.TycheCommonSdJwtNegativeTest' \
    --no-daemon --console=plain
) >"$ec_log" 2>&1

mpz_repo="$work_dir/multipaz"
mpz_clone_log="$results_dir/common-presentation-multipaz-clone-2026-08-12.log"
mpz_log="$results_dir/common-presentation-multipaz-2026-08-12.log"
clone_at \
  "https://github.com/openwallet-foundation/multipaz" \
  "570aa2475bd5b7e437d9041bf8ff1127bcf86cfb" \
  "$mpz_repo" "$mpz_clone_log"
dependency_manifest "$mpz_repo" "$work_dir/mpz-dependencies.json" \
  build.gradle.kts settings.gradle.kts gradle/libs.versions.toml \
  gradle/wrapper/gradle-wrapper.properties multipaz/build.gradle.kts
git -C "$mpz_repo" apply --check "$packet_dir/build-isolation/multipaz-jvm-only.patch"
git -C "$mpz_repo" apply "$packet_dir/build-isolation/multipaz-jvm-only.patch"
mkdir -p "$mpz_repo/multipaz/src/jvmTest/kotlin/org/multipaz/sdjwt" "$mpz_repo/multipaz/src/jvmTest/resources"
cp "$packet_dir/external-tests/multipaz/TycheCommonSdJwtNegativeTest.kt" \
  "$mpz_repo/multipaz/src/jvmTest/kotlin/org/multipaz/sdjwt/"
cp "$corpus_dir/corpus.json" "$mpz_repo/multipaz/src/jvmTest/resources/tyche-common-sdjwt-corpus.json"

if [[ ! -d "$sdk_root/cmdline-tools" ]]; then
  archive="commandlinetools-linux-15859902_latest.zip"
  expected="4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583"
  mkdir -p "$sdk_root/cmdline-tools"
  curl --fail --location --silent --show-error \
    --output "$sdk_root/$archive" "https://dl.google.com/android/repository/$archive"
  printf '%s  %s\n' "$expected" "$sdk_root/$archive" | sha256sum --check
  unzip -q "$sdk_root/$archive" -d "$sdk_root/cmdline-tools"
  mv "$sdk_root/cmdline-tools/cmdline-tools" "$sdk_root/cmdline-tools/latest"
fi
(
  cd "$mpz_repo"
  ANDROID_HOME="$sdk_root" ANDROID_SDK_ROOT="$sdk_root" \
    ./gradlew :multipaz:jvmTest \
      --tests 'org.multipaz.sdjwt.TycheCommonSdJwtNegativeTest' \
      -Pdisable.web.targets=true --no-daemon --console=plain
) >"$mpz_log" 2>&1

walt_repo="$work_dir/waltid"
walt_clone_log="$results_dir/common-presentation-waltid-clone-2026-08-12.log"
walt_log="$results_dir/common-presentation-waltid-2026-08-12.log"
clone_at \
  "https://github.com/walt-id/waltid-identity" \
  "f773918a3ad226ba7c0908d58941f18a3b89591d" \
  "$walt_repo" "$walt_clone_log"
dependency_manifest "$walt_repo" "$work_dir/walt-dependencies.json" \
  build.gradle.kts settings.gradle.kts gradle/libs.versions.toml \
  gradle/wrapper/gradle-wrapper.properties \
  waltid-libraries/credentials/waltid-verification-policies2/build.gradle.kts
walt_module="$walt_repo/waltid-libraries/credentials/waltid-verification-policies2"
mkdir -p "$walt_module/src/jvmTest/kotlin/id/walt/policies2/vc" "$walt_module/src/jvmTest/resources"
cp "$packet_dir/external-tests/waltid/TycheCommonSdJwtNegativeTest.kt" \
  "$walt_module/src/jvmTest/kotlin/id/walt/policies2/vc/"
cp "$corpus_dir/corpus.json" "$walt_module/src/jvmTest/resources/tyche-common-sdjwt-corpus.json"
(
  cd "$walt_repo"
  ./gradlew ':waltid-libraries:credentials:waltid-verification-policies2:jvmTest' \
    --tests 'id.walt.policies2.vc.TycheCommonSdJwtNegativeTest' \
    --no-daemon --console=plain
) >"$walt_log" 2>&1

python3 - \
  "$packet_dir" "$receipt_dir" "$corpus_dir/corpus.json" \
  "$ec_repo" "$ec_log" "$ec_clone_log" "$work_dir/ec-dependencies.json" \
  "$mpz_repo" "$mpz_log" "$mpz_clone_log" "$work_dir/mpz-dependencies.json" \
  "$walt_repo" "$walt_log" "$walt_clone_log" "$work_dir/walt-dependencies.json" <<'PY'
from __future__ import annotations
import hashlib, json, platform, re, subprocess, sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

(packet, receipt_dir, corpus_path,
 ec_repo, ec_log, ec_clone_log, ec_dep,
 mpz_repo, mpz_log, mpz_clone_log, mpz_dep,
 walt_repo, walt_log, walt_clone_log, walt_dep) = map(Path, sys.argv[1:])

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
def test_observation(results, expected_reason):
    files = list(results.glob("TEST-*TycheCommon*.xml"))
    if len(files) != 1:
        raise SystemExit(f"expected one Tyche XML in {results}, got {len(files)}")
    root = ET.parse(files[0]).getroot()
    counts = {key: int(root.attrib.get(key, 0)) for key in ("tests", "failures", "errors", "skipped")}
    if counts != {"tests": 1, "failures": 0, "errors": 0, "skipped": 0}:
        raise SystemExit(f"unexpected test counts in {files[0]}: {counts}")
    output = root.findtext("system-out") or ""
    match = re.search(r"TYCHE_OBSERVED_REASON=(.+)", output)
    observed = match.group(1).strip() if match else "missing"
    if observed != expected_reason:
        raise SystemExit(f"unexpected observed reason: {observed}")

corpus = json.loads(corpus_path.read_text())
corpus_sha = sha(corpus_path)
context = corpus["fixed_context"]
negative = next(c for c in corpus["cases"] if c["case_id"] == "RP_WS_SM_IssuerAuthentication_001")
schema = json.loads((packet / "decision-provenance-receipt.schema.json").read_text())
validator = Draft202012Validator(schema, format_checker=FormatChecker())
executed_at = datetime.now(timezone.utc).isoformat()

configs = [
    {
        "adapter": "eudi-official", "repo": ec_repo,
        "url": "https://github.com/eu-digital-identity-wallet/eudi-srv-verifier-endpoint",
        "commit": "db5442501ea06907e614377a20d802748e8bfddb",
        "log": ec_log, "clone_log": ec_clone_log, "dep": ec_dep,
        "xml_dir": ec_repo / "build/test-results/test", "reason": "ContainsInvalidJwt",
        "policy": "TypeMetadataPolicy.NotUsed; fixed clock; trust callback accepts corpus x5c for the classified test VCT",
        "command": "./gradlew test --tests eu.europa.ec.eudi.verifier.endpoint.adapter.out.sdjwtvc.TycheCommonSdJwtNegativeTest",
    },
    {
        "adapter": "multipaz", "repo": mpz_repo,
        "url": "https://github.com/openwallet-foundation/multipaz",
        "commit": "570aa2475bd5b7e437d9041bf8ff1127bcf86cfb",
        "log": mpz_log, "clone_log": mpz_clone_log, "dep": mpz_dep,
        "xml_dir": mpz_repo / "multipaz/build/test-results/jvmTest",
        "reason": "SignatureVerificationException: Error validating issuer signature",
        "policy": "explicit corpus issuer JWK; fixed nonce, audience and KB iat; JVM-only build-isolation patch",
        "command": ":multipaz:jvmTest --tests org.multipaz.sdjwt.TycheCommonSdJwtNegativeTest -Pdisable.web.targets=true",
    },
    {
        "adapter": "waltid", "repo": walt_repo,
        "url": "https://github.com/walt-id/waltid-identity",
        "commit": "f773918a3ad226ba7c0908d58941f18a3b89591d",
        "log": walt_log, "clone_log": walt_clone_log, "dep": walt_dep,
        "xml_dir": walt_repo / "waltid-libraries/credentials/waltid-verification-policies2/build/test-results/jvmTest",
        "reason": "id.walt.crypto2.jose.InvalidJwsSignatureException: Invalid JWS signature",
        "policy": "CredentialSignaturePolicy default JWS allowlist; issuer key resolved from corpus x5c",
        "command": ":waltid-libraries:credentials:waltid-verification-policies2:jvmTest --tests id.walt.policies2.vc.TycheCommonSdJwtNegativeTest",
    },
]

for cfg in configs:
    test_observation(cfg["xml_dir"], cfg["reason"])
    dep = json.loads(cfg["dep"].read_text())
    source_dir = "eudi-official" if cfg["adapter"] == "eudi-official" else cfg["adapter"]
    test_source = packet / "external-tests" / source_dir / "TycheCommonSdJwtNegativeTest.kt"
    patch_hash = sha(packet / "build-isolation/multipaz-jvm-only.patch") if cfg["adapter"] == "multipaz" else "no-build-patch"
    build_material = "\n".join([cfg["commit"], corpus_sha, sha(test_source), cfg["command"], patch_hash])
    evidence = [{"path": f"results/{p.name}", "sha256": sha(p)} for p in (cfg["clone_log"], cfg["log"])]
    receipt = {
        "schema_version": "1.0.0-research",
        "receipt_id": f"urn:tyche:eudi:provenance:{cfg['adapter']}:RP_WS_SM_IssuerAuthentication_001:2026-08-12",
        "adapter_id": cfg["adapter"], "repository": cfg["url"],
        "source_commit": cfg["commit"], "source_tree": git(cfg["repo"], "rev-parse", "HEAD^{tree}"),
        "dependency_material": {"paths": dep["paths"], "sha256": dep["sha256"]},
        "build_configuration_sha256": hashlib.sha256(build_material.encode()).hexdigest(),
        "policy_configuration_sha256": hashlib.sha256(cfg["policy"].encode()).hexdigest(),
        "trust_source": {"type": "synthetic-x5c-and-pinned-jwk", "revision": corpus["corpus_id"], "sha256": corpus_sha},
        "evaluation_context": {
            "evaluated_at": context["evaluated_at"], "nonce": context["nonce"], "audience": context["audience"]
        },
        "input": {"format": corpus["format"], "corpus_sha256": corpus_sha, "presentation_sha256": negative["presentation_sha256"]},
        "baseline": {"case_id": "COMMON-SDJWT-BASELINE-001", "verdict": "ACCEPT"},
        "mutation": {"case_id": "RP_WS_SM_IssuerAuthentication_001", "verdict": "REJECT", "raw_reason": cfg["reason"]},
        "normalized_reason": "INVALID_ISSUER_SIGNATURE", "executed_at": executed_at,
        "execution_control": "tyche-controlled-local-run", "production_source_unmodified": True,
        "evidence_files": evidence,
        "claim_boundary": (
            "Pinned-stack execution of one synthetic common compact presentation and one isolated issuer-signature mutation. "
            "The run demonstrates the stated library/verifier decision at this commit and configuration; it is not an "
            "independent reproduction, full RP-service workflow, product certification, or EUDIW/FCAF conformance result."
        ),
    }
    errors = sorted(validator.iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        raise SystemExit(f"{cfg['adapter']}: {errors[0].message}")
    output = receipt_dir / f"{cfg['adapter']}-RP_WS_SM_IssuerAuthentication_001-2026-08-12.json"
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

summary = {
    "schema_version": "1.0.0-research", "executed_at": executed_at,
    "corpus_sha256": corpus_sha, "presentation_sha256": negative["presentation_sha256"],
    "case_id": negative["case_id"], "adapters": [c["adapter"] for c in configs],
    "baseline_verdicts": ["ACCEPT"] * 3, "mutation_verdicts": ["REJECT"] * 3,
    "environment": {"os": platform.platform(), "architecture": platform.machine()},
    "claim_boundary": "Three Tyche-controlled pinned-stack executions; not independent reproduction or conformance certification."
}
(packet / "results/common-presentation-probe-2026-08-12.json").write_text(
    json.dumps(summary, indent=2, sort_keys=True) + "\n"
)
PY

python3 "$packet_dir/tools/verify_common_presentation_packet.py"
