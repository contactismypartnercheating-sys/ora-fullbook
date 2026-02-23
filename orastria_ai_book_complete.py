#!/usr/bin/env python3
"""
Orastria AI-Powered Book Generator v7
- Prokerala API integration for accurate Western tropical chart calculations
- Optimised for 2026 shortened quiz schema
- Graceful fallback for all optional fields
- Rich AI content driven by actual planetary positions
- Visual: Raleway/Garamond fonts, colored compatibility bars, zodiac symbols
"""

import requests
import json
import time
import math
import os
import urllib.request
from datetime import datetime, timedelta

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import textwrap

# ============================================================
# CONFIGURATION
# ============================================================

REPLICATE_URL    = os.environ.get('REPLICATE_MODEL_URL', 'https://api.replicate.com/v1/models/anthropic/claude-3.7-sonnet/predictions')
REPLICATE_API_KEY = os.environ.get('REPLICATE_API_KEY', '')

PROKERALA_CLIENT_ID     = os.environ.get('PROKERALA_CLIENT_ID', '')
PROKERALA_CLIENT_SECRET = os.environ.get('PROKERALA_CLIENT_SECRET', '')

# ============================================================
# FONT MANAGEMENT
# ============================================================

FONT_URLS = {
    'Raleway-Regular.ttf': 'https://cdn.jsdelivr.net/fontsource/fonts/raleway@latest/latin-400-normal.ttf',
    'Raleway-Bold.ttf':    'https://cdn.jsdelivr.net/fontsource/fonts/raleway@latest/latin-700-normal.ttf',
    'Raleway-Italic.ttf':  'https://cdn.jsdelivr.net/fontsource/fonts/raleway@latest/latin-400-italic.ttf',
    'EBGaramond-Regular.ttf': 'https://cdn.jsdelivr.net/fontsource/fonts/eb-garamond@latest/latin-400-normal.ttf',
    'EBGaramond-Bold.ttf':    'https://cdn.jsdelivr.net/fontsource/fonts/eb-garamond@latest/latin-700-normal.ttf',
    'DejaVuSans.ttf':      'https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf/DejaVuSans.ttf',
    'DejaVuSans-Bold.ttf': 'https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf/DejaVuSans-Bold.ttf',
}

def ensure_fonts():
    font_dir = '/app/fonts' if os.path.exists('/app') else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
    os.makedirs(font_dir, exist_ok=True)
    for font_name, url in FONT_URLS.items():
        font_path = os.path.join(font_dir, font_name)
        if not os.path.exists(font_path):
            try:
                print(f"Downloading {font_name}...")
                urllib.request.urlretrieve(url, font_path)
            except Exception as e:
                print(f"Failed to download {font_name}: {e}")
    fonts_registered = {}
    font_mappings = {
        'Raleway':        'Raleway-Regular.ttf',
        'Raleway-Bold':   'Raleway-Bold.ttf',
        'Raleway-Italic': 'Raleway-Italic.ttf',
        'EBGaramond':     'EBGaramond-Regular.ttf',
        'EBGaramond-Bold':'EBGaramond-Bold.ttf',
        'DejaVuSans':     'DejaVuSans.ttf',
        'DejaVuSans-Bold':'DejaVuSans-Bold.ttf',
    }
    for font_name, font_file in font_mappings.items():
        font_path = os.path.join(font_dir, font_file)
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                fonts_registered[font_name] = True
            except Exception as e:
                print(f"Failed to register {font_name}: {e}")
    return fonts_registered

FONTS = ensure_fonts()

FONT_BODY         = 'Raleway'        if 'Raleway'         in FONTS else 'Helvetica'
FONT_BODY_BOLD    = 'Raleway-Bold'   if 'Raleway-Bold'    in FONTS else 'Helvetica-Bold'
FONT_BODY_ITALIC  = 'Raleway-Italic' if 'Raleway-Italic'  in FONTS else 'Helvetica-Oblique'
FONT_HEADING      = 'EBGaramond'     if 'EBGaramond'      in FONTS else 'Times-Roman'
FONT_HEADING_BOLD = 'EBGaramond-Bold' if 'EBGaramond-Bold' in FONTS else 'Times-Bold'
FONT_SYMBOL       = 'DejaVuSans'     if 'DejaVuSans'      in FONTS else 'Helvetica'
FONT_SYMBOL_BOLD  = 'DejaVuSans-Bold' if 'DejaVuSans-Bold' in FONTS else 'Helvetica-Bold'

print(f"Using fonts: Body={FONT_BODY}, Heading={FONT_HEADING}, Symbol={FONT_SYMBOL}")

# ============================================================
# COLORS
# ============================================================

NAVY       = HexColor('#1a1f3c')
GOLD       = HexColor('#c9a961')
CREAM      = HexColor('#f8f5f0')
SOFT_GOLD  = HexColor('#d4b87a')
LIGHT_NAVY = HexColor('#2d3561')

GREEN      = HexColor('#2ecc71')
YELLOW     = HexColor('#f1c40f')
ORANGE     = HexColor('#e67e22')
RED        = HexColor('#e74c3c')
LIGHT_GRAY = HexColor('#ecf0f1')

COLOR_THEMES = {
    'black':         {'primary': HexColor('#1a1a1a'),  'accent': GOLD},
    'green':         {'primary': HexColor('#1a3c2a'),  'accent': HexColor('#c9d961')},
    'dark purple':   {'primary': HexColor('#2a1a3c'),  'accent': HexColor('#c9a9d1')},
    'brighter black':{'primary': HexColor('#2a2a2a'),  'accent': GOLD},
    'red':           {'primary': HexColor('#3c1a1a'),  'accent': HexColor('#d9c961')},
    'creamy':        {'primary': HexColor('#f5f0e6'),  'accent': HexColor('#8b7355')},
    'maroon':        {'primary': HexColor('#722F37'),  'accent': GOLD},
    'navy':          {'primary': NAVY,                 'accent': GOLD},
}

# ============================================================
# ZODIAC DATA
# ============================================================

ZODIAC_SYMBOLS = {
    'Aries': '♈', 'Taurus': '♉', 'Gemini': '♊', 'Cancer': '♋',
    'Leo': '♌',   'Virgo': '♍',  'Libra': '♎',  'Scorpio': '♏',
    'Sagittarius': '♐', 'Capricorn': '♑', 'Aquarius': '♒', 'Pisces': '♓'
}

ZODIAC_ORDER = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

ZODIAC_DATA = {
    "Aries":       {"element": "Fire",  "modality": "Cardinal", "ruler": "Mars",    "crystal": "Carnelian"},
    "Taurus":      {"element": "Earth", "modality": "Fixed",    "ruler": "Venus",   "crystal": "Rose Quartz"},
    "Gemini":      {"element": "Air",   "modality": "Mutable",  "ruler": "Mercury", "crystal": "Citrine"},
    "Cancer":      {"element": "Water", "modality": "Cardinal", "ruler": "Moon",    "crystal": "Moonstone"},
    "Leo":         {"element": "Fire",  "modality": "Fixed",    "ruler": "Sun",     "crystal": "Tiger's Eye"},
    "Virgo":       {"element": "Earth", "modality": "Mutable",  "ruler": "Mercury", "crystal": "Green Aventurine"},
    "Libra":       {"element": "Air",   "modality": "Cardinal", "ruler": "Venus",   "crystal": "Lapis Lazuli"},
    "Scorpio":     {"element": "Water", "modality": "Fixed",    "ruler": "Pluto",   "crystal": "Black Obsidian"},
    "Sagittarius": {"element": "Fire",  "modality": "Mutable",  "ruler": "Jupiter", "crystal": "Turquoise"},
    "Capricorn":   {"element": "Earth", "modality": "Cardinal", "ruler": "Saturn",  "crystal": "Garnet"},
    "Aquarius":    {"element": "Air",   "modality": "Fixed",    "ruler": "Uranus",  "crystal": "Amethyst"},
    "Pisces":      {"element": "Water", "modality": "Mutable",  "ruler": "Neptune", "crystal": "Aquamarine"},
}

ZODIAC_SIGNS = list(ZODIAC_DATA.keys())

# ============================================================
# PROKERALA API
# ============================================================

# Lahiri ayanamsa (current accurate value for 2025-2026)
AYANAMSA = 24.13


def get_prokerala_token():
    """Obtain OAuth2 token from Prokerala."""
    cid = PROKERALA_CLIENT_ID.strip()
    csec = PROKERALA_CLIENT_SECRET.strip()
    print(f"🔑 Prokerala auth: id={cid[:8]}… len={len(cid)}")

    resp = requests.post(
        "https://api.prokerala.com/token",
        data={
            'grant_type':    'client_credentials',
            'client_id':     cid,
            'client_secret': csec,
        },
        timeout=30
    )
    if resp.status_code != 200:
        print(f"❌ Prokerala token error {resp.status_code}: {resp.text[:300]}")
    resp.raise_for_status()
    return resp.json()['access_token']


def get_timezone_from_coords(lat, lon, place_name):
    """Determine IANA timezone from coordinates."""
    try:
        from timezonefinder import TimezoneFinder
        tz = TimezoneFinder().timezone_at(lat=lat, lng=lon)
        if tz:
            print(f"✅ Timezone: {tz}")
            return tz
    except ImportError:
        print("⚠️ timezonefinder not installed, using fallback")
    except Exception as e:
        print(f"⚠️ timezonefinder error: {e}")
    return _guess_timezone(lat, lon, place_name)


def geocode_location(place_name):
    """Geocode a place name via Nominatim. Returns (lat, lon, timezone)."""
    resp = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={'q': place_name, 'format': 'json', 'limit': 1},
        headers={'User-Agent': 'OrastriaApp/2.0'},
        timeout=30
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise ValueError(f"Could not geocode: {place_name}")
    lat = float(results[0]['lat'])
    lon = float(results[0]['lon'])
    tz  = get_timezone_from_coords(lat, lon, place_name)
    print(f"📍 {place_name} → {lat:.4f}, {lon:.4f}, tz={tz}")
    return lat, lon, tz


def _guess_timezone(lat, lon, place_name):
    """Longitude-based timezone guess when timezonefinder is unavailable."""
    p = place_name.lower()
    mapping = [
        (['paris', 'france'],                       'Europe/Paris'),
        (['london', 'uk', 'england', 'britain'],    'Europe/London'),
        (['new york'],                              'America/New_York'),
        (['los angeles', 'california'],             'America/Los_Angeles'),
        (['chicago'],                               'America/Chicago'),
        (['dubai', 'uae', 'abu dhabi'],             'Asia/Dubai'),
        (['tokyo', 'japan'],                        'Asia/Tokyo'),
        (['sydney', 'australia'],                   'Australia/Sydney'),
        (['berlin', 'germany'],                     'Europe/Berlin'),
        (['rome', 'italy'],                         'Europe/Rome'),
        (['madrid', 'spain'],                       'Europe/Madrid'),
        (['moscow', 'russia'],                      'Europe/Moscow'),
        (['beijing', 'shanghai', 'china'],          'Asia/Shanghai'),
        (['india', 'mumbai', 'delhi', 'bangalore'], 'Asia/Kolkata'),
        (['beirut', 'lebanon'],                     'Asia/Beirut'),
        (['cairo', 'egypt'],                        'Africa/Cairo'),
        (['istanbul', 'turkey'],                    'Europe/Istanbul'),
        (['riyadh', 'saudi'],                       'Asia/Riyadh'),
        (['singapore'],                             'Asia/Singapore'),
    ]
    for keywords, tz in mapping:
        if any(k in p for k in keywords):
            return tz
    # Longitude-based fallback
    if lon < -100: return 'America/Los_Angeles'
    if lon < -60:  return 'America/New_York'
    if lon < 0:    return 'Europe/London'
    if lon < 30:   return 'Europe/Paris'
    if lon < 60:   return 'Asia/Dubai'
    if lon < 100:  return 'Asia/Kolkata'
    if lon < 130:  return 'Asia/Shanghai'
    return 'Asia/Tokyo'


_TZ_OFFSETS = {
    'America/Los_Angeles': '-08:00', 'America/Denver': '-07:00',
    'America/Chicago': '-06:00',     'America/New_York': '-05:00',
    'America/Sao_Paulo': '-03:00',   'Europe/London': '+00:00',
    'Europe/Paris': '+01:00',        'Europe/Berlin': '+01:00',
    'Europe/Rome': '+01:00',         'Europe/Madrid': '+01:00',
    'Europe/Istanbul': '+03:00',     'Europe/Moscow': '+03:00',
    'Africa/Cairo': '+02:00',        'Asia/Beirut': '+02:00',
    'Asia/Riyadh': '+03:00',         'Asia/Dubai': '+04:00',
    'Asia/Kolkata': '+05:30',        'Asia/Singapore': '+08:00',
    'Asia/Shanghai': '+08:00',       'Asia/Tokyo': '+09:00',
    'Australia/Sydney': '+11:00',    'Pacific/Auckland': '+13:00',
    'UTC': '+00:00',
}

def get_tz_offset(timezone):
    return _TZ_OFFSETS.get(timezone, '+00:00')


def longitude_to_tropical_sign(longitude):
    """Convert ecliptic longitude (sidereal, from Prokerala) to Western tropical sign."""
    tropical = (longitude + AYANAMSA) % 360
    return ZODIAC_SIGNS[int(tropical / 30)]


def get_birth_chart(birth_date, birth_time, latitude, longitude, timezone):
    """Call Prokerala planet-position and kundli APIs."""
    token  = get_prokerala_token()
    dt_str = f"{birth_date}T{birth_time}:00{get_tz_offset(timezone)}"
    headers = {"Authorization": f"Bearer {token}"}
    params  = {
        "ayanamsa":   1,
        "coordinates": f"{latitude},{longitude}",
        "datetime":   dt_str,
    }

    planet_resp = requests.get(
        "https://api.prokerala.com/v2/astrology/planet-position",
        headers=headers, params=params, timeout=30
    )
    planet_resp.raise_for_status()
    planet_data = planet_resp.json()['data']

    kundli_data = None
    try:
        kundli_resp = requests.get(
            "https://api.prokerala.com/v2/astrology/kundli",
            headers=headers, params=params, timeout=30
        )
        if kundli_resp.ok:
            kundli_data = kundli_resp.json()['data']
    except Exception as e:
        print(f"⚠️ Kundli API error (non-fatal): {e}")

    return parse_chart_data(planet_data, kundli_data)


def parse_chart_data(planet_data, kundli_data):
    """
    Parse Prokerala response into our chart dict.
    Defaults to 'Unknown' — never silently falls back to 'Aries',
    so bad data is immediately visible in logs.
    """
    chart = {
        'sun_sign':   'Unknown',
        'moon_sign':  'Unknown',
        'rising_sign':'Unknown',
        'mercury':    'Unknown',
        'venus':      'Unknown',
        'mars':       'Unknown',
        'jupiter':    'Unknown',
        'saturn':     'Unknown',
        'midheaven':  'Unknown',
        'north_node': 'Unknown',
    }

    planet_key_map = {
        'Sun':       'sun_sign',
        'Moon':      'moon_sign',
        'Mercury':   'mercury',
        'Venus':     'venus',
        'Mars':      'mars',
        'Jupiter':   'jupiter',
        'Saturn':    'saturn',
        'Rahu':      'north_node',
        'Ascendant': 'rising_sign',
    }

    for planet in planet_data.get('planet_position', []):
        name      = planet.get('name', '')
        longitude = planet.get('longitude', 0)

        if longitude and longitude > 0:
            sign = longitude_to_tropical_sign(longitude)
        else:
            # Fallback via rasi id — shift by 1 to convert sidereal → tropical
            rasi_id = planet.get('rasi', {}).get('id', -1)
            sign = ZODIAC_SIGNS[(rasi_id + 1) % 12] if 0 <= rasi_id < 12 else 'Unknown'

        if name in planet_key_map:
            chart[planet_key_map[name]] = sign

    # Rising from kundli if available (more accurate)
    if kundli_data:
        asc = kundli_data.get('ascendant', {})
        asc_lon = asc.get('longitude', 0)
        if asc_lon and asc_lon > 0:
            chart['rising_sign'] = longitude_to_tropical_sign(asc_lon)

    print(f"🔭 Parsed chart: Sun={chart['sun_sign']} Moon={chart['moon_sign']} Rising={chart['rising_sign']}")
    return chart


def get_chart_from_prokerala(birth_date, birth_time, birth_place):
    """Orchestrate geocoding + chart fetch. Returns chart dict or None on failure."""
    if not PROKERALA_CLIENT_ID or not PROKERALA_CLIENT_SECRET:
        print("⚠️ Prokerala credentials not configured — skipping API call")
        return None
    try:
        lat, lon, tz = geocode_location(birth_place)
        chart = get_birth_chart(birth_date, birth_time, lat, lon, tz)
        return chart
    except Exception as e:
        print(f"❌ Prokerala error: {e}")
        import traceback; traceback.print_exc()
        return None


# ============================================================
# NUMEROLOGY
# ============================================================

def calculate_life_path(birth_date):
    try:
        if "-" in birth_date:
            y, m, d = [int(x) for x in birth_date.split("-")]
        else:
            dt = datetime.strptime(birth_date, "%B %d, %Y")
            y, m, d = dt.year, dt.month, dt.day
        total = sum(int(c) for c in str(y) + str(m) + str(d))
        while total > 9 and total not in (11, 22, 33):
            total = sum(int(c) for c in str(total))
        return total
    except:
        return 7

def calculate_expression_number(name):
    vals = {'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,
            'j':1,'k':2,'l':3,'m':4,'n':5,'o':6,'p':7,'q':8,'r':9,
            's':1,'t':2,'u':3,'v':4,'w':5,'x':6,'y':7,'z':8}
    total = sum(vals.get(c.lower(), 0) for c in name if c.isalpha())
    while total > 9 and total not in (11, 22, 33):
        total = sum(int(c) for c in str(total))
    return total

def calculate_personal_year(birth_date, target_year=2026):
    """Personal year number = reduced sum of birth month + birth day + target year."""
    try:
        if "-" in birth_date:
            _, m, d = [int(x) for x in birth_date.split("-")]
        else:
            dt = datetime.strptime(birth_date, "%B %d, %Y")
            m, d = dt.month, dt.day
        total = sum(int(c) for c in str(m) + str(d) + str(target_year))
        while total > 9 and total not in (11, 22, 33):
            total = sum(int(c) for c in str(total))
        return total
    except:
        return 5

# ============================================================
# AI CONTENT GENERATION
# ============================================================

def call_claude_api(prompt, max_tokens=1500):
    """Call Claude 3.5 Sonnet via Replicate and poll for result."""
    headers = {
        "Authorization": f"Bearer {REPLICATE_API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {"input": {"prompt": prompt, "max_tokens": max_tokens}}

    try:
        resp = requests.post(REPLICATE_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        prediction = resp.json()

        poll_url = prediction.get("urls", {}).get("get")
        if not poll_url:
            return None

        for _ in range(90):
            time.sleep(1)
            result = requests.get(poll_url, headers=headers, timeout=30).json()
            status = result.get("status")
            if status == "succeeded":
                output = result.get("output", "")
                return "".join(output) if isinstance(output, list) else output
            if status == "failed":
                print("❌ Replicate prediction failed")
                return None

        print("⏱️ Replicate timeout after 90s")
        return None

    except Exception as e:
        print(f"API Error: {e}")
        return None


class AIContentGenerator:
    """
    Generate all AI sections for the book.
    Works excellently with the 2026 shortened quiz (fewer personal answers)
    by driving personalisation through actual planetary positions.
    """

    def __init__(self, user_data, chart_data):
        self.user  = user_data
        self.chart = chart_data

        self.name       = user_data.get("name") or f"{user_data.get('first_name','')} {user_data.get('last_name','')}".strip() or "Friend"
        self.first_name = user_data.get("first_name") or self.name.split()[0]
        self.gender     = (user_data.get("gender") or "").lower()

        self.sun_sign    = chart_data.get("sun_sign",    "Aries")
        self.moon_sign   = chart_data.get("moon_sign",   "Aries")
        self.rising_sign = chart_data.get("rising_sign", "Aries")
        self.venus       = chart_data.get("venus",   "Unknown")
        self.mars        = chart_data.get("mars",    "Unknown")
        self.mercury     = chart_data.get("mercury", "Unknown")
        self.jupiter     = chart_data.get("jupiter", "Unknown")
        self.saturn      = chart_data.get("saturn",  "Unknown")
        self.midheaven   = chart_data.get("midheaven",  "Unknown")
        self.north_node  = chart_data.get("north_node", "Unknown")

        self.life_path        = calculate_life_path(user_data.get("birth_date", "2000-01-01"))
        self.expression_num   = calculate_expression_number(self.name)
        self.personal_year    = calculate_personal_year(user_data.get("birth_date", "2000-01-01"))

        self.sun_data  = ZODIAC_DATA.get(self.sun_sign,    {})
        self.moon_data = ZODIAC_DATA.get(self.moon_sign,   {})
        self.asc_data  = ZODIAC_DATA.get(self.rising_sign, {})

        self.content = {}

    # ----------------------------------------------------------
    # Helper: pronoun set based on gender
    # ----------------------------------------------------------
    def _pronouns(self):
        g = self.gender
        if g in ('female', 'woman', 'f', 'she', 'her'):
            return {'sub': 'she', 'obj': 'her', 'pos': 'her', 'ref': 'herself'}
        if g in ('male', 'man', 'm', 'he', 'him'):
            return {'sub': 'he', 'obj': 'him', 'pos': 'his', 'ref': 'himself'}
        return {'sub': 'they', 'obj': 'them', 'pos': 'their', 'ref': 'themselves'}

    # ----------------------------------------------------------
    # Build context string — gracefully handles missing fields
    # ----------------------------------------------------------
    def _build_context(self):
        def fmt(val, fallback=''):
            if isinstance(val, list):
                return ', '.join(val) if val else fallback
            return val.strip() if val and str(val).strip() else fallback

        u = self.user
        p = self._pronouns()

        # Only include quiz-answer lines if the value is actually set
        quiz_lines = []
        if fmt(u.get('main_goals')):
            quiz_lines.append(f"Primary goals: {fmt(u.get('main_goals'))}")
        if fmt(u.get('relationship_status')):
            quiz_lines.append(f"Relationship status: {fmt(u.get('relationship_status'))}")
        if fmt(u.get('logic_vs_emotions')):
            quiz_lines.append(f"Decision style (logic vs emotions): {fmt(u.get('logic_vs_emotions'))}")
        # Legacy quiz fields — included only if present
        for label, key in [
            ("Outlook",              'outlook'),
            ("Love language",        'love_language'),
            ("Relationship goals",   'relationship_goals'),
            ("Desired partner traits",'desired_partner_traits'),
            ("Career question",      'career_question'),
            ("Motivations",          'motivations'),
            ("Life dreams",          'life_dreams'),
        ]:
            val = fmt(u.get(key))
            if val:
                quiz_lines.append(f"{label}: {val}")

        quiz_section = "\n".join(quiz_lines) if quiz_lines else "(Limited quiz data — rely primarily on chart)"

        return f"""
=== PERSON ===
Name: {self.name}
Gender: {fmt(u.get('gender'), 'not specified')}
Pronouns: {p['sub']}/{p['obj']}/{p['pos']}
Birth: {fmt(u.get('birth_date'))} at {fmt(u.get('birth_time'))}
Place: {fmt(u.get('birth_place'))}

=== NATAL CHART (Western / Tropical) ===
☉ Sun:      {self.sun_sign}   ({self.sun_data.get('element','')} • {self.sun_data.get('modality','')} • ruler {self.sun_data.get('ruler','')})
☽ Moon:     {self.moon_sign}  ({self.moon_data.get('element','')} • {self.moon_data.get('modality','')} • ruler {self.moon_data.get('ruler','')})
↑ Rising:   {self.rising_sign}({self.asc_data.get('element','')} • {self.asc_data.get('modality','')} • ruler {self.asc_data.get('ruler','')})
☿ Mercury:  {self.mercury}
♀ Venus:    {self.venus}
♂ Mars:     {self.mars}
♃ Jupiter:  {self.jupiter}
♄ Saturn:   {self.saturn}
MC:         {self.midheaven}
☊ N.Node:  {self.north_node}

=== NUMEROLOGY ===
Life Path: {self.life_path}  |  Expression: {self.expression_num}  |  2026 Personal Year: {self.personal_year}

=== QUIZ ANSWERS ===
{quiz_section}
"""

    # ----------------------------------------------------------
    # Core generation helper
    # ----------------------------------------------------------
    def generate_section(self, section_name, prompt, max_tokens=1500):
        print(f"  Generating: {section_name}…")

        full_prompt = f"""{prompt}

--- FULL PROFILE ---
{self._build_context()}

WRITING RULES:
• Write in second person ("you / your") — warm, intimate, personal
• Base personalisation primarily on the natal chart data above
• DO NOT quote quiz answers verbatim in quotation marks — synthesise them naturally
• Use SHORT paragraphs (3-4 sentences). No walls of text.
• Never open with a heading like "Analysis for {self.name}" — dive straight into content
• If a field shows "Unknown" treat it as unconfirmed and write around it gracefully
• If quiz data is limited, let the planetary placements carry the analysis — they are rich enough
"""
        result = call_claude_api(full_prompt, max_tokens)
        self.content[section_name] = result or self._fallback(section_name)
        return self.content[section_name]

    # ----------------------------------------------------------
    # Fallbacks (used when API fails or times out)
    # ----------------------------------------------------------
    def _fallback(self, section):
        s = self.sun_sign; m = self.moon_sign; r = self.rising_sign
        fb = {
            'introduction': f"Dear {self.first_name}, welcome to your personalized cosmic blueprint. Your natal chart — with the Sun in {s}, Moon in {m}, and {r} Rising — tells a unique story that this book was written to reveal for you.",
            'sun_sign':    f"Your Sun in {s} is the foundation of your identity. {self.sun_data.get('element','')} energy runs through everything you do, shaping how you pursue goals and express yourself in the world.",
            'moon_sign':   f"Your Moon in {m} colors your inner emotional landscape. This placement reveals how you process feelings, what makes you feel safe, and the hidden rhythms that drive your responses.",
            'rising_sign': f"With {r} Rising, you present a {self.asc_data.get('element','')} energy face to the world. This is your social mask — the first impression you create, and how others instinctively experience you.",
            'personality': f"The interplay of your {s} Sun, {m} Moon, and {r} Rising creates a layered, fascinating personality that defies easy labels.",
            'love':        f"Your Venus in {self.venus} and Mars in {self.mars} tell the real story of how you love and what you desire in a partner.",
            'career':      f"Your Midheaven in {self.midheaven} illuminates your professional calling, while Saturn in {self.saturn} defines the discipline and lessons that shape your path.",
            'forecast':    f"2026 activates powerful themes in your chart. Your {self.personal_year} Personal Year numerology adds another layer of cosmic timing to watch.",
            'numerology':  f"Life Path {self.life_path} is the thread woven through everything you experience — your soul's chosen curriculum for this lifetime.",
            'tarot':       f"The tarot offers a mirror for your {s} energy, reflecting both your gifts and the growth edges the universe is nudging you toward.",
            'crystals':    f"Certain crystals — particularly {self.sun_data.get('crystal','Quartz')} — resonate deeply with your natal chart and can support your journey.",
            'closing':     f"Dear {self.first_name}, may the wisdom encoded in your birth chart — Sun in {s}, Moon in {m}, {r} Rising — light your way forward. With cosmic blessings, ORASTRIA",
        }
        return fb.get(section, "Your personalized cosmic content awaits…")

    # ----------------------------------------------------------
    # Generate all sections
    # ----------------------------------------------------------
    def generate_all(self):
        print(f"\n🌟 Generating AI content for {self.name}…")
        print("=" * 55)

        s  = self.sun_sign
        m  = self.moon_sign
        r  = self.rising_sign
        ve = self.venus
        ma = self.mars
        mc = self.midheaven
        nn = self.north_node
        sa = self.saturn
        ju = self.jupiter
        me = self.mercury

        sun_elem  = self.sun_data.get('element', '')
        sun_ruler = self.sun_data.get('ruler', '')
        moon_elem = self.moon_data.get('element', '')
        asc_elem  = self.asc_data.get('element', '')

        u = self.user
        goals   = u.get('main_goals') or []
        goals_s = ', '.join(goals) if goals else 'personal growth and self-understanding'
        rel     = u.get('relationship_status') or ''
        lve     = u.get('logic_vs_emotions') or ''

        # ── 1. INTRODUCTION ─────────────────────────────────
        self.generate_section('introduction', f"""Write a warm, captivating introduction to this cosmic blueprint book (5 paragraphs, ~550 words).

Opening: Welcome {self.first_name} by name and make them feel this was written specifically for them.
Paragraph 2: Briefly describe what a natal chart reveals — frame it as a map of their soul encoded at birth.
Paragraph 3: Highlight the significance of their unique combination: Sun in {s} ({sun_elem}), Moon in {m} ({moon_elem}), {r} Rising ({asc_elem}). What does this blend suggest at first glance?
Paragraph 4: Mention their primary goals ({goals_s}) and how this book will help illuminate the path toward them.
Paragraph 5: Invite them to read with an open mind and heart — this is a journey of self-discovery.

Tone: Mystical yet grounded, warm, personal. NOT generic horoscope language.""", max_tokens=1600)

        # ── 2. SUN SIGN ─────────────────────────────────────
        self.generate_section('sun_sign', f"""Write a deep, nuanced Sun sign analysis for {self.first_name} (6 paragraphs, ~650 words).

The Sun is in {s} — this is their core identity and life force.

Cover:
1. The essence of {s} energy: its {sun_elem} element, {self.sun_data.get('modality','')} modality, and ruler {sun_ruler}.
2. How this Sun sign expresses itself as a core personality driver — strengths and shadow sides.
3. The interaction with Moon in {m} — how their emotional nature complements or challenges their solar identity.
4. The interaction with {r} Rising — how they project their {s} energy outward.
5. Mercury in {me} — how they think and communicate within this solar framework.
6. Practical guidance: how {self.first_name} can best honour and channel their {s} Sun energy in daily life.

Make it specific and rich — not generic Sun sign content. Reference the other placements to show the chart as a whole.""", max_tokens=1800)

        # ── 3. MOON SIGN ────────────────────────────────────
        self.generate_section('moon_sign', f"""Write a deeply personal Moon sign analysis for {self.first_name} (6 paragraphs, ~650 words).

The Moon is in {m} — this governs emotional needs, instincts, inner security, and the unconscious.

Cover:
1. The emotional landscape of a {m} Moon — what they need to feel safe and nourished.
2. How {m} Moon processes feelings: {moon_elem} energy in the emotional body.
3. Their instinctive reactions and unconscious patterns shaped by this placement.
4. How Moon in {m} influences their relationships — what they seek emotionally from others.
5. The interplay with Venus in {ve} — how emotional needs and love style interact.{f" Reference their decision style ({lve}) as it connects to emotional processing." if lve else ""}
6. Practical advice: daily rituals or approaches that help them honour their {m} Moon needs.

Avoid generic Moon sign content. Make it feel like a personal reading.""", max_tokens=1800)

        # ── 4. RISING SIGN ──────────────────────────────────
        self.generate_section('rising_sign', f"""Write an illuminating Rising Sign analysis for {self.first_name} (5 paragraphs, ~580 words).

The Rising (Ascendant) is {r} — this is the mask they wear, the energy others feel first, and their approach to new situations.

Cover:
1. The energy and appearance of {r} Rising — how {self.first_name} is perceived at first meeting.
2. The {asc_elem} element's role in shaping their outward presence and social style.
3. How {r} Rising influences how they enter new environments or relationships — confident vs cautious, bold vs measured.
4. The relationship between their {r} Rising and their {s} Sun — does the mask align with or contrast the core identity?
5. Guidance: how to work consciously with their {r} Rising energy to make the right first impressions and navigate social situations with authenticity.

Do not reference quiz fields that may be empty. Ground everything in the astrological placements.""", max_tokens=1600)

        # ── 5. INNER WORLD / PERSONALITY ────────────────────
        self.generate_section('personality', f"""Write a rich, layered personality analysis for {self.first_name} (7 paragraphs, ~750 words).

This section dives beneath the surface, using the full chart to paint a portrait of who they truly are.

Structure:
1. The Big Three synthesis: what does Sun in {s} + Moon in {m} + {r} Rising create as a combined personality type?
2. Mercury in {me}: how they think, communicate, and process information. Learning style and mental gifts.
3. The elemental balance in their chart — identify the dominant elements and what that means psychologically.
4. Their relationship with decision-making and logic{f" — tie this to their stated style ({lve})" if lve else ""} — revealed through the air/fire/water/earth balance.
5. Inner tensions or paradoxes in the chart — places where the placements pull in different directions, creating depth.
6. Their core psychological gifts — what the chart says they are naturally exceptional at.
7. Their edges for growth — what the chart gently points to as areas for development. Frame positively.

Synthesise everything into a cohesive portrait. This should feel like you know them deeply.""", max_tokens=2000)

        # ── 6. LOVE & RELATIONSHIPS ─────────────────────────
        rel_context = f"They are currently {rel}." if rel else ""
        goals_love  = ", ".join(u.get('relationship_goals', [])) or ""

        self.generate_section('love', f"""Write a comprehensive love and relationship analysis for {self.first_name} (7 paragraphs, ~750 words).

{rel_context}

Cover:
1. Venus in {ve}: what they are naturally attracted to, how they express love, what they value in a partner.
2. Mars in {ma}: their passion style, how they pursue what they desire, their sexual and romantic drive.
3. The Sun in {s} in relationships — how their core identity shows up in intimate partnerships.
4. The Moon in {m} — their emotional needs from a partner and what makes them feel truly loved and secure.
5. Relationship patterns and tendencies revealed by the Venus/Mars combination — are they a pursuer or receiver? Passionate or measured?{f" Weave in their decision style ({lve}) when discussing emotional vs practical love choices." if lve else ""}
6. {f"Their relationship goals ({goals_love}) and how the chart supports or challenges achieving them." if goals_love else "What the chart suggests they most need in a lasting partnership."}
7. Guidance: what {self.first_name} should prioritise to attract and sustain a truly fulfilling relationship.

Ground every insight in actual chart placements, not generic advice.""", max_tokens=2000)

        # ── 7. CAREER & PURPOSE ─────────────────────────────
        career_q = u.get('career_question') or ''

        self.generate_section('career', f"""Write an inspiring career and purpose analysis for {self.first_name} (7 paragraphs, ~750 words).

Cover:
1. Midheaven in {mc}: their public image, the career path the cosmos designed them for, how they're meant to be known professionally.
2. Sun in {s}: the natural professional strengths and working style this placement brings.
3. Saturn in {sa}: their professional lessons, areas requiring discipline, and where earned mastery will come.
4. North Node in {nn}: their soul's evolutionary direction — where the universe is calling them to grow, including professionally.
5. Jupiter in {ju}: where luck and expansion flow most naturally in their career.
6. Mercury in {me}: their communication and intellectual strengths in a professional context — how they best convey ideas and lead.
7. {f"Directly address their question: {career_q}. What does the chart say about this?" if career_q else f"Synthesise: what career paths and professional environments will allow {self.first_name} to thrive most fully?"}

Be specific and actionable. Reference concrete chart placements for every claim.""", max_tokens=2000)

        # ── 8. 2026 FORECAST ────────────────────────────────
        self.generate_section('forecast', f"""Write an exciting 2026 yearly forecast for {self.first_name} (7 paragraphs, ~750 words).

Key numerology context: they are in a Personal Year {self.personal_year} in 2026.

Cover:
1. Overall 2026 theme for {self.first_name} — what is the overarching cosmic invitation this year?
2. Jupiter's influence in 2026 and how it interacts with their natal Jupiter in {ju} and Sun in {s}.
3. Saturn's lessons and structure themes — how Saturn in {sa} will be activated.
4. Career and financial windows — specific seasons (spring, summer, autumn, winter) that favour professional action.
5. Love and relationships forecast — timing for deepening connections or meeting someone new.
6. Personal growth and spiritual themes for the year — what the North Node in {nn} suggests.
7. The Personal Year {self.personal_year} energy — how numerology amplifies or challenges the astrological themes.

Be specific about timing and seasons. Make it feel like a real forecast, not generic positivity.""", max_tokens=2000)

        # ── 9. NUMEROLOGY ───────────────────────────────────
        self.generate_section('numerology', f"""Write a rich numerology section for {self.first_name} (6 paragraphs, ~650 words).

Numbers: Life Path {self.life_path} | Expression {self.expression_num} | 2026 Personal Year {self.personal_year}

Cover:
1. Life Path {self.life_path}: the overarching soul journey and life theme this number represents.
2. How Life Path {self.life_path} interacts with their Sun in {s} — do they amplify or balance each other?
3. Expression Number {self.expression_num}: the natural talents and gifts encoded in their name.
4. The Personal Year {self.personal_year} in 2026: what energetic theme governs this specific year, and how to work with it.
5. Key universal months within their 2026 Personal Year that are especially potent — identify 2-3 stand-out months.
6. How numerology and astrology together confirm the same themes — show the coherence between these systems for {self.first_name}.

Make it specific and illuminating, not generic number descriptions.""", max_tokens=1800)

        # ── 10. TAROT ───────────────────────────────────────
        self.generate_section('tarot', f"""Write a deeply personal tarot guidance section for {self.first_name} (6 paragraphs, ~650 words).

Cover:
1. Identify their Sun card (the Major Arcana card associated with {s}) and explain its significance for them.
2. Their Moon card (associated with {m}) — emotional wisdom and shadow themes.
3. A 3-card reading tailored to their goals ({goals_s}): Past / Present / Future. Name specific tarot cards for each position and interpret them for {self.first_name}'s situation.
4. A card for their love life — what the tarot is saying about their romantic path right now.
5. A card for their career / purpose — guidance from the tarot for their professional growth.
6. Overall tarot message for 2026 — a closing card and its meaning for the year ahead.

Choose real, specific tarot cards (not placeholders). Make the interpretations personal to their chart.""", max_tokens=1800)

        # ── 11. CRYSTALS & RITUALS ──────────────────────────
        self.generate_section('crystals', f"""Write a beautifully practical crystals and rituals section for {self.first_name} (6 paragraphs, ~650 words).

Cover:
1. 3 primary power crystals for their Sun in {s} — name each, explain why it resonates and how to use it.
2. 2 crystals for their Moon in {m} — emotional support and inner healing.
3. 1 crystal for Venus in {ve} — supporting their love life and relationships.
4. A New Moon ritual designed for {s} energy — a specific step-by-step practice (3-4 steps) they can do each new moon.
5. A Full Moon ritual for their {m} Moon — what to release, reflect on, or celebrate.
6. A short daily grounding practice tailored to their chart's dominant elements ({sun_elem} Sun, {moon_elem} Moon) — something achievable in 5-10 minutes.

Be practical and specific. Include actual crystal names, actions, intentions.""", max_tokens=1800)

        # ── 12. CLOSING ─────────────────────────────────────
        self.generate_section('closing', f"""Write a warm, memorable closing letter for {self.first_name} (5 paragraphs, ~550 words).

1. Acknowledge the journey they've just taken through their cosmic blueprint.
2. Summarise the most important insight from their chart — one thing about their Sun in {s} + Moon in {m} + {r} Rising combination they should carry with them.
3. Connect to their goals ({goals_s}) — affirm that the stars support their path.
4. Offer an empowering forward-looking statement: they are not defined by their chart, but the chart illuminates their highest potential.
5. A warm, personalised blessing that references their Sun, Moon, and Rising in a poetic final sentence.

Sign off: "With cosmic blessings, ORASTRIA"

Tone: heartfelt, uplifting, like a letter from a wise friend.""", max_tokens=1600)

        # ── COMPATIBILITY (batched, 2 API calls) ─────────────
        print("  Generating: compatibility (batched)…")
        self.content['compatibility'] = {}

        for batch in [ZODIAC_ORDER[:6], ZODIAC_ORDER[6:]]:
            batch_str = ', '.join(batch)
            prompt = f"""Write compatibility for {s} Sun with: {batch_str}.

{self.first_name} has Venus in {ve} and Mars in {ma}.

For EACH sign, write 2 rich paragraphs (~120-150 words total) covering:
- The core dynamic between {s} and that sign
- How Venus in {ve} and Mars in {ma} colour this pairing
- Practical compatibility insight

Then provide a PERCENTAGE score (realistic, varied between 45-95%).

Format EXACTLY as:
{batch[0].upper()}:
[content]
PERCENTAGE: XX%

{batch[1].upper()}:
[content]
PERCENTAGE: XX%

(continue for all {len(batch)} signs)"""

            result = call_claude_api(f"{prompt}\n\n{self._build_context()}", max_tokens=2500)
            if result:
                self._parse_compat(result, batch)

        # Fill any missing signs with defaults
        for sign in ZODIAC_ORDER:
            if sign not in self.content['compatibility']:
                self.content['compatibility'][sign] = {
                    'text': f"{s} and {sign} create an intriguing dynamic shaped by their contrasting yet complementary energies.",
                    'percentage': 65
                }

        # ── MONTHLY FORECASTS (batched, 2 API calls) ─────────
        print("  Generating: monthly forecasts (batched)…")
        self.content['monthly'] = {}
        all_months = ["January","February","March","April","May","June",
                      "July","August","September","October","November","December"]

        for batch in [all_months[:6], all_months[6:]]:
            batch_str = ', '.join(batch)
            prompt = f"""Write 2026 monthly forecasts for {self.first_name} (Sun: {s}, Moon: {m}, Personal Year: {self.personal_year}) for: {batch_str}.

For EACH month write 2 specific paragraphs (~120 words total) covering:
- The dominant astrological or numerological energy active that month
- A practical focus area (love, career, health, or spiritual — vary by month)
- One concrete action or theme for the month

Forecasts must be VARIED — not all "transformation and growth". Make each month feel distinct.

Format EXACTLY as:
{batch[0].upper()}:
[content]

{batch[1].upper()}:
[content]

(continue for all {len(batch)} months)"""

            result = call_claude_api(f"{prompt}\n\n{self._build_context()}", max_tokens=2500)
            if result:
                self._parse_monthly(result, batch)

        for month in all_months:
            if month not in self.content['monthly']:
                self.content['monthly'][month] = f"{month} 2026 invites you to focus inward and align your actions with your natal chart's deepest wisdom."

        print("=" * 55)
        print("✅ All AI content generated!")
        return self.content

    # ----------------------------------------------------------
    # Parsing helpers
    # ----------------------------------------------------------
    def _parse_compat(self, text, signs):
        import re
        for sign in signs:
            # Match sign header to either PERCENTAGE line or next sign header
            pattern = rf'{sign.upper()}:\s*(.*?)(?=PERCENTAGE:\s*(\d+))'
            match   = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                content    = match.group(1).strip()
                # Find percentage right after the content block
                pct_match  = re.search(rf'{sign.upper()}:.*?PERCENTAGE:\s*(\d+)', text, re.DOTALL | re.IGNORECASE)
                percentage = int(pct_match.group(1)) if pct_match else 70
                self.content['compatibility'][sign] = {'text': content, 'percentage': percentage}
            else:
                # Looser fallback
                next_signs = '|'.join(s.upper() for s in ZODIAC_SIGNS if s != sign)
                loose = re.search(rf'{sign.upper()}:\s*(.*?)(?=(?:{next_signs}):|$)', text, re.DOTALL | re.IGNORECASE)
                if loose:
                    raw = loose.group(1).strip()
                    pct = re.search(r'(\d+)%', raw)
                    percentage = int(pct.group(1)) if pct else 70
                    self.content['compatibility'][sign] = {'text': raw, 'percentage': percentage}

    def _parse_monthly(self, text, months):
        import re
        all_upper = '|'.join(m.upper() for m in [
            "JANUARY","FEBRUARY","MARCH","APRIL","MAY","JUNE",
            "JULY","AUGUST","SEPTEMBER","OCTOBER","NOVEMBER","DECEMBER"
        ])
        for month in months:
            pattern = rf'{month.upper()}:\s*(.*?)(?=(?:{all_upper}):|$)'
            match   = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                self.content['monthly'][month] = match.group(1).strip()


# ============================================================
# PDF BOOK GENERATOR  (unchanged layout, fixes applied)
# ============================================================

class OrastriaVisualBook:
    """Generate the beautiful PDF book from AI content and chart data."""

    def __init__(self, user_data, chart_data, ai_content, output_path):
        self.user    = user_data
        self.chart   = chart_data
        self.content = ai_content
        self.output_path = output_path

        self.width, self.height = letter
        self.margin  = 0.75 * inch
        self.page_num = 0
        self.c = canvas.Canvas(output_path, pagesize=letter)

        self.name       = user_data.get("name") or f"{user_data.get('first_name','')} {user_data.get('last_name','')}".strip() or "Friend"
        self.first_name = user_data.get("first_name") or self.name.split()[0]

        self.sun_sign    = chart_data.get("sun_sign",    "Aries")
        self.moon_sign   = chart_data.get("moon_sign",   "Aries")
        self.rising_sign = chart_data.get("rising_sign", "Aries")

        color_choice       = user_data.get('book_color', 'navy').lower()
        self.theme         = COLOR_THEMES.get(color_choice, COLOR_THEMES['navy'])
        self.primary_color = self.theme['primary']
        self.accent_color  = self.theme['accent']

        # Format birth date for display
        bd = user_data.get("birth_date", "2000-01-01")
        if "-" in bd:
            parts = bd.split("-")
            months_names = ["","January","February","March","April","May","June",
                            "July","August","September","October","November","December"]
            try:
                self.birth_date_formatted = f"{months_names[int(parts[1])]} {int(parts[2])}, {parts[0]}"
            except:
                self.birth_date_formatted = bd
        else:
            self.birth_date_formatted = bd

    # ── Color bar helper ─────────────────────────────────────
    def get_compat_color(self, percentage):
        if percentage >= 80: return GREEN
        if percentage >= 65: return YELLOW
        if percentage >= 50: return ORANGE
        return RED

    # ── Page chrome ──────────────────────────────────────────
    def new_page(self):
        self.page_num += 1
        c = self.c
        c.setFillColor(CREAM)
        c.rect(0, 0, self.width, self.height, fill=True, stroke=False)
        c.setFillColor(GOLD)
        c.setFont(FONT_SYMBOL, 10)
        for x, y in [(50, self.height-50),(self.width-50, self.height-50),(50,50),(self.width-50,50)]:
            c.drawCentredString(x, y, '✦')
        c.setFillColor(NAVY)
        c.setFont(FONT_BODY, 10)
        c.drawCentredString(self.width/2, 30, f"— {self.page_num} —")
        return self.height - 80

    def draw_chapter(self, title, subtitle=None, icon=None):
        chapter_icons = {
            "Introduction":       "✧", "The Big Three":       "☉",
            "Your Inner World":   "◆", "Love & Relationships":"♥",
            "Compatibility Guide":"♡", "Career & Purpose":    "★",
            "Important Dates":    "◈", "Your Year Ahead":     "☆",
            "Monthly Forecasts":  "◇", "Numerology":          "∞",
            "Tarot Guidance":     "▲", "Crystals & Rituals":  "◆",
            "Your Cosmic Summary":"✦", "Closing Thoughts":    "∞",
        }
        y = self.new_page()
        c = self.c
        display_icon = icon or chapter_icons.get(title, "✧")
        c.setFillColor(GOLD)
        c.setFont(FONT_SYMBOL_BOLD, 48)
        c.drawCentredString(self.width/2, self.height - 180, display_icon)
        c.setStrokeColor(GOLD)
        c.setLineWidth(1)
        c.line(self.width/2 - 60, self.height-220, self.width/2 + 60, self.height-220)
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 32)
        c.drawCentredString(self.width/2, self.height - 280, title)
        if subtitle:
            c.setFillColor(SOFT_GOLD)
            c.setFont(FONT_BODY_ITALIC, 16)
            c.drawCentredString(self.width/2, self.height - 320, subtitle)
        c.setFillColor(GOLD)
        c.setFont(FONT_SYMBOL, 14)
        c.drawCentredString(self.width/2, self.height - 380, "✧  ✦  ✧")
        c.showPage()

    # ── Cover ────────────────────────────────────────────────
    def draw_cover(self):
        c = self.c
        c.setFillColor(self.primary_color)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        c.setStrokeColor(self.accent_color)
        c.setLineWidth(2)
        c.rect(0.4*inch, 0.4*inch, self.width-0.8*inch, self.height-0.8*inch)
        c.setLineWidth(1)
        c.rect(0.5*inch, 0.5*inch, self.width-1*inch, self.height-1*inch)
        c.setFont(FONT_SYMBOL_BOLD, 24)
        c.setFillColor(self.accent_color)
        c.drawCentredString(0.8*inch,          self.height-0.8*inch, '☉')
        c.drawCentredString(self.width-0.8*inch, self.height-0.8*inch, '☽')
        c.setFont(FONT_HEADING_BOLD, 36)
        c.drawCentredString(self.width/2, self.height-1.8*inch, "YOUR COSMIC")
        c.drawCentredString(self.width/2, self.height-2.3*inch, "BLUEPRINT")
        c.setLineWidth(1)
        c.line(2*inch, self.height-2.55*inch, self.width-2*inch, self.height-2.55*inch)
        c.setFillColor(white)
        c.setFont(FONT_HEADING_BOLD, 28)
        c.drawCentredString(self.width/2, self.height-3.2*inch, self.name)
        c.setFillColor(SOFT_GOLD)
        c.setFont(FONT_BODY, 12)
        birth_time = f"{self.user.get('birth_time','')} {self.user.get('birth_time_period','')}".strip()
        c.drawCentredString(self.width/2, self.height-3.6*inch, f"{self.birth_date_formatted}  •  {birth_time}")
        c.drawCentredString(self.width/2, self.height-3.85*inch, self.user.get('birth_place',''))
        cy = self.height/2 - 0.3*inch
        c.setStrokeColor(self.accent_color)
        c.setLineWidth(2)
        c.circle(self.width/2, cy, 85)
        c.setLineWidth(1)
        c.circle(self.width/2, cy, 95)
        c.setFillColor(self.accent_color)
        c.setFont(FONT_SYMBOL_BOLD, 72)
        c.drawCentredString(self.width/2, cy-15, ZODIAC_SYMBOLS.get(self.sun_sign,'★'))
        c.setFont(FONT_HEADING_BOLD, 18)
        c.drawCentredString(self.width/2, cy-60, self.sun_sign.upper())
        c.setFont(FONT_SYMBOL, 11)
        c.setFillColor(white)
        c.drawCentredString(self.width/2, cy-115, f"☉ Sun: {self.sun_sign}  •  ☽ Moon: {self.moon_sign}  •  ↑ Rising: {self.rising_sign}")
        c.setFillColor(self.accent_color)
        c.setFont(FONT_HEADING_BOLD, 22)
        c.drawCentredString(self.width/2, 1.3*inch, "ORASTRIA")
        c.setFont(FONT_BODY, 10)
        c.drawCentredString(self.width/2, 1*inch, "Personalized Astrology  •  Written in the Stars")
        c.setFont(FONT_SYMBOL, 16)
        c.drawCentredString(0.8*inch, 0.8*inch, '☽')
        c.drawCentredString(self.width-0.8*inch, 0.8*inch, '☽')
        c.showPage()

    # ── Table of Contents ────────────────────────────────────
    def draw_table_of_contents(self):
        y = self.new_page()
        c = self.c
        c.setFillColor(GOLD)
        c.setFont(FONT_SYMBOL, 24)
        c.drawCentredString(self.width/2, self.height-80, "✧")
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 28)
        c.drawCentredString(self.width/2, self.height-120, "Table of Contents")
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.5)
        c.line(self.width/2-80, self.height-140, self.width/2+80, self.height-140)
        toc_entries = [
            ("Your Birth Chart",              "☉"),
            ("Introduction",                  "✧"),
            ("The Big Three: Sun, Moon & Rising","★"),
            ("Your Inner World",              "◆"),
            ("Love & Relationships",          "♥"),
            ("Compatibility Guide",           "♡"),
            ("Career & Purpose",              "★"),
            ("Your Year Ahead: 2026",         "☆"),
            ("Monthly Forecasts",             "◇"),
            ("Numerology",                    "∞"),
            ("Tarot Guidance",                "▲"),
            ("Crystals & Rituals",            "◆"),
            ("Your Cosmic Summary",           "✦"),
            ("Closing Thoughts",              "∞"),
        ]
        y = self.height - 180
        for title, icon in toc_entries:
            c.setFillColor(GOLD)
            c.setFont(FONT_SYMBOL, 12)
            c.drawString(self.margin+10, y, icon)
            c.setFillColor(NAVY)
            c.setFont(FONT_BODY, 12)
            c.drawString(self.margin+35, y, title)
            c.setFillColor(HexColor('#cccccc'))
            dots_start = self.margin + 40 + c.stringWidth(title, FONT_BODY, 12)
            dot_x = dots_start + 10
            while dot_x < self.width - self.margin:
                c.drawString(dot_x, y, ".")
                dot_x += 6
            y -= 28
        c.showPage()

    # ── Birth Chart Wheel ────────────────────────────────────
    def draw_birth_chart_wheel(self):
        y = self.new_page()
        c = self.c
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 24)
        c.drawCentredString(self.width/2, self.height-100, "Your Birth Chart")
        c.setFillColor(HexColor('#666666'))
        c.setFont(FONT_BODY_ITALIC, 12)
        c.drawCentredString(self.width/2, self.height-125, "A snapshot of the heavens at the moment you were born")
        cx = self.width/2
        cy = self.height/2 + 0.5*inch
        c.setStrokeColor(NAVY)
        c.setLineWidth(2); c.circle(cx, cy, 140)
        c.setLineWidth(1); c.circle(cx, cy, 110); c.circle(cx, cy, 60)
        c.setStrokeColor(HexColor('#cccccc'))
        c.setLineWidth(0.5)
        for i in range(12):
            angle = (90 - i*30)*math.pi/180
            c.line(cx+60*math.cos(angle), cy+60*math.sin(angle),
                   cx+140*math.cos(angle), cy+140*math.sin(angle))
        for i, sign in enumerate(ZODIAC_ORDER):
            angle = (75 - i*30)*math.pi/180
            x = cx + 125*math.cos(angle)
            sy = cy + 125*math.sin(angle)
            if   sign == self.sun_sign:    c.setFillColor(GOLD)
            elif sign == self.moon_sign:   c.setFillColor(HexColor('#8899AA'))
            elif sign == self.rising_sign: c.setFillColor(HexColor('#AA7755'))
            else:                          c.setFillColor(NAVY)
            c.setFont(FONT_SYMBOL_BOLD, 14)
            c.drawCentredString(x, sy-5, ZODIAC_SYMBOLS.get(sign,'★'))
        c.setFillColor(HexColor('#faf8f5'))
        c.circle(cx, cy, 55, fill=1, stroke=0)
        c.setStrokeColor(GOLD); c.setLineWidth(1); c.circle(cx, cy, 45)
        c.setStrokeColor(GOLD); c.setLineWidth(1.5)
        c.circle(cx-18, cy+8, 14, fill=0, stroke=1)
        c.setFillColor(GOLD); c.setFont(FONT_SYMBOL_BOLD, 18)
        c.drawCentredString(cx-18, cy+3, '☉')
        c.setStrokeColor(HexColor('#7788AA')); c.setLineWidth(1.5)
        c.circle(cx+18, cy+8, 14, fill=0, stroke=1)
        c.setFillColor(HexColor('#7788AA'))
        c.drawCentredString(cx+18, cy+3, '☽')
        c.setFillColor(NAVY); c.setFont(FONT_BODY_BOLD, 9)
        c.drawCentredString(cx, cy-22, f"{self.sun_sign[:3]} / {self.moon_sign[:3]} / {self.rising_sign[:3]}")
        y_table = 2.8*inch
        c.setFillColor(NAVY); c.setFont(FONT_HEADING_BOLD, 14)
        c.drawCentredString(self.width/2, y_table+0.4*inch, "Your Planetary Positions")
        table_w = 5*inch
        table_x = (self.width-table_w)/2
        c.setFillColor(CREAM)
        c.roundRect(table_x, y_table-1.6*inch, table_w, 1.8*inch, 5, fill=1, stroke=0)
        planets = [
            ("☉","Sun",        self.sun_sign),
            ("☽","Moon",       self.moon_sign),
            ("↑","Rising",     self.rising_sign),
            ("☿","Mercury",    self.chart.get('mercury','—')),
            ("♀","Venus",      self.chart.get('venus','—')),
            ("♂","Mars",       self.chart.get('mars','—')),
            ("♃","Jupiter",    self.chart.get('jupiter','—')),
            ("♄","Saturn",     self.chart.get('saturn','—')),
            ("MC","Midheaven", self.chart.get('midheaven','—')),
            ("☊","North Node", self.chart.get('north_node','—')),
        ]
        c1x = table_x+20; c2x = table_x+table_w/2+20
        for i, (sym, name, sign) in enumerate(planets):
            x   = c1x if i < 5 else c2x
            row = y_table - (i%5)*0.3*inch
            c.setFillColor(GOLD); c.setFont(FONT_SYMBOL, 12); c.drawString(x, row, sym)
            c.setFillColor(NAVY); c.setFont(FONT_BODY, 10);   c.drawString(x+25, row, name)
            c.setFillColor(HexColor('#444444'));                c.drawString(x+90, row, sign)
        c.showPage()

    # ── Glossary (only for explicit beginner) ────────────────
    def draw_glossary_page(self):
        self.draw_chapter("Astrology Glossary", "Key Terms Explained")
        y = self.new_page()
        c = self.c
        glossary = [
            ("Sun Sign",           "Your core identity and ego — where the Sun was at your birth."),
            ("Moon Sign",          "Your emotional nature and inner self — how you process feelings."),
            ("Rising (Ascendant)", "The energy others perceive first — your social mask and outer presence."),
            ("Venus",              "Planet of love and beauty — how you express affection and what you value."),
            ("Mars",               "Planet of action and desire — your drive, passion, and assertion style."),
            ("Mercury",            "Planet of communication — how you think, learn, and express ideas."),
            ("Jupiter",            "Planet of expansion — where you find luck, growth, and opportunity."),
            ("Saturn",             "Planet of discipline — your life lessons, responsibilities, and mastery."),
            ("Midheaven (MC)",     "Your public image and career path — what you're known for professionally."),
            ("North Node",         "Your soul's evolutionary direction — where you're meant to grow."),
            ("Transit",            "A planet moving through a sign, creating temporary influences on your chart."),
            ("Element",            "Fire, Earth, Air, or Water — the fundamental energy quality of each sign."),
            ("Modality",           "Cardinal (initiate), Fixed (sustain), or Mutable (adapt) — the sign's mode of action."),
        ]
        c.setFillColor(NAVY); c.setFont(FONT_HEADING_BOLD, 16)
        c.drawString(self.margin, y, "Understanding Your Chart")
        y -= 30
        c.setFont(FONT_BODY, 10); c.setFillColor(HexColor('#666666'))
        c.drawString(self.margin, y, "Reference these terms as you read through your personalized analysis.")
        y -= 30
        for term, defn in glossary:
            if y < self.margin + 60:
                c.showPage(); y = self.new_page()
            c.setFillColor(NAVY); c.setFont(FONT_BODY_BOLD, 11)
            c.drawString(self.margin, y, term)
            c.setFillColor(HexColor('#444444')); c.setFont(FONT_BODY, 10)
            wrapper = textwrap.TextWrapper(width=85)
            def_y = y - 16
            for line in wrapper.wrap(defn):
                c.drawString(self.margin+10, def_y, line); def_y -= 14
            y = def_y - 10
        c.showPage()

    # ── Section title ────────────────────────────────────────
    def draw_section_title(self, text, y):
        c = self.c
        c.setFillColor(NAVY); c.setFont(FONT_HEADING_BOLD, 18)
        c.drawString(self.margin, y, text)
        c.setStrokeColor(GOLD); c.setLineWidth(2)
        c.line(self.margin, y-5, self.margin+60, y-5)
        return y - 35

    # ── Body text ────────────────────────────────────────────
    def draw_text(self, text, y, width=None):
        if not text: return y
        c = self.c
        c.setFillColor(NAVY); c.setFont(FONT_BODY, 11)
        if width is None: width = self.width - 2*self.margin
        wrapper = textwrap.TextWrapper(width=int(width/5.5))
        paragraphs = text.split('\n\n') if '\n\n' in text else text.split('\n')
        for para in paragraphs:
            para = para.strip()
            if not para: continue
            for line in wrapper.wrap(para):
                if y < self.margin + 50:
                    c.showPage(); y = self.new_page()
                    c.setFillColor(NAVY); c.setFont(FONT_BODY, 11)
                c.drawString(self.margin, y, line)
                y -= 16
            y -= 8
        return y

    # ── Compatibility entry ──────────────────────────────────
    def draw_compat_entry(self, sign, data, y):
        c = self.c
        if y < self.margin + 120:
            c.showPage(); y = self.new_page()
        if isinstance(data, dict):
            text       = data.get('text', '')
            percentage = data.get('percentage', 70)
        else:
            text = data
            import re
            m = re.search(r'(\d+)%', text)
            percentage = int(m.group(1)) if m else 70
        c.setFillColor(GOLD); c.setFont(FONT_SYMBOL_BOLD, 18)
        c.drawString(self.margin, y, ZODIAC_SYMBOLS.get(sign,'★'))
        c.setFillColor(NAVY); c.setFont(FONT_HEADING_BOLD, 14)
        c.drawString(self.margin+30, y, sign)
        bar_w = 120; bar_h = 12
        bar_x = self.width - self.margin - bar_w - 50
        bar_y = y - 2
        c.setFillColor(LIGHT_GRAY); c.rect(bar_x, bar_y, bar_w, bar_h, fill=1, stroke=0)
        fill_w = bar_w * (percentage/100)
        c.setFillColor(self.get_compat_color(percentage))
        c.rect(bar_x, bar_y, fill_w, bar_h, fill=1, stroke=0)
        c.setFillColor(NAVY); c.setFont(FONT_BODY_BOLD, 11)
        c.drawString(bar_x+bar_w+10, y-2, f"{percentage}%")
        y -= 25
        if text:
            sentences = text.split('.')[:3]
            short_text = '.'.join(sentences) + '.' if sentences else text[:200]
            y = self.draw_text(short_text, y, width=self.width-2.5*self.margin)
        return y - 15

    # ── Monthly entry ────────────────────────────────────────
    def draw_monthly_entry(self, month, text, y):
        c = self.c
        if y < self.margin + 100:
            c.showPage(); y = self.new_page()
        c.setFillColor(GOLD); c.setFont(FONT_SYMBOL, 12); c.drawString(self.margin, y, "✧")
        c.setFillColor(NAVY); c.setFont(FONT_HEADING_BOLD, 14)
        c.drawString(self.margin+20, y, f"{month} 2026")
        y -= 20
        if text: y = self.draw_text(text, y)
        return y - 10

    # ── Summary page ─────────────────────────────────────────
    def draw_summary_page(self):
        self.draw_chapter("Your Cosmic Summary", "Key Takeaways at a Glance")
        y = self.new_page()
        c = self.c
        c.setFillColor(HexColor('#1a1f3c'))
        c.roundRect(self.margin, y-100, self.width-2*self.margin, 110, 10, fill=1, stroke=0)
        c.setFillColor(GOLD); c.setFont(FONT_HEADING_BOLD, 16)
        c.drawCentredString(self.width/2, y-15, "Your Big Three")
        col_w = (self.width-2*self.margin)/3
        for i, (sym, label, sign) in enumerate([("☉","SUN",self.sun_sign),("☽","MOON",self.moon_sign),("↑","RISING",self.rising_sign)]):
            cx = self.margin + col_w/2 + i*col_w
            c.setFont(FONT_SYMBOL_BOLD, 28); c.setFillColor(GOLD); c.drawCentredString(cx, y-45, sym)
            c.setFont(FONT_BODY, 9); c.setFillColor(HexColor('#888888')); c.drawCentredString(cx, y-65, label)
            c.setFont(FONT_BODY_BOLD, 12); c.setFillColor(white); c.drawCentredString(cx, y-82, sign)
        y -= 130
        c.setFillColor(GOLD); c.setFont(FONT_SYMBOL, 14); c.drawString(self.margin, y, "✧")
        c.setFillColor(NAVY); c.setFont(FONT_HEADING_BOLD, 14); c.drawString(self.margin+18, y, "Your Top Compatible Signs")
        y -= 25
        compat = self.content.get('compatibility', {})
        sorted_compat = sorted(
            [(s, d.get('percentage',70) if isinstance(d,dict) else 70) for s,d in compat.items()],
            key=lambda x: x[1], reverse=True
        )[:3]
        for sign, pct in sorted_compat:
            c.setFillColor(GOLD); c.setFont(FONT_SYMBOL, 14); c.drawString(self.margin+10, y, ZODIAC_SYMBOLS.get(sign,'★'))
            c.setFillColor(NAVY); c.setFont(FONT_BODY_BOLD, 11); c.drawString(self.margin+35, y, sign)
            c.setFillColor(HexColor('#666666')); c.setFont(FONT_BODY, 11); c.drawString(self.margin+130, y, f"{pct}%")
            y -= 22
        y -= 20
        c.setFillColor(GOLD); c.setFont(FONT_SYMBOL, 14); c.drawString(self.margin, y, "✧")
        c.setFillColor(NAVY); c.setFont(FONT_HEADING_BOLD, 14); c.drawString(self.margin+18, y, "Your Numbers")
        y -= 25
        lp = calculate_life_path(self.user.get('birth_date','2000-01-01'))
        ex = calculate_expression_number(self.name)
        py = calculate_personal_year(self.user.get('birth_date','2000-01-01'))
        c.setFont(FONT_BODY, 11); c.setFillColor(HexColor('#444444'))
        c.drawString(self.margin+10, y, f"Life Path: {lp}")
        c.drawString(self.margin+150, y, f"Expression: {ex}")
        c.drawString(self.margin+270, y, f"2026 Personal Year: {py}")
        y -= 35
        c.setFillColor(GOLD); c.setFont(FONT_SYMBOL, 14); c.drawString(self.margin, y, "✧")
        c.setFillColor(NAVY); c.setFont(FONT_HEADING_BOLD, 14); c.drawString(self.margin+18, y, "2026 Highlights")
        y -= 25
        highlights = [
            "Career breakthrough windows identified in your forecast",
            "Key relationship growth periods mapped by planetary transits",
            f"Personal Year {py} theme shapes your entire 2026 journey",
        ]
        for h in highlights:
            c.setFillColor(GOLD); c.setFont(FONT_SYMBOL, 10); c.drawString(self.margin+10, y, "•")
            c.setFillColor(HexColor('#444444')); c.setFont(FONT_BODY, 10); c.drawString(self.margin+25, y, h)
            y -= 18
        y -= 25
        # Lucky elements cards
        element = ZODIAC_DATA.get(self.sun_sign, {}).get('element', 'Fire')
        lucky_colors = {'Fire':'Red, Orange, Gold','Earth':'Green, Brown, Tan','Air':'Yellow, Light Blue, White','Water':'Blue, Silver, Sea Green'}
        lucky_days   = {'Fire':'Tuesday, Sunday','Earth':'Friday, Saturday','Air':'Wednesday, Thursday','Water':'Monday, Friday'}
        c.setFillColor(GOLD); c.setFont(FONT_SYMBOL, 14); c.drawString(self.margin, y, "✧")
        c.setFillColor(NAVY); c.setFont(FONT_HEADING_BOLD, 14); c.drawString(self.margin+18, y, "Your Lucky Elements")
        y -= 25
        card_w = (self.width-2*self.margin-24)/4; card_h = 75; card_y = y - card_h
        cards = [
            ("Element",     element,                                    ZODIAC_SYMBOLS.get(self.sun_sign,'★')),
            ("Lucky Colors",lucky_colors.get(element,'Gold'),           "◆"),
            ("Lucky Days",  lucky_days.get(element,'Sunday'),           "☆"),
            ("Power Crystal",ZODIAC_DATA.get(self.sun_sign,{}).get('crystal','Quartz'),"◇"),
        ]
        for i, (label, value, icon) in enumerate(cards):
            cx = self.margin + i*(card_w+8)
            c.setFillColor(HexColor('#f5f3ef'))
            c.roundRect(cx, card_y, card_w, card_h, 8, fill=1, stroke=0)
            c.setStrokeColor(HexColor('#e0dcd5')); c.setLineWidth(1)
            c.roundRect(cx, card_y, card_w, card_h, 8, fill=0, stroke=1)
            c.setFillColor(GOLD); c.setFont(FONT_SYMBOL, 18)
            c.drawCentredString(cx+card_w/2, card_y+card_h-20, icon)
            c.setFillColor(HexColor('#888888')); c.setFont(FONT_BODY, 8)
            c.drawCentredString(cx+card_w/2, card_y+card_h-38, label)
            c.setFillColor(NAVY); c.setFont(FONT_BODY_BOLD, 8)
            c.drawCentredString(cx+card_w/2, card_y+12, value)
        c.showPage()

    # ── Upsell page ──────────────────────────────────────────
    def draw_upsell_page(self):
        c = self.c
        self.page_num += 1
        DEEP_NAVY   = HexColor('#0f1628')
        MID_NAVY    = HexColor('#252b4a')
        PURPLE_ICON = HexColor('#6b4c9a')
        LIGHT_PURPLE= HexColor('#9b7bc7')
        TEAL        = HexColor('#2d7a6d')
        LIGHT_TEAL  = HexColor('#3a9a8a')
        SUPSOFGOLD  = HexColor('#d4b87a')
        steps = 60; step_h = self.height/steps
        c1 = DEEP_NAVY; c2 = HexColor('#1a2040')
        for i in range(steps):
            r_ = c1.red   + (c2.red   - c1.red)   * i/steps
            g_ = c1.green + (c2.green - c1.green) * i/steps
            b_ = c1.blue  + (c2.blue  - c1.blue)  * i/steps
            c.setFillColor(Color(r_, g_, b_))
            c.rect(0, self.height-(i+1)*step_h, self.width, step_h+1, fill=1, stroke=0)
        c.setFillColor(MID_NAVY)
        c.ellipse(-2*inch, self.height-2*inch, self.width+2*inch, self.height+2.5*inch, fill=1, stroke=0)
        c.setFillColor(GOLD); c.rect(0, self.height-6, self.width, 6, fill=1, stroke=0)
        c.setFillColor(SUPSOFGOLD); c.setFont(FONT_SYMBOL, 10)
        c.drawCentredString(35, self.height-35, '✦')
        c.drawCentredString(self.width-35, self.height-35, '✦')
        badge_y = self.height-70
        c.setFillColor(GOLD); c.roundRect(self.width/2-85, badge_y-9, 170, 24, 12, fill=1, stroke=0)
        c.setFillColor(DEEP_NAVY); c.setFont(FONT_BODY_BOLD, 9)
        c.drawCentredString(self.width/2, badge_y-1, "YOUR EXCLUSIVE GIFT")
        c.setFillColor(white); c.setFont(FONT_HEADING_BOLD, 34)
        c.drawCentredString(self.width/2, self.height-115, "Continue Your")
        c.drawCentredString(self.width/2, self.height-152, "Cosmic Journey")
        c.setFillColor(SUPSOFGOLD); c.setFont(FONT_BODY_ITALIC, 13)
        c.drawCentredString(self.width/2, self.height-180, "Your personalized book is just the beginning")
        img_y = self.height-380; img_w = 5.2*inch; img_h = 2.5*inch
        img_x = (self.width-img_w)/2
        try:
            import tempfile as _tmp
            timg = _tmp.NamedTemporaryFile(suffix='.png', delete=False)
            urllib.request.urlretrieve("https://f005.backblazeb2.com/file/publicorastria/book-last-page-image.png", timg.name)
            c.drawImage(timg.name, img_x, img_y, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
            os.unlink(timg.name)
        except Exception as e:
            print(f"⚠️ Promo image failed: {e}")
            c.setFillColor(SUPSOFGOLD); c.setFont(FONT_BODY, 11)
            c.drawCentredString(self.width/2, img_y+img_h/2, "Visit orastria.com")
        trial_y = img_y-50
        c.setFillColor(TEAL); c.roundRect(self.width/2-135, trial_y-10, 270, 34, 17, fill=1, stroke=0)
        c.setFillColor(LIGHT_TEAL); c.roundRect(self.width/2-132, trial_y-7, 264, 28, 14, fill=1, stroke=0)
        c.setFillColor(white); c.setFont(FONT_BODY_BOLD, 13)
        c.drawCentredString(self.width/2, trial_y+1, "FREE 1-MONTH TRIAL INCLUDED")
        fh_y = trial_y-45
        c.setFillColor(GOLD); c.setFont(FONT_HEADING_BOLD, 18)
        c.drawCentredString(self.width/2, fh_y, "Unlock Your Full Cosmic Toolkit")
        c.setStrokeColor(HexColor('#3a4060')); c.setLineWidth(1)
        c.line(self.margin+80, fh_y-12, self.width-self.margin-80, fh_y-12)
        features = [
            ("☉","Daily Personalized Horoscopes", "Readings based on YOUR natal chart"),
            ("☽","Tarot & Oracle Readings",        "Ask any question, receive guidance"),
            ("✧","Dream Interpretation",           "Decode your subconscious messages"),
            ("♫","Sacred Frequencies",             "Healing sounds for transformation"),
            ("★","Master Astral Live Chat",        "24/7 guidance from real advisors"),
            ("◎","Real-Time Planetary Data",       "NASA precision for accuracy"),
        ]
        col_w = 230; gap = 30; total_w = col_w*2+gap
        c1x = (self.width-total_w)/2; c2x = c1x+col_w+gap
        start_y = fh_y-38; row_h = 48
        for i,(icon,title,desc) in enumerate(features):
            x = c1x if i%2==0 else c2x
            fy = start_y - (i//2)*row_h
            c.setFillColor(PURPLE_ICON); c.circle(x+16, fy+6, 18, fill=1, stroke=0)
            c.setFillColor(LIGHT_PURPLE); c.circle(x+16, fy+7, 15, fill=1, stroke=0)
            c.setFillColor(white); c.setFont(FONT_SYMBOL_BOLD, 14); c.drawCentredString(x+16, fy+2, icon)
            c.setFont(FONT_BODY_BOLD, 10); c.drawString(x+40, fy+10, title)
            c.setFillColor(HexColor('#9999aa')); c.setFont(FONT_BODY, 8); c.drawString(x+40, fy-4, desc)
        cta_y = 75
        c.setStrokeColor(HexColor('#3a4060')); c.setLineWidth(0.5)
        c.line(self.margin+100, cta_y+50, self.width-self.margin-100, cta_y+50)
        c.setFillColor(HexColor('#a07d1f')); c.roundRect(self.width/2-112, cta_y-2, 224, 42, 21, fill=1, stroke=0)
        c.setFillColor(GOLD); c.roundRect(self.width/2-110, cta_y, 220, 40, 20, fill=1, stroke=0)
        c.setFillColor(DEEP_NAVY); c.setFont(FONT_BODY_BOLD, 14)
        c.drawCentredString(self.width/2, cta_y+13, "Start Your Free Trial")
        c.linkURL("https://orastria.com/?from=book", (self.width/2-112, cta_y-2, self.width/2+112, cta_y+42))
        c.setFillColor(SUPSOFGOLD); c.setFont(FONT_BODY, 10)
        c.drawCentredString(self.width/2, cta_y-18, "orastria.com")
        c.linkURL("https://orastria.com/?from=book", (self.width/2-50, cta_y-28, self.width/2+50, cta_y-8))
        c.setFillColor(SUPSOFGOLD); c.setFont(FONT_SYMBOL, 10)
        c.drawCentredString(35, 35, '✦'); c.drawCentredString(self.width-35, 35, '✦')
        c.setFillColor(HexColor('#555566')); c.setFont(FONT_BODY, 8)
        c.drawCentredString(self.width/2, 22, "— Your journey continues —")
        c.showPage()

    # ── Build the complete book ──────────────────────────────
    def build(self):
        print(f"\n📖 Building PDF for {self.name}…")

        self.draw_cover()
        self.draw_table_of_contents()
        self.draw_birth_chart_wheel()

        # Glossary only for users who explicitly set beginner level
        familiarity = self.user.get('astrology_familiarity', 'Intermediate')
        if familiarity.lower() in ('beginner', 'new', 'none', 'just starting'):
            self.draw_glossary_page()

        # Introduction
        self.draw_chapter("Introduction", "Your Cosmic Journey Begins")
        y = self.new_page()
        y = self.draw_section_title(f"Welcome, {self.first_name}", y)
        y = self.draw_text(self.content.get('introduction',''), y)
        self.c.showPage()

        # The Big Three
        self.draw_chapter("The Big Three", "Sun, Moon & Rising")

        # Sun
        y = self.new_page()
        self.c.setFillColor(GOLD); self.c.setFont(FONT_SYMBOL_BOLD, 48)
        self.c.drawCentredString(self.width/2, self.height-120, ZODIAC_SYMBOLS.get(self.sun_sign,'★'))
        self.c.setFillColor(NAVY); self.c.setFont(FONT_HEADING_BOLD, 20)
        self.c.drawCentredString(self.width/2, self.height-160, f"Your Sun in {self.sun_sign}")
        y = self.height-200; y = self.draw_text(self.content.get('sun_sign',''), y)
        self.c.showPage()

        # Moon
        y = self.new_page()
        self.c.setFillColor(GOLD); self.c.setFont(FONT_SYMBOL_BOLD, 48)
        self.c.drawCentredString(self.width/2, self.height-120, '☽')
        self.c.setFillColor(NAVY); self.c.setFont(FONT_HEADING_BOLD, 20)
        self.c.drawCentredString(self.width/2, self.height-160, f"Your Moon in {self.moon_sign}")
        y = self.height-200; y = self.draw_text(self.content.get('moon_sign',''), y)
        self.c.showPage()

        # Rising
        y = self.new_page()
        self.c.setFillColor(GOLD); self.c.setFont(FONT_SYMBOL_BOLD, 48)
        self.c.drawCentredString(self.width/2, self.height-120, '↑')
        self.c.setFillColor(NAVY); self.c.setFont(FONT_HEADING_BOLD, 20)
        self.c.drawCentredString(self.width/2, self.height-160, f"Your {self.rising_sign} Rising")
        y = self.height-200; y = self.draw_text(self.content.get('rising_sign',''), y)
        self.c.showPage()

        # Personality
        self.draw_chapter("Your Inner World", "Deep Personality Analysis")
        y = self.new_page()
        y = self.draw_section_title("Understanding Your Psychology", y)
        y = self.draw_text(self.content.get('personality',''), y)
        self.c.showPage()

        # Love
        self.draw_chapter("Love & Relationships", "Your Heart's Blueprint")
        y = self.new_page()
        y = self.draw_section_title("Your Romantic Nature", y)
        y = self.draw_text(self.content.get('love',''), y)
        self.c.showPage()

        # Compatibility
        self.draw_chapter("Compatibility Guide", "Your Match with All 12 Signs")
        y = self.new_page()
        for sign in ZODIAC_ORDER:
            data = self.content.get('compatibility',{}).get(sign, {'text':'','percentage':70})
            y = self.draw_compat_entry(sign, data, y)
        self.c.showPage()

        # Career
        self.draw_chapter("Career & Purpose", "Your Professional Destiny")
        y = self.new_page()
        y = self.draw_section_title("Your Career Blueprint", y)
        y = self.draw_text(self.content.get('career',''), y)
        self.c.showPage()

        # 2026 Forecast
        self.draw_chapter("Your Year Ahead", "2026 Forecast")
        y = self.new_page()
        y = self.draw_section_title("2026 Overview", y)
        y = self.draw_text(self.content.get('forecast',''), y)
        self.c.showPage()

        # Monthly Forecasts
        self.draw_chapter("Monthly Forecasts", "Your 2026 Month-by-Month Guide")
        y = self.new_page()
        for month in ["January","February","March","April","May","June",
                      "July","August","September","October","November","December"]:
            y = self.draw_monthly_entry(month, self.content.get('monthly',{}).get(month,''), y)
        self.c.showPage()

        # Numerology
        self.draw_chapter("Numerology", "The Numbers of Your Life")
        y = self.new_page()
        lp = calculate_life_path(self.user.get('birth_date','2000-01-01'))
        y = self.draw_section_title(f"Life Path {lp}", y)
        y = self.draw_text(self.content.get('numerology',''), y)
        self.c.showPage()

        # Tarot
        self.draw_chapter("Tarot Guidance", "Cards for Your Journey")
        y = self.new_page()
        y = self.draw_section_title("Your Tarot Reading", y)
        y = self.draw_text(self.content.get('tarot',''), y)
        self.c.showPage()

        # Crystals
        self.draw_chapter("Crystals & Rituals", "Tools for Your Path")
        y = self.new_page()
        y = self.draw_section_title("Your Power Crystals", y)
        y = self.draw_text(self.content.get('crystals',''), y)
        self.c.showPage()

        # Summary
        self.draw_summary_page()

        # Closing
        self.draw_chapter("Closing Thoughts", "Your Journey Continues")
        y = self.new_page()
        y = self.draw_section_title(f"Dear {self.first_name},", y)
        y = self.draw_text(self.content.get('closing',''), y)
        y -= 40
        self.c.setFillColor(NAVY); self.c.setFont(FONT_BODY_ITALIC, 14)
        self.c.drawString(self.margin, y, "With cosmic blessings,")
        self.c.setFillColor(GOLD); self.c.setFont(FONT_HEADING_BOLD, 26)
        self.c.drawString(self.margin, y-35, "ORASTRIA")
        self.c.showPage()

        # Upsell (final page)
        self.draw_upsell_page()

        self.c.save()
        print(f"✅ Book saved: {self.output_path}  ({self.page_num} pages)")
        return self.output_path


# ============================================================
# PUBLIC API FUNCTIONS
# ============================================================

def generate_ai_book(user_data, chart_data, output_path):
    """
    Generate complete AI-powered astrology book.
    BACKWARD COMPATIBLE — uses provided chart_data directly.
    """
    ai_gen  = AIContentGenerator(user_data, chart_data)
    content = ai_gen.generate_all()
    book    = OrastriaVisualBook(user_data, chart_data, content, output_path)
    return book.build()


def generate_book(user_data, output_path):
    """
    Primary function for new integrations.
    Fetches chart from Prokerala API; falls back to user-supplied signs if API fails.
    """
    chart_data = None

    if PROKERALA_CLIENT_ID and PROKERALA_CLIENT_SECRET:
        birth_date  = user_data.get('birth_date', '')
        birth_time  = user_data.get('birth_time', '12:00')
        birth_place = user_data.get('birth_place', '')

        # Normalise 12-hour time if birth_time_period is present
        period = user_data.get('birth_time_period', '').upper().strip()
        if period and ':' in birth_time:
            h, mn = birth_time.split(':')[:2]
            hour = int(h)
            if period == 'PM' and hour != 12:
                hour += 12
            elif period == 'AM' and hour == 12:
                hour = 0
            birth_time = f"{hour:02d}:{mn}"

        chart_data = get_chart_from_prokerala(birth_date, birth_time, birth_place)
        if chart_data:
            print(f"✅ Prokerala: Sun={chart_data['sun_sign']} Moon={chart_data['moon_sign']} Rising={chart_data['rising_sign']}")
    else:
        print("⚠️ Prokerala credentials not set — using provided chart data")

    if not chart_data:
        # Use whatever the caller provided, or sensible named defaults
        # We do NOT blindly default everything to 'Aries'
        sun = user_data.get('sun_sign') or ''
        chart_data = {
            'sun_sign':    sun,
            'moon_sign':   user_data.get('moon_sign')   or sun or 'Unknown',
            'rising_sign': user_data.get('rising_sign') or user_data.get('ascendant') or sun or 'Unknown',
            'mercury':     user_data.get('mercury')     or 'Unknown',
            'venus':       user_data.get('venus')       or 'Unknown',
            'mars':        user_data.get('mars')        or 'Unknown',
            'jupiter':     user_data.get('jupiter')     or 'Unknown',
            'saturn':      user_data.get('saturn')      or 'Unknown',
            'midheaven':   user_data.get('midheaven')   or 'Unknown',
            'north_node':  user_data.get('north_node')  or user_data.get('northNode') or 'Unknown',
        }
        print(f"⚠️ Fallback chart: Sun={chart_data['sun_sign']}")

    return generate_ai_book(user_data, chart_data, output_path)


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":
    test_user = {
        "first_name":        "John",
        "last_name":         "Doe",
        "gender":            "male",
        "birth_date":        "1990-05-15",
        "birth_time":        "14:30",
        "birth_place":       "New York, NY, USA",
        "relationship_status": "single",
        "main_goals":        ["improve my relationships"],
        "logic_vs_emotions": "emotions",
        "book_color":        "navy",
        "astrology_familiarity": "Intermediate",
    }
    generate_book(test_user, "/tmp/orastria_test_v7.pdf")
    print("✅ Test complete: /tmp/orastria_test_v7.pdf")
