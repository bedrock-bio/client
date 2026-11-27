from concurrent.futures import ThreadPoolExecutor

import duckdb
import pytest
from conftest import requires_live_v2_manifest

from bedrock_bio.load_table import load_table


class TestLoadTable:
    def test_errors_on_unknown_table(self):
        requires_live_v2_manifest()
        with pytest.raises(ValueError, match="not found in manifest"):
            load_table("not_a_table")

    def test_returns_relation(self):
        requires_live_v2_manifest()
        assert isinstance(load_table("dbsnp.vcf"), duckdb.DuckDBPyRelation)

    def test_filter_narrows(self):
        requires_live_v2_manifest()
        rel = (
            load_table("dbsnp.vcf")
            .filter("assembly = 'GRCh38' AND chromosome = '22'")
            .limit(5)
        )
        rows = rel.fetchall()
        assert len(rows) == 5
        chromosome = rel.columns.index("chromosome")
        assert {row[chromosome] for row in rows} == {"22"}

    def test_select_limits_columns(self):
        requires_live_v2_manifest()
        rel = (
            load_table("dbsnp.vcf")
            .filter("assembly = 'GRCh38' AND chromosome = '22'")
            .select("chromosome", "position")
            .limit(5)
        )
        assert rel.columns == ["chromosome", "position"]

    def test_filters_and_projection_push_down_to_scan(self):
        requires_live_v2_manifest()
        plan = (
            load_table("dbsnp.vcf")
            .filter("assembly = 'GRCh38' AND chromosome = '22' AND position > 50000000")
            .select("rsid, position")
            .explain()
        )
        assert "ICEBERG_SCAN" in plan
        assert "FILTER" not in plan
        assert "assembly='GRCh38'" in plan
        assert "chromosome='22'" in plan
        assert "position>50000000" in plan
        assert "ref_allele" not in plan
        assert "alt_allele" not in plan

    def test_reads_second_real_table(self):
        requires_live_v2_manifest()
        rows = load_table("ensembl.taxonomies").limit(3).fetchall()
        assert len(rows) == 3


class TestLoadTableConcurrency:
    """DuckDB 2.0 refuses a second query on a busy connection; each relation
    must run on its own cursor."""

    WHERE = (
        "assembly_accession = 'GCF_000001405.40' AND chromosome = '22' "
        "AND position BETWEEN {lo} AND {hi}"
    )

    def count(self, i: int) -> int:
        lo = 20_000_000 + i * 1_000_000
        where = self.WHERE.format(lo=lo, hi=lo + 100_000)
        rel = load_table("dbsnp.variants").filter(where).aggregate("count(*)")
        return rel.fetchall()[0][0]

    def test_query_while_another_result_is_open(self):
        pytest.importorskip("pyarrow")  # Arrow readers need it
        requires_live_v2_manifest()
        where = self.WHERE.format(lo=20_000_000, hi=21_000_000)
        rel = load_table("dbsnp.variants").filter(where).select("rsid")
        reader = rel.to_arrow_reader(batch_size=1_000)
        next(iter(reader))  # leave the first result unfinished
        assert self.count(1) > 0

    def test_parallel_threads(self):
        requires_live_v2_manifest()
        with ThreadPoolExecutor(max_workers=4) as pool:
            counts = list(pool.map(self.count, range(4)))
        assert all(n > 0 for n in counts)
