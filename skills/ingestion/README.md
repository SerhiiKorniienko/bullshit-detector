# Ingestion

The layer that turns any source into clean text + metadata. Analysis skills build on it and never talk to platforms directly — new sources mean a new adapter here, zero changes there.

## Model-invoked

- **[fetch-content](./fetch-content/SKILL.md)** — Any URL or file → normalized text with metadata. YouTube transcripts (no API key), articles, PDFs, tweets/X posts, local files. One script, auto-detects source type.
- **[coverage-check](./coverage-check/SKILL.md)** — How many *independent origins* are behind coverage of a claim. Collapses reprints and wire copy into one source and flags publication bursts, so the detector counts origins instead of URLs. GDELT, no API key.
