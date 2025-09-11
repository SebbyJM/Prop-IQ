# 01_pull_prizepicks_nfl.py
import json
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

API_URL = "https://api.prizepicks.com/projections?per_page=2500&state_code=IL"
APP_URL = "https://app.prizepicks.com/"
PROFILE_DIR = Path(".pp_profile")  # persistent storage for cookies/localStorage

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
    n = n.replace("YDS", "YARDS")
    n = n.replace("REC", "RECEPTIONS")
    n = n.replace("PASS YARDS", "PASSING YARDS")
    n = n.replace("RUSH YARDS", "RUSHING YARDS")
    n = n.replace("PASS ATT", "PASS ATTEMPTS").replace("ATT", "ATTEMPTS")
    return n

def parse_json_to_rows(result: dict):
    # Build maps
    player_info = {}
    leagues = {}

    for inc in result.get("included", []):
        t = inc.get("type", "")
        if t in ("players", "new_players", "new_player"):
            pid = inc.get("id")
            attrs = inc.get("attributes", {})
            name = attrs.get("name") or attrs.get("display_name") or attrs.get("full_name") or "UNKNOWN"
            team = attrs.get("team", "N/A")
            player_info[pid] = {"name": name, "team": team}
        elif "league" in t:
            leagues[inc.get("id")] = inc.get("attributes", {}).get("name")

    rows = []
    for prop in result.get("data", []):
        attrs = prop.get("attributes", {})
        rel   = prop.get("relationships", {})

        # only NFL
        league_id = rel.get("league", {}).get("data", {}).get("id")
        league_name = leagues.get(league_id, "")
        if league_name != "NFL":
            continue

        rel_data = rel.get("new_player") or rel.get("player")
        if not rel_data:
            continue
        player_id = rel_data.get("data", {}).get("id")
        pinfo = player_info.get(player_id, {})

        rows.append(
            {
                "player": pinfo.get("name", "UNKNOWN"),
                "team": pinfo.get("team", "N/A"),
                "prop": attrs.get("stat_type", "UNKNOWN"),
                "pp_line": attrs.get("line_score", "N/A"),
                "projection_id": prop.get("id"),
                "kickoff": attrs.get("start_time"),
                "player_clean": clean_player(pinfo.get("name", "UNKNOWN")),
                "prop_clean": clean_prop(attrs.get("stat_type", "UNKNOWN")),
            }
        )
    return rows

def save_rows(rows):
    df = pd.DataFrame(rows)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%SUTC")
    out = f"pp_nfl_board_{stamp}.csv"
    df.to_csv(out, index=False)
    print(f"✅ Saved {len(df)} NFL lines to {out}")

def main():
    PROFILE_DIR.mkdir(exist_ok=True)
    rows = []

    with sync_playwright() as p:
        # persistent profile helps PerimeterX tokens survive between runs
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,  # set True once it’s stable for you
            viewport={"width": 1280, "height": 900},
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )

        page = browser.new_page()

        # Make navigator.webdriver = undefined (simple stealth)
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        # 1) Visit the app first so PX cookies get set
        try:
            page.goto(APP_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)
            # Scroll a bit to trigger app requests
            for _ in range(5):
                page.mouse.wheel(0, 1500)
                page.wait_for_timeout(400)
        except PWTimeout:
            print("⚠️ App page load took too long, continuing...")

        # 2) Try to hit the API directly in SAME CONTEXT (cookies should carry)
        try:
            api_page = browser.new_page()
            resp = api_page.goto(API_URL, wait_until="domcontentloaded", timeout=60000)
            status = resp.status if resp else None
            if resp and 200 <= status < 300:
                text = api_page.content()
                # content() returns HTML wrapper if any; prefer response body:
                try:
                    text = resp.text()
                except Exception:
                    pass
                try:
                    data = json.loads(text)
                    rows = parse_json_to_rows(data)
                except json.JSONDecodeError:
                    # Sometimes the API may render JSON as plain text without proper MIME; try extracting from <pre>
                    try:
                        pre = api_page.locator("pre").first
                        text2 = pre.inner_text(timeout=3000)
                        data = json.loads(text2)
                        rows = parse_json_to_rows(data)
                    except Exception:
                        pass
            else:
                print(f"⚠️ API direct status: {status}")
        except PWTimeout:
            print("⚠️ API direct request timed out")

        # 3) Fallback: listen on the app tab for a /projections response
        if not rows:
            try:
                with page.expect_response(
                    lambda r: ("projections" in r.url) and (200 <= r.status < 300),
                    timeout=90000,
                ) as resp_wait:
                    # Trigger another small interaction to prompt more requests
                    page.reload(wait_until="domcontentloaded")
                    page.wait_for_timeout(4000)
                resp = resp_wait.value
                try:
                    data = resp.json()
                except Exception:
                    data = json.loads(resp.text())
                rows = parse_json_to_rows(data)
            except PWTimeout:
                print("⚠️ Did not capture /projections on the app page")

        # Done
        try:
            browser.close()
        except Exception:
            pass

    if rows:
        save_rows(rows)
    else:
        print("❌ No data captured. (PX may still be blocking — try running once with headless=False and keep the window focused for ~10s.)")

if __name__ == "__main__":
    main()