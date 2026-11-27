import duckdb

from .config import config


def load_table(name: str) -> duckdb.DuckDBPyRelation:
    """Lazily query a table.

    Parameters
    ----------
    name : str
        Table identifier.

    Returns
    -------
    duckdb.DuckDBPyRelation
        A lazy relation that can be further filtered, selected, or collected.
        Filter on partition columns (see ``describe_table()``) for fastest reads.
        Data downloaded during a session is cached locally, so repeated or
        refined queries in the same Python session are much faster.

    Examples
    --------
    >>> import bedrock_bio as bb
    >>> df = (
    ...     bb.load_table("dbsnp.variants")
    ...     .filter("assembly_accession = 'GCF_000001405.40' AND chromosome = '22'")
    ...     .select("rsid, position, ref_allele, alt_allele")
    ...     .limit(5)
    ...     .df()
    ... )
    """
    manifest = config.get_manifest()
    if name not in manifest:
        raise ValueError(
            f"Table '{name}' not found in manifest. "
            f"See list_tables() for available tables."
        )

    # Each relation gets its own cursor. DuckDB 2.0 refuses a second query on a
    # connection that is busy (another thread) or has an unfinished result (an
    # open Arrow reader), so a shared connection breaks parallel tool calls.
    # Cursors share the database, so the downloaded-data cache is still shared.
    cursor = config.get_connection().cursor()
    escaped = manifest[name]["iceberg_json"].replace("'", "''")
    return cursor.sql(f"SELECT * FROM iceberg_scan('{escaped}')")
