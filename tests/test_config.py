import json
import pytest


def test_valid_config(tmp_path, valid_config_dict):
    from gbgolf.data.config import load_contest_config  # ImportError until Plan 02
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(valid_config_dict))
    contests = load_contest_config(str(config_file))
    assert len(contests) >= 1
    assert contests[0].name == "The Tips"
    assert contests[0].salary_max == 64000
    assert contests[0].roster_size == 6


def test_invalid_config_missing_field(tmp_path):
    from gbgolf.data.config import load_contest_config
    bad = {"contests": [{"name": "The Tips"}]}  # missing required fields
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(bad))
    with pytest.raises(Exception):  # pydantic ValidationError
        load_contest_config(str(config_file))


def test_invalid_config_salary_range(tmp_path):
    from gbgolf.data.config import load_contest_config
    bad = {"contests": [{"name": "Bad Contest", "salary_min": 50000, "salary_max": 30000,
                          "roster_size": 6, "max_entries": 3,
                          "collection_limits": {"Core": 6, "Weekly Collection": 3}}]}
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(bad))
    with pytest.raises(Exception):
        load_contest_config(str(config_file))
