# Controlled HaloPSA extraction command

`controlled_halopsa_extract.py` is a fail-closed entrypoint for future controlled HaloPSA extraction.

- It does not load `.env` files and never logs secret values.
- `HALO_PAGE_SIZE` defaults to `1` when absent and is passed through unchanged when strictly positive.
- `HALO_PAGE_NO` defaults to `1` when absent; the ticket query always sends `pageinate=true`.
- Standalone execution validates runtime variables, then blocks unless `HALOPSA_ENABLE_NETWORK=true` and `POSTGRES_ENABLE_WRITE=true` are both explicit.
- Real extraction must go through `TicketIngestionService`, which applies PII/HMAC guardrails before repository storage.
- PostgreSQL storage uses `backend/app/db/schema.sql`; the table is `clean_tickets` and contains no raw JSON/payload column.

Runtime wiring may use `POSTGRES_DSN` or the complete component set `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`; missing values fail closed without logging credentials. Tests should use synthetic mocks only.
