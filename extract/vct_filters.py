"""
Logic for identifying which PandaScore VALORANT series belong to the
franchised VCT international leagues (Americas, EMEA, Pacific, China)
and their true international events (Masters <City> <Year>, Champions)
as opposed to Game Changers, Challengers, Ascension, sub-regional
Challengers leagues (Brazil, Vietnam, etc.), qualifiers, and events that
reuse VCT terminology in their own branding (e.g. Latin America's
"ACE Masters", which is not the real international Masters).

Matching notes:
- "champions" is matched as a whole word (\\bchampions\\b) so it does not
  accidentally match inside "championship" (a Game Changers event name).
- Real international Masters events are always formatted as
  "Masters <City> <Year>" with nothing else in the name, so we require
  the string to START with "masters" followed by a word — this excludes
  "ACE Masters"-branded Challengers events.
- Regional-league series only count if they ALSO contain a real stage
  keyword. The official VCT international-league format runs exactly
  two stages per year (Stage 1, Stage 2) plus Kickoff and Clash events —
  there is no "Stage 3" in the real format, confirmed against Liquipedia's
  official 2025 season structure, so "stage 3" is deliberately excluded
  even though it appears in some PandaScore serie names (e.g.
  "EMEA Stage 3 2025", which does not match the official format and is
  treated as a data anomaly, not a real flagship stage).

Verified against PandaScore's live league_id=4531 series list across two
correction passes on 2026-08-31.
"""
import re

FRANCHISED_LEAGUES = ["americas", "emea", "pacific", "china"]

CHAMPIONS_PATTERN = re.compile(r"\bchampions\b")
MASTERS_PATTERN = re.compile(r"^masters\s+\w+")

EXCLUDE_KEYWORDS = [
    "game changers", "challengers", "ascension", "last chance qualifier",
    "closed qualifier", "open qualifier", "relegation", "promotion",
    "qualifier", "ace masters",
]

VCT_STAGE_KEYWORDS = ["kickoff", "stage 1", "stage 2", "clash"]

VCT_LEAGUE_ID = 4531


def is_flagship_vct_serie(serie_name: str) -> bool:
    """
    Returns True only for franchised VCT international-league series
    (Americas/EMEA/Pacific/China + Kickoff/Stage 1/Stage 2/Clash) or true
    international events (Masters <City> <Year>, Champions).
    """
    name = " ".join(serie_name.lower().split())
    name = name.replace(":", "")

    if any(bad in name for bad in EXCLUDE_KEYWORDS):
        return False

    if CHAMPIONS_PATTERN.search(name):
        return True
    if MASTERS_PATTERN.match(name):
        return True

    has_league = any(lg in name for lg in FRANCHISED_LEAGUES)
    has_stage = any(st in name for st in VCT_STAGE_KEYWORDS)
    return has_league and has_stage