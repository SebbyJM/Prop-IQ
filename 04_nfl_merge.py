import pandas as pd

# Map PrizePicks props to FantasyPros columns
prop_map = {
    "PASSING YARDS": "PASSING YDS",
    "PASS COMPLETIONS": "PASSING CMP",
    "PASS ATTEMPTS": "PASSING ATT",
    "RUSHING YARDS": "RUSHING YDS",
    "RUSH ATTEMPTS": "RUSHING ATT",
    "RECEIVING YARDS": "RECEIVING YDS",
    "RECEPTIONS": "RECEIVING REC"
}

def main():
    # PrizePicks + odds
    pp = pd.read_csv("nfl_regular.csv")
    
    # FantasyPros projections
    proj = pd.read_csv("fantasypros_week1_projections_clean.csv")
    
    # Keep only the relevant projection columns
    keep_cols = ["Player"] + list(prop_map.values())
    proj = proj[[c for c in proj.columns if c in keep_cols]].copy()

    # Clean player names (remove team codes like "PHI", "DAL")
    proj["Player"] = proj["Player"].str.replace(r"\s[A-Z]{2,}$", "", regex=True).str.strip()
    pp["Player"] = pp["Player"].str.strip()

    merged = []
    for _, row in pp.iterrows():
        player = row["Player"]
        prop = row["Prop"]

        # Skip if prop not in our map
        if prop not in prop_map:
            continue

        col = prop_map[prop]
        match = proj[proj["Player"].str.lower() == player.lower()]

        if not match.empty and col in match.columns:
            projection = match.iloc[0][col]
        else:
            projection = None  # no projection available

        merged.append({
            "Player": player,
            "Prop": prop,
            "PrizePicks_Line": row["PrizePicks_Line"],
            "Over_Odds": row["Over_Odds"],
            "Under_Odds": row["Under_Odds"],
            "Projection": projection
        })

    final = pd.DataFrame(merged)
    final.to_csv("nfl_regular_with_proj.csv", index=False)
    print("✅ Saved nfl_regular_with_proj.csv with", len(final), "rows")

if __name__ == "__main__":
    main()