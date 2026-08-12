# Mutation analysis of the study-authored oracle

Status: **post-submission local experiment; not incorporated; not a real-stack result**.

The submitted study reports agreement across three heterogeneous, study-authored executable paths
for 36 synthetic vectors. Agreement alone does not show whether the corpus would detect defects in
those paths. This analysis therefore generates one rule-omission mutant per rejection rule and per
implementation by replacing only that rule's condition with `false` in a temporary copy.

The design yields 17 rule mutants × 3 implementation paths = 51 candidate mutants. A valid mutant
is killed when at least one vector's observed verdict or reason differs from the frozen corpus
oracle. Compile/runtime-invalid mutants are excluded from the denominator rather than counted as
killed. Surviving valid mutants are reported, not hidden or used to silently tune the corpus.

Run:

```sh
python3 run_mutation_analysis.py
python3 verify_mutation_analysis.py
sha256sum -c SHA256SUMS
```

The original verifier sources and frozen corpus are read-only inputs. Mutated files exist only in a
temporary directory and are removed after execution.

Claim boundary: mutation score measures sensitivity to this declared rule-omission operator in
three study-authored implementations. It does not establish completeness, independence, deployed
behavior, real-stack correctness or EUDIW/FCAF conformance.
