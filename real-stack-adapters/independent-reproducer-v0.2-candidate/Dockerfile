FROM eclipse-temurin@sha256:55fb9bf738f5d9b4a6c01b39337e3070d3e27370dd3c478fd1d5d3cd2233c6d8

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates git python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install --no-cache-dir \
      attrs==26.1.0 \
      jsonschema==4.26.0 \
      jsonschema-specifications==2025.9.1 \
      referencing==0.37.0 \
      rpds-py==0.30.0

LABEL org.opencontainers.image.title="Tyche EUDI Independent Reproducer Kit v0.2" \
      org.opencontainers.image.description="Two pinned JVM verifier entry points; no Android SDK" \
      org.opencontainers.image.source="https://github.com/tyche-institute/eudi-rp-assurance-evidence" \
      org.opencontainers.image.version="0.2.0"

ENV TYCHE_REPRO_BASE_IMAGE="eclipse-temurin@sha256:55fb9bf738f5d9b4a6c01b39337e3070d3e27370dd3c478fd1d5d3cd2233c6d8" \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /kit
COPY receipt-schema-v1.1-candidate/decision-provenance-receipt-1.1.schema.json /kit/receipt.schema.json
COPY decision-scope-census/corpus.json /kit/corpus.json
COPY independent-reproducer-v0.2-candidate/container/entrypoint.sh /kit/entrypoint.sh
COPY independent-reproducer-v0.2-candidate/container/emit_return.py /kit/emit_return.py
COPY independent-reproducer-v0.2-candidate/container/verify_return.py /kit/verify_return.py
COPY independent-reproducer-v0.2-candidate/container/external-tests /kit/external-tests

RUN chmod 0555 /kit/entrypoint.sh /kit/emit_return.py /kit/verify_return.py \
    && test -z "$(find / -type f -name sdkmanager -print -quit 2>/dev/null)"

ENTRYPOINT ["/kit/entrypoint.sh"]
