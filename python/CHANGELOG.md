# Changelog

## bedrock-bio 3.0

* **Requires DuckDB 2.0 (breaking).** `duckdb>=2.0.0`.
* `load_table()` now runs each relation on its own cursor, so relations can be
  used from several threads at once and a partly-read result (for example an
  open Arrow reader) no longer blocks other queries. DuckDB 2.0 rejects both on
  a single shared connection. Cursors share the session's cache of downloaded
  data, so repeated queries stay fast.
* The S3 settings are now set with `SET GLOBAL` so those cursors inherit them.
* Fixed a race when several threads make their first call at once: the manifest
  and connection are now built in full under a lock before other threads can
  see them. Previously a thread could get a partly loaded manifest ("not found
  in manifest") or a connection that was still being set up.

## bedrock-bio 2.0.0

* Reads are now anonymous over HTTPS — the client no longer fetches
  `credentials.json` or creates an R2 S3 secret. No API keys are required.
  Partition pruning and predicate pushdown are unchanged.
* **Removed `reset()` (breaking).** It existed to clear cached credentials
  after rotation; with credential-free reads it no longer serves a purpose.
* **Manifest v2 (breaking).** The client now reads the v2 `manifest.json` and
  hard-gates on `version == 2`; older client releases reading v1 must upgrade.
  `describe_table()` now returns `context`, `columns`, and `partitions`
  (each partition column carrying its allowed `values` and `default`);
  `describe_namespace()` returns `name`, `citation`, `license`, `context`, and
  the namespace's tables. Column entries no longer carry `allowed_values`
  (enumerated values live under `partitions`).

## bedrock-bio 1.4.1

* `reset()`: now exported — clears the cached manifest, credentials, and
  connection (useful after credentials are rotated during a session).
* `BB_ENV=dev` points the client at the development data host
  (`data-dev.bedrock.bio`).
* Internal: timeouts on manifest and credentials requests.

## bedrock-bio 1.4.0

* `list_namespaces()`: list available namespaces (data sources).
* `describe_namespace()`: view namespace metadata, citation, license,
  instructions, and the namespace's tables.

## bedrock-bio 1.3.1

* Internal: hardened SQL string handling for catalog-derived paths and
  credentials.
* Internal: updated upstream manifest endpoint URL.

## bedrock-bio 1.3.0

* Initial release.
* `list_tables()`: list available tables.
* `load_table()`: lazily query a table with optional partition filters and
  predicate pushdown via DuckDB and Apache Iceberg.
* `describe_table()`: view table metadata, citation, and column definitions.
