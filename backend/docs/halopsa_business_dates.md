# HaloPSA business date mapping

The backend keeps `ingested_at` as the storage ingestion timestamp and maps HaloPSA business dates into dedicated nullable columns:

- `ticket_created_at`: `created`, `datecreated`, `date_created`, `dateoccurred`, `date_opened`, `opened_at`, `dateopened`
- `ticket_updated_at`: `updated`, `last_update`, `lastupdated`, `dateupdated`
- `ticket_closed_at`: `closed`, `closed_at`, `dateclosed`, `resolved_at`

Invalid or unsupported provider date values fail closed to `NULL` and never block the whole ticket ingestion. No raw payload or field value is logged by the mapper.
