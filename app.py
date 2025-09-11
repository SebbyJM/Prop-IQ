import streamlit as st
import pandas as pd
from thefuzz import process

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Prop IQ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

PURPLE = "#7A2CF5"

# ---------------- GLOBAL STYLES ----------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;700;800;900&display=swap');

* {{ font-family: 'Poppins', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; }}
.stApp {{ background:#000; color:#fff; }}
.section-title {{
  font-family: 'Poppins', sans-serif;
  font-weight: 800;
  font-size: 24px;
  color: #ffffff;
  letter-spacing: 0.5px;
  margin: 0 0 14px 0;
  padding-bottom: 4px;
  border-bottom: 2px solid #7A2CF5;
  display: inline-block;
}}

section[data-testid="stSidebar"] {{
  background:#000 !important;
  padding: 10px 14px 22px 14px;
  border-right:1px solid #171717;
  box-shadow: inset -1px 0 0 #151515, 0 0 26px rgba(122,44,245,.22);
}}

.sidebar-card {{
  background: linear-gradient(180deg, #0b0b0b 0%, #070707 100%);
  border:1px solid #1f1f1f;
  border-radius:16px;
  padding:12px;
  margin:10px 0 16px;
  box-shadow: 0 1px 0 rgba(255,255,255,.03), 0 10px 28px rgba(122,44,245,.08);
}}

.sidebar-title {{
  font-weight:800;
  font-size:12.5px;
  letter-spacing:.7px;
  text-transform:uppercase;
  color:#d8d8d8;
  margin:2px 0 8px 2px;
  opacity:.95;
}}

section[data-testid="stSidebar"] .stRadio > div {{ gap:10px; }}

section[data-testid="stSidebar"] .stRadio label {{
  background:#0e0e0e;
  border:1px solid #1f1f1f;
  padding:10px 12px;
  border-radius:12px;
  width:100%;
  transition: all .18s ease;
}}

section[data-testid="stSidebar"] .stRadio label:hover {{
  border-color:#2b2b2b;
  box-shadow: 0 0 0 2px rgba(122,44,245,.35), 0 0 18px rgba(122,44,245,.25);
}}

/* NFL sub-option container and radio custom styles */
.nfl-sub-options-container {{
  margin-left: 18px;
  margin-top: -2px;
  margin-bottom: 8px;
  padding: 4px 0 0 4px;
}}
.nfl-sub-options-container .stRadio label {{
  background: #111;
  border: 1px solid #232323;
  padding: 7px 11px;
  border-radius: 10px;
  font-size: 13px;
  color: #cfcfcf;
  margin-bottom: 2px;
  width: 90%;
}}
.nfl-sub-options-container .stRadio label:hover {{
  border-color: #7A2CF5;
}}

hr.prop-divider {{
  border:none; border-top:1px solid #171717; margin:16px 0 8px;
}}

.prop-hero {{ text-align:center; margin: 14px auto 4px; }}
.prop-hero .prop {{ font-weight:900; font-size: clamp(42px, 6.5vw, 96px); color:#fff; letter-spacing:.5px; }}
.prop-hero .iq   {{ font-weight:900; font-size: clamp(42px, 6.5vw, 96px); color:{PURPLE}; margin-left:10px; }}
.prop-tagline {{ text-align:center; font-weight:700; font-size: clamp(14px, 2.1vw, 22px); color:#e8e8e8; margin-top:-2px; }}

.main-card {{
  background: linear-gradient(180deg, #0b0b0b, #070707);
  border:1px solid #1f1f1f; border-radius:18px; padding:18px; 
  box-shadow: 0 1px 0 rgba(255,255,255,.03), 0 10px 28px rgba(0,0,0,.35);
}}

.stDataFrame {{
  border: none !important;
  border-radius: 8px;
  box-shadow: 0 0 20px {PURPLE};
  background: #0e0e0e !important;
}}

.prop-bubble {{
  background: linear-gradient(180deg, #0b0b0b, #121212);
  border-radius:16px;
  padding:20px 24px;
  margin:12px 0 20px;
  box-shadow: 0 0 16px {PURPLE};
  color: #ddd;
  font-weight: 400;
  font-size: 1rem;
  line-height: 1.5;
  border: 1px solid #1f1f1f;
  transition: box-shadow 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 12px;
}}

.prop-bubble strong {{
  color: {PURPLE};
  font-weight: 700;
  font-size: 1.2rem;
  display: block;
  margin-bottom: 4px;
}}

.prop-details {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px 24px;
  font-size: 0.9rem;
  color: #ccc;
  font-weight: 400;
}}

.prop-details div {{
  display: flex;
  flex-direction: column;
  gap: 4px;
}}

.prop-details div span.label {{
  font-size: 0.8rem;
  color: #888;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}}

.prop-bubble .badge-recommended {{
  align-self: flex-start;
  background: #444444;
  color: #ddd;
  font-weight: 700;
  font-size: 0.85rem;
  padding: 6px 14px;
  border-radius: 14px;
  box-shadow: 0 0 8px rgba(122,44,245,0.45);
  user-select: none;
  transition: background-color 0.3s ease;
}}

.prop-bubble:hover {{
  box-shadow: 0 0 24px {PURPLE}, 0 0 36px {PURPLE};
}}

.edge-meter {{
  background: linear-gradient(90deg, #2a2a2a, #1a1a1a);
  border-radius: 20px;
  height: 20px;
  margin-top: 10px;
  overflow: hidden;
  position: relative;
  box-shadow: inset 0 0 8px rgba(122,44,245,0.3);
}}

.edge-meter-fill {{
  height: 100%;
  background: linear-gradient(90deg, #7A2CF5, #b388ff);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 0.95rem;
  text-shadow: 0 0 6px rgba(122,44,245,0.8);
  transition: width 0.4s ease;
  white-space: nowrap;
  padding: 0 8px;
  box-sizing: border-box;
}}

.edge-meter-text {{
  position: absolute;
  width: 100%;
  top: 0;
  left: 0;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  font-weight: 700;
  color: #bbb;
  pointer-events: none;
  user-select: none;
  letter-spacing: 0.02em;
}}

@media (max-width: 768px) {{
  .prop-bubble, .main-card {{
    width: 100% !important;
    box-sizing: border-box;
  }}
  .prop-bubble {{
    padding: 16px 18px;
    font-size: 0.95rem;
  }}
  .main-card {{
    padding: 12px;
  }}
  .prop-details {{
    grid-template-columns: 1fr 1fr;
    gap: 10px 16px;
  }}
}}
</style>
""", unsafe_allow_html=True)

# ---------------- TOP BRAND (text logo) ----------------
st.markdown("""
<div class="prop-hero">
  <span class="prop">PROP</span><span class="iq"> IQ</span>
</div>
<div class="prop-tagline">Advance your bets &amp; knowledge.</div>
<hr class="prop-divider" />
""", unsafe_allow_html=True)

# ---------------- ONE ACTIVE PAGE STATE ----------------
if "active_page" not in st.session_state:
    st.session_state.active_page = "NFL"  # default landing

def set_active_page():
    st.session_state.active_page = st.session_state.active_page_choice

SPORTS = ["NFL", "Sports News"]
# Expanded navigation: all in one radio
# Remove "Open AI Chat" from navigation
ALL_PAGES_BASE = ["Sports News", "NFL"]

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">📊 NAVIGATION</div>', unsafe_allow_html=True)
    # Unified navigation: Sports News, NFL
    ALL_PAGES = ALL_PAGES_BASE.copy()
    nav_index = ALL_PAGES.index(st.session_state.active_page) if st.session_state.active_page in ALL_PAGES else 0
    selected_page = st.radio(
        "Navigation",
        ["Sports News", "NFL"],
        key="active_page_choice",
        index=nav_index if nav_index < 2 else 0,
        on_change=set_active_page,
        label_visibility="collapsed",
        horizontal=False,
    )
    # NFL sub-options: render indented and styled under NFL if NFL is selected
    if selected_page == "NFL":
        st.markdown('<div class="nfl-sub-options-container">', unsafe_allow_html=True)
        nfl_sub_option = st.radio(
            "",
            ["Player Search", "Value Props"],
            index=0,
            key="_nfl_sub_option",
            horizontal=False,
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

page = st.session_state.active_page

def header(title: str):
    st.markdown(f"<div class='main-card'><h2 style='margin:0; font-weight:800;'>{title}</h2></div>", unsafe_allow_html=True)

# --- Navigation / state guards ---
if "last_page" not in st.session_state:
    st.session_state["last_page"] = page
if page != st.session_state["last_page"]:
    # Clear player selection when switching pages
    st.session_state.pop("nfl_player_dropdown", None)
    st.session_state["last_page"] = page

# Reset player dropdown when switching NFL sub-option (e.g., Value Props ↔ Player Search)
curr_sub = st.session_state.get("_nfl_sub_option")
prev_sub = st.session_state.get("_nfl_sub_option_prev")
if curr_sub != prev_sub:
    st.session_state.pop("nfl_player_dropdown", None)
    st.session_state["_nfl_sub_option_prev"] = curr_sub

if page == "Sports News":
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=5 * 60 * 1000, key="sports_news_autorefresh")
    st.markdown("<div class='section-title'>Latest NFL News</div>", unsafe_allow_html=True)

    import feedparser
    from datetime import datetime

    # ---- Bubble Card Style for News ----
    st.markdown(f"""
    <style>
    .news-bubble {{
        background: linear-gradient(180deg, #1a1125, #181822 100%);
        border-radius: 18px;
        box-shadow: 0 0 16px {PURPLE}, 0 2px 32px #1a1a1a;
        border: 1px solid #2e1757;
        padding: 18px 20px;
        margin: 18px 0 22px 0;
        display: flex;
        flex-direction: row;
        align-items: flex-start;
        gap: 16px;
        transition: box-shadow 0.32s cubic-bezier(.4,0,.2,1), background 0.22s;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }}
    .news-bubble:hover {{
        box-shadow: 0 0 32px {PURPLE}, 0 0 48px {PURPLE}, 0 2px 46px #1a1a1a;
        background: linear-gradient(180deg, #2d1a54, #2e1757 100%);
    }}
    .news-thumb {{
        width: 62px;
        height: 62px;
        border-radius: 12px;
        object-fit: cover;
        margin-right: 8px;
        background: #232232;
        box-shadow: 0 0 8px #7A2CF540;
        flex-shrink: 0;
        border: 1.5px solid #3f226f;
    }}
    .news-content {{
        flex: 1 1 0%;
        display: flex;
        flex-direction: column;
        gap: 6px;
        min-width: 0;
    }}
    .news-title {{
        font-size: 1.19rem;
        font-weight: 900;
        color: #fff;
        margin-bottom: 1px;
        line-height: 1.22;
        letter-spacing: .01em;
        transition: color 0.18s;
        text-decoration: none;
        word-break: break-word;
        display: block;
    }}
    .news-bubble:hover .news-title {{
        color: {PURPLE};
    }}
    .news-date {{
        font-size: 0.97rem;
        color: #c6bafd;
        font-weight: 600;
        margin-bottom: 2px;
        opacity: .92;
        letter-spacing: .01em;
    }}
    .news-summary {{
        font-size: 1.01rem;
        color: #c3c3c3;
        opacity: .85;
        margin-top: 2px;
        font-weight: 400;
        line-height: 1.41;
        word-break: break-word;
    }}
    @media (max-width: 700px) {{
        .news-bubble {{
            flex-direction: column;
            gap: 10px;
            padding: 14px 10px;
        }}
        .news-thumb {{
            margin: 0 0 8px 0;
            width: 52px;
            height: 52px;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

    def get_rss_items(feed_url, limit=5):
        d = feedparser.parse(feed_url)
        items = []
        for entry in d.entries[:limit]:
            title = entry.title
            link = entry.link
            published = getattr(entry, 'published', '')
            summary = getattr(entry, 'summary', '') or title
            # Remove " +0000" timezone suffix if present
            published = published.replace(" +0000", "")
            # Try to find image (media_content, media_thumbnail, or enclosure)
            img_url = None
            if hasattr(entry, "media_content"):
                # media_content is a list of dicts
                try:
                    img_url = entry.media_content[0].get('url')
                except Exception:
                    pass
            if not img_url and hasattr(entry, "media_thumbnail"):
                try:
                    img_url = entry.media_thumbnail[0].get('url')
                except Exception:
                    pass
            if not img_url and hasattr(entry, "enclosures"):
                try:
                    img_url = entry.enclosures[0].get('href')
                except Exception:
                    pass
            items.append({
                'title': title,
                'link': link,
                'published': published,
                'summary': summary,
                'img_url': img_url
            })
        return items

    def format_rss_date(dt_str):
        # Example: 'Thu, 11 Sep 2025 17:24:00'
        # Want: "Sep 11, 2025 – 5:24 PM"
        try:
            dt = datetime.strptime(dt_str, "%a, %d %b %Y %H:%M:%S")
        except Exception:
            try:
                dt = datetime.strptime(dt_str, "%a, %d %b %Y %H:%M")
            except Exception:
                try:
                    dt = datetime.strptime(dt_str, "%d %b %Y %H:%M:%S")
                except Exception:
                    return dt_str
        return dt.strftime("%b %-d, %Y – %-I:%M %p") if hasattr(dt, "strftime") else dt_str

    # Only use the News feed (remove Injuries)
    news_feed_url = "https://www.cbssports.com/rss/headlines/nfl/"
    try:
        rss_items = get_rss_items(news_feed_url, limit=8)
        for item in rss_items:
            # Format date
            date_str = format_rss_date(item['published'])
            # Sanitize summary (truncate if too long)
            summary = item['summary']
            if summary and len(summary) > 320:
                summary = summary[:310] + "..."
            # Build thumbnail HTML if image exists
            thumb_html = ""
            if item.get("img_url"):
                thumb_html = f'<img src="{item["img_url"]}" class="news-thumb" alt="news image" />'
            # Render clickable bubble card
            st.markdown(
                f"""
                <a href="{item['link']}" target="_blank" style="text-decoration:none;">
                <div class="news-bubble">
                    {thumb_html}
                    <div class="news-content">
                        <span class="news-title">{item['title']}</span>
                        <span class="news-date">{date_str}</span>
                        <span class="news-summary">{summary}</span>
                    </div>
                </div>
                </a>
                """,
                unsafe_allow_html=True
            )
    except Exception:
        st.error("Couldn't fetch News feed right now.")

# ---------------- NFL PROJECTIONS + ODDS ----------------
def load_nfl_file():
    for fname in ["nfl_regular_with_proj.csv", "nfl_regular_sample_with_proj.csv", "nfl_regular.csv"]:
        try:
            return pd.read_csv(fname)
        except FileNotFoundError:
            continue
    return pd.DataFrame()

def format_odds(odds):
    try:
        odds_val = float(odds)
        odds_int = int(round(odds_val))
        odds_str = str(odds_int)
        if odds_int > 0:
            odds_str = '+' + odds_str
        return odds_str
    except:
        return odds

def determine_recommended(over_odds, under_odds, proj, line):
    try:
        over_odds_val = float(over_odds)
        under_odds_val = float(under_odds)
        # Prioritize odds: more negative is better
        if over_odds_val < under_odds_val:
            recommended = "Over"
        elif under_odds_val < over_odds_val:
            recommended = "Under"
        else:
            # If tied, use projection vs line
            if proj > line:
                recommended = "Over"
            elif proj < line:
                recommended = "Under"
            else:
                recommended = ""
        return recommended
    except:
        return ""

if page == "NFL":
    df = load_nfl_file()
    if df.empty:
        st.info("No merged NFL file found (expected nfl_regular_with_proj.csv).")
    else:
        nfl_sub_option = st.session_state.get("_nfl_sub_option", "Player Search")
        if nfl_sub_option == "Player Search":
            # ---- Search-only player view (PrizePicks odds only) ----
            st.markdown("<div class='section-title'>Player Search Results</div>", unsafe_allow_html=True)
            # Only include players that have PrizePicks odds today
            active_df = df.dropna(subset=["PrizePicks_Line", "Over_Odds", "Under_Odds"])
            players = sorted(active_df["Player"].dropna().unique())

            # --- Player search input ---
            search_str = st.text_input(
                "Search by player",
                value="",
                key="nfl_player_search",
                label_visibility="collapsed",
                placeholder="Type a player name..."
            )

            selected_player = None
            filtered_players = []
            # Only filter if there is input
            if search_str.strip():
                # Use fuzzy matching to get top 5 matches
                matches = process.extract(search_str, players, limit=5)
                filtered_players = [m[0] for m in matches if m[1] > 60]  # threshold to avoid bad matches
                # If exact match (case-insensitive), select that player
                for p in players:
                    if search_str.strip().lower() == p.lower():
                        selected_player = p
                        break
                # If not exact match and one fuzzy match, select that player
                if not selected_player and len(filtered_players) == 1:
                    selected_player = filtered_players[0]
                # If not exact match and multiple fuzzy matches, show as clickable links
                elif not selected_player and len(filtered_players) > 1:
                    st.markdown("<div style='margin:10px 0 16px 0; font-size:1.06rem;'>Multiple matches found:</div>", unsafe_allow_html=True)
                    for fp in filtered_players:
                        # Create a link that sets the search box value to this player (simulate selection)
                        st.markdown(
                            f"<a href='#{fp}' style='color:#b388ff; font-weight:700; text-decoration:none;' "
                            f"onclick=\"window.parent.document.querySelector('input[id^=nfl_player_search]').value='{fp}';window.parent.document.querySelector('input[id^=nfl_player_search]').dispatchEvent(new Event('input', {{bubbles:true}}));return false;\">{fp}</a>",
                            unsafe_allow_html=True
                        )
                elif not selected_player and len(filtered_players) == 0:
                    st.info("No players found matching your search.")
            # If no input, do not show any player list by default

            # Only show props if a player is selected (not blank)
            if selected_player:
                pdata = df[df["Player"] == selected_player][
                    ["Prop", "PrizePicks_Line", "Over_Odds", "Under_Odds", "Projection"]
                ].reset_index(drop=True)

                # Convert Prop column from ALL CAPS to title case
                pdata["Prop"] = pdata["Prop"].str.title()

                pdata = pdata.rename(columns={
                    "Prop": "Prop",
                    "PrizePicks_Line": "PP Line",
                    "Over_Odds": "Over",
                    "Under_Odds": "Under",
                    "Projection": "Proj"
                })

                # Render each row as a prop bubble card (like Value Props)
                for _, row in pdata.iterrows():
                    over_odds_fmt = format_odds(row['Over'])
                    under_odds_fmt = format_odds(row['Under'])
                    pp_line_fmt = f"{row['PP Line']:.1f}" if isinstance(row['PP Line'], (float, int)) else str(row['PP Line'])
                    proj_fmt = f"{row['Proj']:.1f}" if isinstance(row['Proj'], (float, int)) else str(row['Proj'])

                    recommended = determine_recommended(row['Over'], row['Under'], row['Proj'], row['PP Line'])
                    badge_text = f"Recommended {recommended}" if recommended else ""

                    edge_val = abs(float(row['Proj']) - float(row['PP Line'])) if (
                        isinstance(row['Proj'], (float, int)) and isinstance(row['PP Line'], (float, int))
                    ) else 0
                    edge_pct = min(100, max(0, (edge_val / 10) * 100))

                    st.markdown(f"""
                    <div class="prop-bubble">
                      <strong>{row['Prop']}</strong>
                      <div class="prop-details">
                        <div><span class="label">PP Line</span><span>{pp_line_fmt}</span></div>
                        <div><span class="label">Projection</span><span>{proj_fmt}</span></div>
                        <div><span class="label">Odds</span><span>Over {over_odds_fmt} / Under {under_odds_fmt}</span></div>
                      </div>
                      <div class="edge-meter">
                        <div class="edge-meter-fill" style="width:{edge_pct}%;"></div>
                        <div class="edge-meter-text">{edge_val:.1f}</div>
                      </div>
                      {f'<div class="badge-recommended">{badge_text}</div>' if badge_text else ''}
                    </div>
                    """, unsafe_allow_html=True)

            # Guidance message below results (always visible)
            st.markdown(
                "<div style='text-align:center; color:#aaa; font-size:13px; margin:18px 0;'>"
                "Want to research your own player? Feel free to search by players and look through all their prop data!"
                "</div>",
                unsafe_allow_html=True,
            )
        elif nfl_sub_option == "Value Props":
            # ---- Top Value Props: Various prop types and thresholds ----
            st.markdown("<div class='main-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>Top Value Props</div>", unsafe_allow_html=True)

            temp = df.copy()
            if not temp.empty:
                # Normalize prop type
                temp["Prop_LC"] = temp["Prop"].str.lower()
                # Apply thresholds by prop type
                def prop_type_and_threshold(row):
                    prop = row["Prop_LC"]
                    line = row["PrizePicks_Line"]
                    if "completion" in prop:
                        return line >= 23
                    elif "pass attempt" in prop:
                        return line >= 30
                    elif "rush attempt" in prop:
                        return line >= 10
                    elif "receiving yards" in prop:
                        return line >= 35
                    elif "receptions" in prop:
                        return line >= 2.5
                    elif "rushing yards" in prop:
                        return line >= 45
                    elif "rush + rec yards" in prop or "rush & rec yards" in prop or "rush and rec yards" in prop:
                        return line >= 65
                    else:
                        return False
                temp = temp[temp.apply(prop_type_and_threshold, axis=1)]
                # Only keep props where Projection > PrizePicks_Line (recommended over)
                temp = temp[temp["Projection"] > temp["PrizePicks_Line"]]
                # Compute edge
                temp["Edge"] = temp["Projection"] - temp["PrizePicks_Line"]
                # Only keep props where the edge is at least +1.0
                temp = temp[temp["Edge"] >= 1.0]
                # Sort by projection edge descending, then by best odds strength (lowest absolute Over_Odds)
                def odds_strength(row):
                    try:
                        return abs(float(row["Over_Odds"]))
                    except:
                        return 9999
                temp["Odds_Strength"] = temp.apply(odds_strength, axis=1)
                temp = temp.sort_values(["Edge", "Odds_Strength"], ascending=[False, True])
                top = temp.head(4)

                if not top.empty:
                    for _, row in top.iterrows():
                        pp_line_fmt = f"{row['PrizePicks_Line']:.1f}" if isinstance(row['PrizePicks_Line'], (float, int)) else str(row['PrizePicks_Line'])
                        proj_fmt = f"{row['Projection']:.1f}" if isinstance(row['Projection'], (float, int)) else str(row['Projection'])
                        over_odds_fmt = format_odds(row['Over_Odds'])
                        under_odds_fmt = format_odds(row['Under_Odds'])
                        edge_val = row['Edge']
                        edge_pct = min(100, max(0, (edge_val / 10) * 100))

                        st.markdown(f"""
                        <div class="prop-bubble">
                          <strong>{row['Player']} - {row['Prop'].title()}</strong>
                          <div class="prop-details">
                            <div><span class="label">PP Line</span><span>{pp_line_fmt}</span></div>
                            <div><span class="label">Projection</span><span>{proj_fmt}</span></div>
                            <div><span class="label">Odds</span><span>Over {over_odds_fmt} / Under {under_odds_fmt}</span></div>
                          </div>
                          <div class="edge-meter">
                            <div class="edge-meter-fill" style="width:{edge_pct}%;"></div>
                            <div class="edge-meter-text">{edge_val:.1f}</div>
                          </div>
                          <div class="badge-recommended">Recommended Over</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No value props found for current thresholds and edges.")
            else:
                st.info("No data available for value props.")

            st.markdown("</div>", unsafe_allow_html=True)
# ---------------- OPEN AI CLIENT (Sidebar Disabled Switch) ----------------
with st.sidebar:
    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">🤖 OPEN AI CLIENT</div>', unsafe_allow_html=True)
    # Disabled toggle (styled HTML)
    st.markdown('''
        <div style="display: flex; align-items: center; gap: 12px; margin-top: 6px;">
          <label style="font-weight: 600; color: #b388ff;">Enable panel</label>
          <input type="checkbox" checked disabled style="accent-color: #7A2CF5; width: 22px; height: 22px; margin-left: 8px; cursor: not-allowed; opacity: 0.7;">
        </div>
        <div style="color:#888; font-size:12px; margin-top:2px; margin-left:2px; opacity:.7;">Coming soon</div>
    ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)