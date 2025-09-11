import requests
import pandas as pd

POSITIONS = {
    "QB": "https://www.fantasypros.com/nfl/projections/qb.php?week={week}",
    "RB": "https://www.fantasypros.com/nfl/projections/rb.php?week={week}",
    "WR": "https://www.fantasypros.com/nfl/projections/wr.php?week={week}",
    "TE": "https://www.fantasypros.com/nfl/projections/te.php?week={week}",
    "K":  "https://www.fantasypros.com/nfl/projections/k.php?week={week}",
    "DST":"https://www.fantasypros.com/nfl/projections/dst.php?week={week}",
}

def scrape_fantasypros(week: int = 1):
    all_dfs = []

    for pos, url in POSITIONS.items():
        full_url = url.format(week=week)
        print(f"📄 Scraping {pos} projections (Week {week})...")

        resp = requests.get(full_url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()

        # Parse all tables
        tables = pd.read_html(resp.text, header=[0,1])  # Multi-index headers
        if not tables:
            print(f"⚠️ No table found for {pos}")
            continue

        df = tables[0]

        # Flatten multi-level headers into single strings
        df.columns = [
            " ".join(col).strip() if isinstance(col, tuple) else str(col)
            for col in df.columns
        ]

        # Insert position column
        df["POS"] = pos

        all_dfs.append(df)

    # Combine
    final_df = pd.concat(all_dfs, ignore_index=True)

    # Clean column names: remove Unnamed & extra spaces
    final_df.columns = [
        col.replace("Unnamed: 0_level_0 ", "").replace("Unnamed: 1_level_0 ", "").strip()
        for col in final_df.columns
    ]

    return final_df


def main():
    week = 1
    df = scrape_fantasypros(week)

    # Save cleaned output
    output_file = f"fantasypros_week{week}_projections_clean.csv"
    df.to_csv(output_file, index=False)
    print(f"✅ Saved {output_file} with {len(df)} rows and {len(df.columns)} columns")


if __name__ == "__main__":
    main()