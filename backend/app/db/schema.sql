CREATE TABLE IF NOT EXISTS clean_tickets (
    id BIGSERIAL PRIMARY KEY,
    external_ticket_id TEXT NOT NULL UNIQUE,
    summary TEXT NOT NULL,
    details TEXT NOT NULL,
    status TEXT NOT NULL,
    priority TEXT,
    category TEXT,
    agent_id_pseudonym TEXT,
    ticket_created_at TIMESTAMPTZ NULL,
    ticket_updated_at TIMESTAMPTZ NULL,
    ticket_closed_at TIMESTAMPTZ NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT clean_tickets_agent_pseudonym_hmac_format CHECK (
        agent_id_pseudonym IS NULL OR agent_id_pseudonym LIKE 'hmac_sha256:%'
    )
);
