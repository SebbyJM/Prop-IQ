import pandas as pd
import glob
import os
import numpy as np

# ---------- Helpers ----------
def clean_player(name: str) -> str:
    return (
        str(name).upper()
        .replace(".", "")
        .replace("-", " ")
        .replace("'", "")
        .replace(",", "")
        .strip()
    )

def clean_prop(name: str) -> str:
    n = str(name).upper().strip()
    mapping = {
        # Passing
        "PASS YARDS": "PASSING YARDS",
        "PASSING YARDS": "PASSING YARDS",
        "PLAYER_PASS_YDS": "PASSING YARDS",
        "PASS ATTEMPTS": "PASS ATTEMPTS",
        "PLAYER_PASS_ATTEMPTS": "PASS ATTEMPTS",
        "PLAYER_PASS_ATT": "PASS ATTEMPTS",
        "PASS COMPLETIONS": "PASS COMPLETIONS",
        "PLAYER_PASS_COMPLETIONS": "PASS COMPLETIONS",
        "PLAYER_PASS_COMP": "PASS COMPLETIONS",
        # Rushing
        "RUSH YARDS": "RUSHING YARDS",
        "RUSHING YARDS": "RUSHING YARDS",
        "PLAYER_RUSH_YDS": "RUSHING YARDS",
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

def summarize_line(group: pd.DataFrame) -> pd.Series:
    """Pick the most favored (most negative) Over/Under odds for this (player, prop, line)."""
    over = group[group["Label"].str.upper() == "OVER"]
    under = group[group["Label"].str.upper() == "UNDER"]

    # Most favored means most negative (min) American odds
    over_best = np.nan
    under_best = np.nan
    if not over.empty:
        over_best = over["Odds"].min()
    if not under.empty:
        under_best = under["Odds"].min()

    # Determine which side is favored at this line
    # (more negative number = more favored)
    over_favored = False
    under_favored = False
    if not np.isnan(over_best) and not np.isnan(under_best):
        if over_best < under_best:
            over_favored = True
        elif under_best < over_best:
            under_favored = True

    return pd.Series({
        "Over_Odds": over_best if not np.isnan(over_best) else None,
        "Under_Odds": under_best if not np.isnan(under_best) else None,
        "Over_Favored": over_favored,
        "Under_Favored": under_favored
    })

# ---------- Main ----------
def main(pp_csv, odds_folder, out_csv="nfl_regular.csv"):
    # Load PrizePicks board
    pp = pd.read_csv(pp_csv)
    pp["player_clean"] = pp["player"].apply(clean_player)
    pp["prop_clean"]  = pp["prop"].apply(clean_prop)
    pp["pp_line"]     = pd.to_numeric(pp["pp_line"], errors="coerce")

    valid_props = {
        "PASSING YARDS", "PASS ATTEMPTS", "PASS COMPLETIONS",
        "RUSHING YARDS", "RUSH ATTEMPTS",
        "RECEIVING YARDS", "RECEPTIONS",
        "RECEIVING + RUSH YARDS",
        "KICKING POINTS", "FIELD GOALS",
    }
    pp = pp[pp["prop_clean"].isin(valid_props)].dropna(subset=["pp_line"]).copy()

    # Load sportsbook odds
    all_odds = []
    for file in glob.glob(os.path.join(odds_folder, "NFL - *.csv")):
        df = pd.read_csv(file)
        # Keep only necessary columns
        keep = ["description", "market", "label", "price", "point", "bookmaker"]
        df = df[[c for c in keep if c in df.columns]].copy()

        df.rename(columns={
            "description": "Player",
            "market": "Prop",
            "label": "Label",
            "price": "Odds",
            "point": "Line",
            "bookmaker": "Book",
        }, inplace=True)

        df["player_clean"] = df["Player"].apply(clean_player)
        df["prop_clean"]   = df["Prop"].apply(clean_prop)
        df["Line"]         = pd.to_numeric(df["Line"], errors="coerce")
        df["Odds"]         = pd.to_numeric(df["Odds"], errors="coerce")  # ensure numeric
        all_odds.append(df)

    if not all_odds:
        raise FileNotFoundError("No sportsbook odds files found matching 'NFL - *.csv'")

    odds = pd.concat(all_odds, ignore_index=True)
    odds = odds.dropna(subset=["player_clean", "prop_clean", "Line", "Odds"])

    # Group by player+prop+line and compute most favored Over/Under odds
    odds_grouped = (
        odds.groupby(["player_clean", "prop_clean", "Line"], as_index=False)
            .apply(summarize_line)
            .reset_index(drop=True)
    )

    # Merge PP with sportsbook lines using exact or directional wiggle
    rows = []
    for _, r in pp.iterrows():
        sub = odds_grouped[
            (odds_grouped["player_clean"] == r["player_clean"]) &
            (odds_grouped["prop_clean"]  == r["prop_clean"])
        ]
        if sub.empty:
            continue

        exact = sub[sub["Line"] == r["pp_line"]]

        # Directional wiggle checks
        wiggle_up   = sub[(sub["Line"] == r["pp_line"] + 0.5) & (sub["Over_Favored"]  == True)]
        wiggle_down = sub[(sub["Line"] == r["pp_line"] - 0.5) & (sub["Under_Favored"] == True)]

        use = None
        if not exact.empty:
            use = exact
        elif not wiggle_up.empty:
            use = wiggle_up
        elif not wiggle_down.empty:
            use = wiggle_down
        else:
            # No acceptable match → drop
            continue

        for _, s in use.iterrows():
            rows.append({
                "Player": r["player"],
                "Prop": r["prop_clean"],
                "PrizePicks_Line": r["pp_line"],
                "Over_Odds": s["Over_Odds"],
                "Under_Odds": s["Under_Odds"],
            })

    out = pd.DataFrame(rows)
    out.to_csv(out_csv, index=False)
    print(f"✅ Saved {len(out)} regular matched rows to {out_csv}")

if __name__ == "__main__":
    files = glob.glob("pp_nfl_board_*.csv")
    if not files:
        raise FileNotFoundError("No PrizePicks NFL CSVs found. Run 01_pull_prizepicks_nfl.py first.")
    latest_pp = max(files, key=os.path.getctime)
    print(f"📂 Using latest PrizePicks file: {latest_pp}")
    main(latest_pp, ".")