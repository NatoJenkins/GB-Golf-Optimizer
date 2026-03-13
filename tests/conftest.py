import pytest

SAMPLE_ROSTER_CSV = """Player,Positions,Team,Multiplier,Overall,Franchise,Rookie,Tradeable,Salary,Collection,Status,Expires
Scottie Scheffler,G,ATL,1.5,90,False,False,True,12000,Core,Active,2026-12-31
Rory McIlroy,G,TOR,1.2,88,False,False,True,11000,Weekly Collection,Active,2026-06-30
Ludvig Aberg,G,BOS,1.3,85,False,True,True,9000,Core,Active,2026-09-15
Tommy Fleetwood,G,NY,1.1,82,False,False,True,8000,Core,Active,2025-01-01
Collin Morikawa,G,LA,1.4,87,False,False,True,10000,Weekly Collection,Active,2026-12-31
Xander Schauffele,G,CHI,1.2,84,False,False,True,9500,Core,Active,2026-12-31
No Projection Guy,G,ATL,1.0,75,False,False,True,7000,Core,Active,2026-12-31
Zero Salary Guy,G,BOS,1.0,70,False,False,True,0,Core,Active,2026-12-31
"""

SAMPLE_PROJECTIONS_CSV = """player,projected_score
Scottie Scheffler,72.5
Rory McIlroy,68.3
Ludvig Aberg,65.1
Tommy Fleetwood,60.0
Collin Morikawa,70.2
Xander Schauffele,67.8
bad_row_no_score,
"""

VALID_CONFIG_DICT = {
    "contests": [
        {
            "name": "The Tips",
            "salary_min": 30000,
            "salary_max": 64000,
            "roster_size": 6,
            "max_entries": 3,
            "collection_limits": {"Weekly Collection": 3, "Core": 6}
        },
        {
            "name": "The Intermediate Tee",
            "salary_min": 20000,
            "salary_max": 52000,
            "roster_size": 5,
            "max_entries": 2,
            "collection_limits": {"Weekly Collection": 2, "Core": 5}
        }
    ]
}


@pytest.fixture
def sample_roster_csv():
    return SAMPLE_ROSTER_CSV


@pytest.fixture
def sample_projections_csv():
    return SAMPLE_PROJECTIONS_CSV


@pytest.fixture
def valid_config_dict():
    return VALID_CONFIG_DICT


@pytest.fixture
def tmp_csv_file(tmp_path):
    def _write(content: str, filename: str = "test.csv") -> str:
        p = tmp_path / filename
        p.write_text(content, encoding="utf-8")
        return str(p)
    return _write
