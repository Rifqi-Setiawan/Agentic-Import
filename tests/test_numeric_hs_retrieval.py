"""Additional protected regression for numeric HS candidate lookup."""
import pytest
from src.core.catalog import get_official_catalog
from src.services.analysis import search_candidates

class CatalogRepo:
    def rows(self, *_):
        return [dict(hs_code=c, description_id=r['description_id'], description_en=r['description_en'],
                     bm_rate=None, ppn_rate=None, pph_rate=None, lartas_coverage='unknown', source='BTKI 2022 DJBC')
                for c,r in get_official_catalog().items()]

@pytest.mark.parametrize('query,prefix', [('841370','841370'),('8413.70','841370'),('85365099','85365099')])
def test_numeric_hs_queries_are_code_constrained(query,prefix):
    rows=search_candidates(CatalogRepo(),query)
    assert rows and all(r['hs_code'].startswith(prefix) for r in rows)

def test_unknown_queries_do_not_return_arbitrary_codes():
    assert search_candidates(CatalogRepo(),'99999999') == []
    assert search_candidates(CatalogRepo(),'zzqxxvnunknown') == []

