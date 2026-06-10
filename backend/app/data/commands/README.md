# Controlled HaloPSA extraction command

`controlled_halopsa_extract.py` is a fail-closed entrypoint for future controlled HaloPSA extraction.

- It does not load `.env` files and never logs secret values.
- `HALO_PAGE_SIZE` defaults to `1` when absent and is capped at `5`.
- Standalone execution validates runtime variables, then blocks unless a transport and repository are explicitly injected by integration code.
- Real extraction must go through `TicketIngestionService`, which applies PII/HMAC guardrails before repository storage.

Future runtime wiring must provide `HaloPsaTransport` and `TicketRepository` implementations explicitly; tests should use synthetic mocks only.
