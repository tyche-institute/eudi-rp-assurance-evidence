#!/usr/bin/env bash
set -euo pipefail

packet_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$packet_dir"

python3 - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("assurance-cards.json").read_text(encoding="utf-8"))
assert data["schema_version"] == "0.1.0-research"
assert len(data["cards"]) == 4
assert len({card["id"] for card in data["cards"]}) == 4
assert all(len(card["minimum_evidence"]) == 4 for card in data["cards"])
serialized = json.dumps(data).lower()
for forbidden in ("traveller_name", "email_address", "contact-ledger", "respondent"):
    assert forbidden not in serialized
print("Structured cards PASS: four unique, privacy-minimised cards")
PY

xelatex -interaction=nonstopmode -halt-on-error travel-mobility-field-brief.tex >/dev/null
xelatex -interaction=nonstopmode -halt-on-error travel-mobility-field-brief.tex >/dev/null

test "$(pdfinfo travel-mobility-field-brief.pdf | awk '/^Pages:/ {print $2}')" = "1"
if rg -n 'Overfull|Underfull|LaTeX Warning' travel-mobility-field-brief.log; then
  printf '%s\n' 'PDF layout warning detected' >&2
  exit 1
fi

python3 - <<'PY'
import hashlib
from pathlib import Path

names = ("README.md", "assurance-cards.json", "build.sh", "travel-mobility-field-brief.pdf", "travel-mobility-field-brief.tex")
Path("SHA256SUMS").write_text("".join(
    f"{hashlib.sha256(Path(name).read_bytes()).hexdigest()}  {name}\n" for name in names
), encoding="utf-8")
PY
sha256sum -c SHA256SUMS
printf '%s\n' 'Travel/mobility field packet PASS'

