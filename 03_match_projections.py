import pandas as pd
import glob
import os
from typing import Optional

# ----------------- Helpers -----------------
SUPPORTED_PROPS = {
    "PASSING YARDS",
    "PASS ATTEMPTS",
    "PASS COMPLETIONS",
    "RUSHING YARDS",
    "RUSH ATTEMPTS",
    "RECEIVING YARDS",
    "RECEPTIONS",
    "RECEIVING + RUSH YARDS",
    "KICKING POINTS",
    "FIELD GOALS",
}

def clean_player(name: str) -> str:
    s = (
        str(name)
        .upper()
        .replace(".", "")
        .replace("-", " ")
        .replace("'", "")
        .replace(",", " ")
        .strip()
    )
    # collapse multiple spaces
    s = " ".join(s.split())
    return s

def flip_name_if_comma_style(s: str) -> str:
    # "BROWN AJ" <-> "AJ BROWN" helper
    parts = s.split()
    if len(parts) >= 2:
        # Heuristic: if original had comma style, flipping will match some sources
        last_first = " ".join(parts[1:] + [parts[0]])
        return last_first
    return s

def clean_prop(raw: str) -> str:
    n = str(raw).upper().strip()
    mapping = {
        # Passing
        "PASS YARDS": "PASSING YARDS",
        "PASSING YARDS": "PASSING YARDS",
        "PLAYER_PASS_YDS": "PASSING YARDS",
        "PASS ATT": "PASS ATTEMPTS",
        "PASS ATTEMPTS": "PASS ATTEMPTS",
        "PLAYER_PASS_ATTEMPTS": "PASS ATTEMPTS",
        "PLAYER_PASS_ATT": "PASS ATTEMPTS",
        "PASS COMP": "PASS COMPLETIONS",
        "PASS COMPLETIONS": "PASS COMPLETIONS",
        "PLAYER_PASS_COMPLETIONS": "PASS COMPLETIONS",
        "PLAYER_PASS_COMP": "PASS COMPLETIONS",
        # Rushing
        "RUSH YARDS": "RUSHING YARDS",
        "RUSHING YARDS": "RUSHING YARDS",
        "PLAYER_RUSH_YDS": "RUSHING YARDS",
        "RUSH ATT": "RUSH ATTEMPTS",
        "RUSH ATTEMPTS": "RUSH ATTEMPTS",
        "PLAYER_RUSH_ATTEMPTS": "RUSH ATTEMPTS",
        "PLAYER_RUSH_ATT": "RUSH ATTEMPTS",
        # Receiving
        "RECEIVING YARDS": "RECEIVING YARDS",
        "PLAYER_RECEPTION_YDS": "RECEIVING YARDS",
        "PLAYER_RECEIV_YDS": "RECEIVING YARDS",
        "RECEPTIONS": "RECEPTIONS",
        "PLAYER_RECEPTIONS": "RECEPTIONS",
        # Combo
        "RECEIVING + RUSH YARDS": "RECEIVING + RUSH YARDS",
        "PLAYER_RUSH_RECEPTION_YDS": "RECEIVING + RUSH YARDS",
        # Kicking
        "KICKING POINTS": "KICKING POINTS",
        "PLAYER_KICKING_POINTS": "KICKING POINTS",
        "FIELD GOALS": "FIELD GOALS",
        "PLAYER_FIELD_GOALS": "FIELD GOALS",
    }
    return mapping.get(n, n)

def coalesce_columns(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    """Return the first existing column name from the candidates list."""
    for c in candidates:
        if c in df.columns:
            return c
    return None

# ----------------- Main -----------------
def main(
    board_csv: str = "nfl_regular.csv",
    projections_folder: str = "projections",
    out_csv: str = "nfl_regular_with_proj.csv",
):
    # 1) Load the matched regular lines produced by script 02
    if not os.path.exists(board_csv):
        raise FileNotFoundError(
            f"'{board_csv}' not found. Run 02_match_regular_lines.py first."
        )
    board = pd.read_csv(board_csv)

    # Normalize on load
    board["player_clean"] = board["Player"].apply(clean_player)
    board["prop_clean"] = board["Prop"].apply(clean_prop)

    # Limit to our supported set (safety)
    board = board[board["prop_clean"].isin(SUPPORTED_PROPS)].copy()

    # 2) Find latest projections file in /projections
    pattern = os.path.join(projections_folder, "*.csv")
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(
            f"No projection CSVs found in '{projections_folder}'. "
            f"Drop weekly projections there (any *.csv)."
        )
    latest_proj = max(files, key=os.path.getctime)
    print(f"📂 Using projections file: {latest_proj}")

    # 3) Load and normalize projections
    proj = pd.read_csv(latest_proj)

    # Try to detect key columns (player, prop, projection value)
    player_col = coalesce_columns(
        proj, ["player", "Player", "name", "Name", "athlete", "Athlete"]
    )
    prop_col = coalesce_columns(
        proj, ["prop", "Prop", "market", "Market", "stat", "Stat", "category", "Category"]
    )
    value_col = coalesce_columns(
        proj, ["projection", "Projection", "proj", "Proj", "value", "Value", "mean", "Mean"]
    )

    if not player_col or not prop_col or not value_col:
        raise ValueError(
            "Could not auto-detect columns in projections CSV. "
            "Expected to find a player, a prop/market, and a projection value column. "
            "Try renaming columns to: player, prop, projection."
        )

    proj = proj.rename(columns={player_col: "PlayerRaw", prop_col: "PropRaw", value_col: "Projection"})
    proj["player_clean"] = proj["PlayerRaw"].apply(clean_player)
    proj["prop_clean"] = proj["PropRaw"].apply(clean_prop)

    # Keep only supported props (drop everything else)
    proj = proj[proj["prop_clean"].isin(SUPPORTED_PROPS)].copy()

    # 4) Primary exact merge on (player_clean, prop_clean)
    merged = board.merge(
        proj[["player_clean", "prop_clean", "Projection"]],
        on=["player_clean", "prop_clean"],
        how="left",
    )

    # 5) Try a light fallback for unmatched rows: flip "LAST FIRST" ↔ "FIRST LAST"
    unmatched_mask = merged["Projection"].isna()
    if unmatched_mask.any():
        need = merged[unmatched_mask].copy()
        need["player_clean_alt"] = need["player_clean"].apply(flip_name_if_comma_style)

        # Build alt lookup table
        proj_alt = proj.copy()
        proj_alt["player_clean_alt"] = proj_alt["player_clean"].apply(flip_name_if_comma_style)
        alt_join = need.merge(
            proj_alt[["player_clean_alt", "prop_clean", "Projection"]],
            left_on=["player_clean_alt", "prop_clean"],
            right_on=["player_clean_alt", "prop_clean"],
            how="left",
            suffixes=("", "_alt"),
        )

        # Fill where Projection is NA with alt match
        merged.loc[unmatched_mask, "Projection"] = alt_join["Projection"]

    # 6) Final tidy output: only what you asked for
    out = merged[["Player", "prop_clean", "PrizePicks_Line", "Over_Odds", "Under_Odds", "Projection"]].copy()
    out = out.rename(columns={"prop_clean": "Prop"})

    # Drop rows where we still don't have a projection (keep the file clean)
    out = out.dropna(subset=["Projection"]).reset_index(drop=True)

    out.to_csv(out_csv, index=False)
    print(f"✅ Saved {len(out)} rows to {out_csv}")

if __name__ == "__main__":
    # Defaults work out-of-the-box:
    # - reads nfl_regular.csv in current folder
    # - picks newest *.csv from ./projections
    # - writes nfl_regular_with_proj.csv
    main()
