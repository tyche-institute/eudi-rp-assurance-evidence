# EUDIW Assurance Graph v0.1

This is a deterministic, machine-readable join across the Tyche relying-party assurance profile,
candidate RP-as-SUT objectives, the first executed common-presentation case, three pinned
implementations and their decision-provenance receipts.

It answers four bounded questions:

1. Which candidate objective operationalises each of the 17 research-profile rules?
2. Which objective has reached a full local test specification?
3. Which exact corpus and pinned implementations produced evidence for that case?
4. Where does evidence stop: Tyche-controlled execution, independent execution, or official
   adoption?

The graph is a research index. An edge means the stated, typed relationship only. It does not turn
a research rule into an official requirement, a local test into FCAF coverage, or a maintained-stack
execution into independent reproduction.

Build and verify:

```sh
python3 build_graph.py
python3 verify_graph.py
sha256sum -c SHA256SUMS
```

`build_graph.py --check` refuses a stale generated graph. `verify_graph.py` validates the JSON
Schema, graph topology, 17-rule one-to-one mapping, local evidence references and the underlying
common-presentation receipt packet.

