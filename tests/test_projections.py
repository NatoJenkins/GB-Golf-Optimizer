def test_valid_projections_returns_dict(tmp_csv_file, sample_projections_csv):
    from gbgolf.data.projections import parse_projections_csv  # ImportError until Plan 02
    path = tmp_csv_file(sample_projections_csv)
    result, warnings = parse_projections_csv(path)
    assert isinstance(result, dict)
    assert "scottie scheffler" in result  # normalized key


def test_bad_row_skipped(tmp_csv_file, sample_projections_csv):
    from gbgolf.data.projections import parse_projections_csv
    path = tmp_csv_file(sample_projections_csv)
    result, warnings = parse_projections_csv(path)
    assert len(warnings) >= 1


def test_scores_are_float(tmp_csv_file, sample_projections_csv):
    from gbgolf.data.projections import parse_projections_csv
    path = tmp_csv_file(sample_projections_csv)
    result, _ = parse_projections_csv(path)
    for score in result.values():
        assert isinstance(score, float)
