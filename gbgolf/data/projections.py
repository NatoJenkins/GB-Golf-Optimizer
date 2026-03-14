import csv
from gbgolf.data.matching import normalize_name


def parse_projections_csv(path: str) -> tuple[dict[str, float], list[str]]:
    """
    Parse projections CSV.
    Returns (projections_dict, warnings).
    projections_dict keys are normalized player names.
    warnings lists rows that were skipped due to missing/bad data.
    """
    projections: dict[str, float] = {}
    warnings_list: list[str] = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Find score column — flexible: accept "projected_score", "score", "projection"
        score_col = None
        name_col = None
        if reader.fieldnames:
            fieldnames_lower = {col.lower(): col for col in reader.fieldnames}
            for candidate in ("projected_score", "score", "projection", "projectedpoints"):
                if candidate in fieldnames_lower:
                    score_col = fieldnames_lower[candidate]
                    break
            for candidate in ("player", "name", "golfer"):
                if candidate in fieldnames_lower:
                    name_col = fieldnames_lower[candidate]
                    break

        if not score_col or not name_col:
            raise ValueError(
                "Projections CSV must have a player name column (player/name/golfer) "
                "and a score column (projected_score/score/projection/projectedpoints)"
            )

        for i, row in enumerate(reader, start=2):  # start=2: row 1 is headers
            raw_name = row.get(name_col, "").strip()
            raw_score = row.get(score_col, "").strip()
            if not raw_name:
                warnings_list.append(f"Row {i}: empty player name, skipped")
                continue
            if not raw_score:
                warnings_list.append(f"Row {i}: no score for {raw_name!r}, skipped")
                continue
            try:
                score = float(raw_score)
            except ValueError:
                warnings_list.append(
                    f"Row {i}: non-numeric score {raw_score!r} for {raw_name!r}, skipped"
                )
                continue
            projections[normalize_name(raw_name)] = score

    return projections, warnings_list
