# Study-authored oracle mutation analysis — results

- **Executed:** 2026-08-12
- **Operator:** `RULE_CONDITION_FALSE`
- **Frozen vectors:** 36
- **Rules:** 17
- **Implementation paths:** Python, JavaScript and jq

## Result

| Path | Generated | Valid | Killed | Survived | Invalid | Score |
|---|---:|---:|---:|---:|---:|---:|
| Python | 17 | 17 | 17 | 0 | 0 | 100% |
| JavaScript | 17 | 17 | 17 | 0 | 0 | 100% |
| jq | 17 | 17 | 17 | 0 | 0 | 100% |
| **Total** | **51** | **51** | **51** | **0** | **0** | **100%** |

Every mutant disabled exactly one rejection rule by replacing its condition with `false` in a
temporary copy. A mutant was killed when at least one vector's verdict or reason differed from the
frozen oracle. Original sources were never edited, and every unmutated implementation was required
to match the full frozen oracle before its mutants ran.

## Interpretation

The result demonstrates complete reachability for the declared rule-omission operator: the corpus
detects total omission of every one of its 17 encoded rejection rules in all three study-authored
paths. This is useful internal-validity evidence because it is stronger than three-path agreement
alone.

The 100% score is not evidence that the corpus is complete. The corpus intentionally contains at
least one vector for every reason code, so rule omission is a favourable but transparent operator.
No boundary inversion, wrong comparator, wrong set direction, precedence swap, timestamp-unit,
reason-mapping or multi-fault mutant was tested. Those would constitute a separate, stronger
operator family and must report their pre-improvement and post-improvement scores if attempted.

## Claim boundary

- These are mutants of study-authored toy/profile evaluators, not maintained verifier products.
- Mutation score does not establish independence, deployed correctness or EUDIW/FCAF conformance.
- The local mutation of the study-authored disclosure rule does not execute or identify a held
  real-stack disclosure-binding reproducer.
- The machine-readable result and 51-row kill matrix are `mutation-results.json` and
  `kill-matrix.csv`.
