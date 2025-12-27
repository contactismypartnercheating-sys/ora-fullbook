#!/usr/bin/env python3
"""
Orastria AI-Powered Book Generator v6
- Prokerala API integration for chart calculations
- ALL questionnaire fields for deep personalization
- Visual improvements: Raleway/Garamond fonts, colored compatibility bars, zodiac symbols
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

REPLICATE_URL = os.environ.get('REPLICATE_MODEL_URL', 'https://api.replicate.com/v1/models/anthropic/claude-3.5-sonnet/predictions')
REPLICATE_API_KEY = os.environ.get('REPLICATE_API_KEY', '')

# Prokerala API credentials
PROKERALA_CLIENT_ID = os.environ.get('PROKERALA_CLIENT_ID', '')
PROKERALA_CLIENT_SECRET = os.environ.get('PROKERALA_CLIENT_SECRET', '')

# ============================================================
# FONT MANAGEMENT
# ============================================================

FONT_URLS = {
    'Raleway-Regular.ttf': 'https://cdn.jsdelivr.net/fontsource/fonts/raleway@latest/latin-400-normal.ttf',
    'Raleway-Bold.ttf': 'https://cdn.jsdelivr.net/fontsource/fonts/raleway@latest/latin-700-normal.ttf',
    'Raleway-Italic.ttf': 'https://cdn.jsdelivr.net/fontsource/fonts/raleway@latest/latin-400-italic.ttf',
    'EBGaramond-Regular.ttf': 'https://cdn.jsdelivr.net/fontsource/fonts/eb-garamond@latest/latin-400-normal.ttf',
    'EBGaramond-Bold.ttf': 'https://cdn.jsdelivr.net/fontsource/fonts/eb-garamond@latest/latin-700-normal.ttf',
    'DejaVuSans.ttf': 'https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf/DejaVuSans.ttf',
    'DejaVuSans-Bold.ttf': 'https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf/DejaVuSans-Bold.ttf',
}

def ensure_fonts():
    """Download and register fonts"""
    if os.path.exists('/app'):
        font_dir = '/app/fonts'
    else:
        font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
    
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
        'Raleway': 'Raleway-Regular.ttf',
        'Raleway-Bold': 'Raleway-Bold.ttf',
        'Raleway-Italic': 'Raleway-Italic.ttf',
        'EBGaramond': 'EBGaramond-Regular.ttf',
        'EBGaramond-Bold': 'EBGaramond-Bold.ttf',
        'DejaVuSans': 'DejaVuSans.ttf',
        'DejaVuSans-Bold': 'DejaVuSans-Bold.ttf',
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

FONT_BODY = 'Raleway' if 'Raleway' in FONTS else 'Helvetica'
FONT_BODY_BOLD = 'Raleway-Bold' if 'Raleway-Bold' in FONTS else 'Helvetica-Bold'
FONT_BODY_ITALIC = 'Raleway-Italic' if 'Raleway-Italic' in FONTS else 'Helvetica-Oblique'
FONT_HEADING = 'EBGaramond' if 'EBGaramond' in FONTS else 'Times-Roman'
FONT_HEADING_BOLD = 'EBGaramond-Bold' if 'EBGaramond-Bold' in FONTS else 'Times-Bold'
FONT_SYMBOL = 'DejaVuSans' if 'DejaVuSans' in FONTS else 'Helvetica'
FONT_SYMBOL_BOLD = 'DejaVuSans-Bold' if 'DejaVuSans-Bold' in FONTS else 'Helvetica-Bold'

print(f"Using fonts: Body={FONT_BODY}, Heading={FONT_HEADING}, Symbol={FONT_SYMBOL}")

# ============================================================
# COLORS
# ============================================================

NAVY = HexColor('#1a1f3c')
GOLD = HexColor('#c9a961')
CREAM = HexColor('#f8f5f0')
SOFT_GOLD = HexColor('#d4b87a')
LIGHT_NAVY = HexColor('#2d3561')

GREEN = HexColor('#2ecc71')
YELLOW = HexColor('#f1c40f')
ORANGE = HexColor('#e67e22')
RED = HexColor('#e74c3c')
LIGHT_GRAY = HexColor('#ecf0f1')

# Book color themes
COLOR_THEMES = {
    'black': {'primary': HexColor('#1a1a1a'), 'accent': GOLD},
    'green': {'primary': HexColor('#1a3c2a'), 'accent': HexColor('#c9d961')},
    'dark purple': {'primary': HexColor('#2a1a3c'), 'accent': HexColor('#c9a9d1')},
    'brighter black': {'primary': HexColor('#2a2a2a'), 'accent': GOLD},
    'red': {'primary': HexColor('#3c1a1a'), 'accent': HexColor('#d9c961')},
    'creamy': {'primary': HexColor('#f5f0e6'), 'accent': HexColor('#8b7355')},
    'maroon': {'primary': HexColor('#722F37'), 'accent': GOLD},
    'navy': {'primary': NAVY, 'accent': GOLD},
}

# ============================================================
# ZODIAC DATA
# ============================================================

ZODIAC_SYMBOLS = {
    'Aries': '♈', 'Taurus': '♉', 'Gemini': '♊', 'Cancer': '♋',
    'Leo': '♌', 'Virgo': '♍', 'Libra': '♎', 'Scorpio': '♏',
    'Sagittarius': '♐', 'Capricorn': '♑', 'Aquarius': '♒', 'Pisces': '♓'
}

ZODIAC_ORDER = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

ZODIAC_DATA = {
    "Aries": {"element": "Fire", "modality": "Cardinal", "ruler": "Mars", "crystal": "Carnelian"},
    "Taurus": {"element": "Earth", "modality": "Fixed", "ruler": "Venus", "crystal": "Rose Quartz"},
    "Gemini": {"element": "Air", "modality": "Mutable", "ruler": "Mercury", "crystal": "Citrine"},
    "Cancer": {"element": "Water", "modality": "Cardinal", "ruler": "Moon", "crystal": "Moonstone"},
    "Leo": {"element": "Fire", "modality": "Fixed", "ruler": "Sun", "crystal": "Tiger's Eye"},
    "Virgo": {"element": "Earth", "modality": "Mutable", "ruler": "Mercury", "crystal": "Green Aventurine"},
    "Libra": {"element": "Air", "modality": "Cardinal", "ruler": "Venus", "crystal": "Lapis Lazuli"},
    "Scorpio": {"element": "Water", "modality": "Fixed", "ruler": "Pluto", "crystal": "Black Obsidian"},
    "Sagittarius": {"element": "Fire", "modality": "Mutable", "ruler": "Jupiter", "crystal": "Turquoise"},
    "Capricorn": {"element": "Earth", "modality": "Cardinal", "ruler": "Saturn", "crystal": "Garnet"},
    "Aquarius": {"element": "Air", "modality": "Fixed", "ruler": "Uranus", "crystal": "Amethyst"},
    "Pisces": {"element": "Water", "modality": "Mutable", "ruler": "Neptune", "crystal": "Aquamarine"}
}

# ============================================================
# PROKERALA API INTEGRATION (matching working sample book)
# ============================================================

ZODIAC_SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

# Ayanamsa offset (Lahiri) - converts from Sidereal to Tropical
AYANAMSA = 24.0


def get_prokerala_token():
    """Get OAuth token from Prokerala - EXACT working version"""
    # Debug: show credential info
    print(f"🔑 CLIENT_ID: '{PROKERALA_CLIENT_ID[:8]}...{PROKERALA_CLIENT_ID[-4:]}' (len={len(PROKERALA_CLIENT_ID)})")
    print(f"🔑 CLIENT_SECRET: '{PROKERALA_CLIENT_SECRET[:8]}...{PROKERALA_CLIENT_SECRET[-4:]}' (len={len(PROKERALA_CLIENT_SECRET)})")
    
    # Check for hidden characters
    if '\n' in PROKERALA_CLIENT_ID or '\r' in PROKERALA_CLIENT_ID:
        print("⚠️ CLIENT_ID contains line breaks!")
    if '\n' in PROKERALA_CLIENT_SECRET or '\r' in PROKERALA_CLIENT_SECRET:
        print("⚠️ CLIENT_SECRET contains line breaks!")
    if ' ' in PROKERALA_CLIENT_ID or ' ' in PROKERALA_CLIENT_SECRET:
        print("⚠️ Credentials contain spaces!")
    
    url = "https://api.prokerala.com/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': PROKERALA_CLIENT_ID,
        'client_secret': PROKERALA_CLIENT_SECRET
    }
    
    print(f"📤 Requesting token from: {url}")
    
    response = requests.post(url, data=data)
    
    print(f"📥 Response status: {response.status_code}")
    if response.status_code != 200:
        print(f"📥 Response body: {response.text[:500]}")
    
    response.raise_for_status()
    return response.json()['access_token']


def get_timezone_from_coords(lat, lon, place_name):
    """Get timezone from coordinates using timezonefinder library"""
    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        timezone = tf.timezone_at(lat=lat, lng=lon)
        if timezone:
            print(f"✅ Timezone found: {timezone}")
            return timezone
    except ImportError:
        print("⚠️ timezonefinder not installed, using fallback")
    except Exception as e:
        print(f"⚠️ timezonefinder error: {e}")
    
    # Fallback to guess
    return guess_timezone_from_coords(lat, lon, place_name)


def geocode_location(place_name):
    """Get latitude, longitude, and timezone for a place using Nominatim"""
    # Using Nominatim (free, no API key needed)
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': place_name,
        'format': 'json',
        'limit': 1
    }
    headers = {'User-Agent': 'OrastriaApp/1.0'}
    
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    
    results = response.json()
    if not results:
        raise ValueError(f"Could not find location: {place_name}")
    
    lat = float(results[0]['lat'])
    lon = float(results[0]['lon'])
    
    # Get timezone reliably
    timezone = get_timezone_from_coords(lat, lon, place_name)
    print(f"📍 Location: {lat}, {lon} → {timezone}")
    
    return lat, lon, timezone


def guess_timezone_from_coords(lat, lon, place_name):
    """Guess timezone based on coordinates and place name"""
    place_lower = place_name.lower()
    
    # Check place name for known locations
    if 'paris' in place_lower or 'france' in place_lower:
        return 'Europe/Paris'
    if 'london' in place_lower or 'uk' in place_lower or 'england' in place_lower:
        return 'Europe/London'
    if 'new york' in place_lower:
        return 'America/New_York'
    if 'los angeles' in place_lower or 'california' in place_lower:
        return 'America/Los_Angeles'
    if 'chicago' in place_lower:
        return 'America/Chicago'
    if 'dubai' in place_lower or 'uae' in place_lower:
        return 'Asia/Dubai'
    if 'tokyo' in place_lower or 'japan' in place_lower:
        return 'Asia/Tokyo'
    if 'sydney' in place_lower or 'australia' in place_lower:
        return 'Australia/Sydney'
    if 'berlin' in place_lower or 'germany' in place_lower:
        return 'Europe/Berlin'
    if 'rome' in place_lower or 'italy' in place_lower:
        return 'Europe/Rome'
    if 'madrid' in place_lower or 'spain' in place_lower:
        return 'Europe/Madrid'
    if 'moscow' in place_lower or 'russia' in place_lower:
        return 'Europe/Moscow'
    if 'beijing' in place_lower or 'china' in place_lower:
        return 'Asia/Shanghai'
    if 'india' in place_lower or 'mumbai' in place_lower or 'delhi' in place_lower:
        return 'Asia/Kolkata'
    if 'beirut' in place_lower or 'lebanon' in place_lower:
        return 'Asia/Beirut'
    
    # Rough guess based on longitude
    if lon < -100:
        return 'America/Los_Angeles'
    elif lon < -60:
        return 'America/New_York'
    elif lon < 0:
        return 'Europe/London'
    elif lon < 30:
        return 'Europe/Paris'
    elif lon < 60:
        return 'Asia/Dubai'
    elif lon < 100:
        return 'Asia/Kolkata'
    elif lon < 130:
        return 'Asia/Shanghai'
    else:
        return 'Asia/Tokyo'


def get_tz_offset(timezone):
    """Get timezone offset string like +03:00"""
    offsets = {
        'Asia/Beirut': '+02:00',
        'America/New_York': '-05:00',
        'America/Chicago': '-06:00',
        'America/Los_Angeles': '-08:00',
        'America/Denver': '-07:00',
        'Europe/London': '+00:00',
        'Europe/Paris': '+01:00',
        'Europe/Berlin': '+01:00',
        'Europe/Rome': '+01:00',
        'Europe/Madrid': '+01:00',
        'Europe/Moscow': '+03:00',
        'Asia/Dubai': '+04:00',
        'Asia/Kolkata': '+05:30',
        'Asia/Shanghai': '+08:00',
        'Asia/Tokyo': '+09:00',
        'Australia/Sydney': '+11:00',
        'Pacific/Auckland': '+13:00',
        'UTC': '+00:00'
    }
    return offsets.get(timezone, '+00:00')


def longitude_to_tropical_sign(longitude):
    """Convert longitude to tropical/Western zodiac sign"""
    tropical_longitude = (longitude + AYANAMSA) % 360
    sign_index = int(tropical_longitude / 30)
    return ZODIAC_SIGNS[sign_index]


def get_birth_chart(birth_date, birth_time, latitude, longitude, timezone):
    """Get birth chart from Prokerala API - EXACT working version"""
    token = get_prokerala_token()
    
    datetime_str = f"{birth_date}T{birth_time}:00{get_tz_offset(timezone)}"
    
    url = "https://api.prokerala.com/v2/astrology/planet-position"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "ayanamsa": 1,
        "coordinates": f"{latitude},{longitude}",
        "datetime": datetime_str
    }
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()['data']
    
    # Also get the ascendant/rising sign
    asc_url = "https://api.prokerala.com/v2/astrology/kundli"
    asc_response = requests.get(asc_url, headers=headers, params=params, timeout=30)
    asc_data = asc_response.json()['data'] if asc_response.ok else None
    
    return parse_chart_data(data, asc_data)


def parse_chart_data(planet_data, kundli_data):
    """Parse Prokerala response into our format - converts to Western/Tropical zodiac"""
    
    chart = {
        'sun_sign': 'Aries',
        'moon_sign': 'Aries',
        'rising_sign': 'Aries',
        'mercury': 'Aries',
        'venus': 'Aries',
        'mars': 'Aries',
        'jupiter': 'Aries',
        'saturn': 'Aries',
        'midheaven': 'Aries',
        'north_node': 'Aries',
    }
    
    planet_name_map = {
        'Sun': 'sun_sign',
        'Moon': 'moon_sign',
        'Mercury': 'mercury',
        'Venus': 'venus',
        'Mars': 'mars',
        'Jupiter': 'jupiter',
        'Saturn': 'saturn',
        'Rahu': 'north_node',
        'Ascendant': 'rising_sign'
    }
    
    # Parse planet positions
    planets = planet_data.get('planet_position', [])
    
    for planet in planets:
        planet_name = planet.get('name', '')
        longitude = planet.get('longitude', 0)
        
        if longitude > 0:
            sign_name = longitude_to_tropical_sign(longitude)
        else:
            rasi = planet.get('rasi', {})
            rasi_id = rasi.get('id', -1)
            if 0 <= rasi_id < 12:
                tropical_rasi_id = (rasi_id + 1) % 12
                sign_name = ZODIAC_SIGNS[tropical_rasi_id]
            else:
                sign_name = 'Aries'
        
        if planet_name in planet_name_map:
            chart[planet_name_map[planet_name]] = sign_name
    
    # Get rising sign from kundli data if available
    if kundli_data:
        ascendant = kundli_data.get('ascendant', {})
        if ascendant:
            asc_longitude = ascendant.get('longitude', 0)
            if asc_longitude > 0:
                chart['rising_sign'] = longitude_to_tropical_sign(asc_longitude)
    
    return chart


def get_chart_from_prokerala(birth_date, birth_time, birth_place):
    """Get complete chart data from Prokerala API"""
    if not PROKERALA_CLIENT_ID or not PROKERALA_CLIENT_SECRET:
        print("Prokerala credentials not configured")
        return None
    
    try:
        print(f"📍 Geocoding: {birth_place}")
        latitude, longitude, timezone = geocode_location(birth_place)
        print(f"✅ Location: {latitude}, {longitude} (TZ: {timezone})")
        
        print(f"🔮 Fetching chart from Prokerala...")
        chart = get_birth_chart(birth_date, birth_time, latitude, longitude, timezone)
        print(f"✅ Chart received: Sun={chart['sun_sign']}, Moon={chart['moon_sign']}, Rising={chart['rising_sign']}")
        
        return chart
        
    except Exception as e:
        print(f"❌ Prokerala error: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================
# NUMEROLOGY
# ============================================================

def calculate_life_path(birth_date):
    try:
        if "-" in birth_date:
            parts = birth_date.split("-")
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        else:
            dt = datetime.strptime(birth_date, "%B %d, %Y")
            year, month, day = dt.year, dt.month, dt.day
        
        total = sum(int(d) for d in str(year)) + sum(int(d) for d in str(month)) + sum(int(d) for d in str(day))
        
        while total > 9 and total not in [11, 22, 33]:
            total = sum(int(d) for d in str(total))
        
        return total
    except:
        return 7

def calculate_expression_number(name):
    letter_values = {
        'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8, 'i': 9,
        'j': 1, 'k': 2, 'l': 3, 'm': 4, 'n': 5, 'o': 6, 'p': 7, 'q': 8, 'r': 9,
        's': 1, 't': 2, 'u': 3, 'v': 4, 'w': 5, 'x': 6, 'y': 7, 'z': 8
    }
    total = sum(letter_values.get(c.lower(), 0) for c in name if c.isalpha())
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(d) for d in str(total))
    return total

# ============================================================
# AI CONTENT GENERATION
# ============================================================

def call_claude_api(prompt, max_tokens=1500):
    """Call Claude API via Replicate"""
    headers = {
        "Authorization": f"Bearer {REPLICATE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "prompt": prompt,
            "max_tokens": max_tokens
        }
    }
    
    try:
        response = requests.post(REPLICATE_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        prediction = response.json()
        
        prediction_url = prediction.get("urls", {}).get("get")
        if not prediction_url:
            return None
        
        for _ in range(90):
            time.sleep(1)
            result = requests.get(prediction_url, headers=headers, timeout=30)
            result_data = result.json()
            
            status = result_data.get("status")
            if status == "succeeded":
                output = result_data.get("output", "")
                if isinstance(output, list):
                    return "".join(output)
                return output
            elif status == "failed":
                return None
        
        return None
        
    except Exception as e:
        print(f"API Error: {e}")
        return None


class AIContentGenerator:
    """Generate personalized AI content using ALL questionnaire data"""
    
    def __init__(self, user_data, chart_data):
        self.user = user_data
        self.chart = chart_data
        
        # Handle both 'name' and 'first_name' fields
        self.name = user_data.get("name") or f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or "Friend"
        self.first_name = user_data.get("first_name") or self.name.split()[0]
        
        self.sun_sign = chart_data.get("sun_sign", "Aries")
        self.moon_sign = chart_data.get("moon_sign", "Aries")
        self.rising_sign = chart_data.get("rising_sign", "Aries")
        self.life_path = calculate_life_path(user_data.get("birth_date", "2000-01-01"))
        self.expression_number = calculate_expression_number(self.name)
        self.content = {}
    
    def _build_context(self):
        """Build comprehensive context string with ALL user data"""
        def format_list(items):
            if isinstance(items, list):
                return ", ".join(items) if items else "Not specified"
            return items or "Not specified"
        
        return f"""
=== PERSONAL PROFILE ===
Name: {self.name}
Gender: {self.user.get('gender', 'Not specified')}
Birth: {self.user.get('birth_date')} at {self.user.get('birth_time')} {self.user.get('birth_time_period', '')}
Place: {self.user.get('birth_place')}

=== ASTROLOGICAL CHART ===
Sun: {self.sun_sign} ({ZODIAC_DATA.get(self.sun_sign, {}).get('element', '')} element)
Moon: {self.moon_sign} ({ZODIAC_DATA.get(self.moon_sign, {}).get('element', '')} element)
Rising: {self.rising_sign} ({ZODIAC_DATA.get(self.rising_sign, {}).get('element', '')} element)
Venus: {self.chart.get('venus', 'Unknown')}
Mars: {self.chart.get('mars', 'Unknown')}
Mercury: {self.chart.get('mercury', 'Unknown')}
Jupiter: {self.chart.get('jupiter', 'Unknown')}
Saturn: {self.chart.get('saturn', 'Unknown')}
Midheaven: {self.chart.get('midheaven', 'Unknown')}
North Node: {self.chart.get('north_node', 'Unknown')}

=== ASTROLOGY KNOWLEDGE ===
Familiarity: {self.user.get('astrology_familiarity', 'Beginner')}

=== GOALS & MOTIVATIONS ===
Main Goals: {format_list(self.user.get('main_goals'))}
Life Dreams: {self.user.get('life_dreams', 'Not specified')}
Motivations: {self.user.get('motivations', 'Not specified')}

=== RELATIONSHIP STATUS ===
Status: {self.user.get('relationship_status', 'Not specified')}
Goals: {format_list(self.user.get('relationship_goals'))}
Satisfaction: {self.user.get('relationship_satisfaction', 'N/A')}
Unresolved Feelings: {self.user.get('unresolved_romantic_feelings', 'No')}

=== PERSONALITY ===
Outlook: {self.user.get('outlook', 'Realist')}
Decision Worry: {self.user.get('decision_worry', 'Not specified')}
Need to be Liked: {self.user.get('need_to_be_liked', 'Sometimes')}
Insecurity with Strangers: {self.user.get('insecurity_with_strangers', 'Not specified')}

=== LOVE & RELATIONSHIPS ===
Love Language: {self.user.get('love_language', 'Not specified')}
Logic vs Emotions: {self.user.get('logic_vs_emotions', 'A bit of both')}
Overthink Relationships: {self.user.get('overthink_relationships', 'Sometimes')}
Desired Partner Traits: {format_list(self.user.get('desired_partner_traits'))}

=== CAREER ===
Career Question: {self.user.get('career_question', 'Finding fulfillment')}

=== BOOK PREFERENCES ===
Birth Chart Includes: {format_list(self.user.get('birth_chart_includes'))}
Important Dates: {format_list(self.user.get('important_dates'))}
Additional Topics: {format_list(self.user.get('additional_topics'))}

=== LIFE EVENTS ===
Significant Event Soon: {self.user.get('significant_life_event_soon', 'No')}

=== NUMEROLOGY ===
Life Path: {self.life_path}
Expression Number: {self.expression_number}
"""
    
    def generate_section(self, section_name, prompt, max_tokens=1500):
        print(f"  Generating: {section_name}...")
        
        # Determine formatting based on familiarity level
        familiarity = self.user.get('astrology_familiarity', 'Beginner')
        is_beginner = familiarity.lower() in ['beginner', 'new', 'none', 'just starting']
        
        formatting_instructions = """
FORMATTING REQUIREMENTS:
- Use SHORT paragraphs (3-4 sentences max)
- Break up long explanations with line breaks
- Make it scannable and easy to read
- Avoid walls of text"""
        
        if is_beginner:
            formatting_instructions += """
- When using astrology terms, briefly explain what they mean in parentheses
- Example: "Your Midheaven (the highest point in your chart, representing career and public image) is in Aries"
- Keep language accessible and warm, not overly technical"""
        
        full_prompt = f"""{prompt}

Context:
{self._build_context()}

IMPORTANT: 
- Write in second person ("you")
- Reference their specific quiz answers and personality traits
- Make it feel like a personal reading, not generic astrology
- Be warm, insightful, and specific to THIS person
- Their astrology knowledge level is: {familiarity}
{formatting_instructions}"""
        
        result = call_claude_api(full_prompt, max_tokens)
        self.content[section_name] = result or self._get_fallback(section_name)
        return self.content[section_name]
    
    def _get_fallback(self, section):
        fallbacks = {
            'introduction': f"Dear {self.first_name}, welcome to your personalized cosmic blueprint...",
            'sun_sign': f"As a {self.sun_sign} Sun, you embody {ZODIAC_DATA[self.sun_sign]['element']} energy...",
            'moon_sign': f"Your {self.moon_sign} Moon shapes your emotional world...",
            'rising_sign': f"With {self.rising_sign} Rising, you present yourself with {ZODIAC_DATA[self.rising_sign]['element']} energy...",
            'personality': f"Your unique blend of {self.sun_sign}, {self.moon_sign}, and {self.rising_sign} creates a fascinating personality...",
            'love': f"In matters of love, your Venus placement guides your heart...",
            'career': f"Your professional path is illuminated by your natural talents...",
            'forecast': f"2026 brings significant opportunities for growth...",
            'numerology': f"Your Life Path {self.life_path} reveals your soul's journey...",
            'tarot': f"The tarot offers guidance for your path ahead...",
            'crystals': f"Certain crystals resonate with your unique energy...",
            'important_dates': f"Key cosmic dates are highlighted for your journey...",
            'closing': f"Dear {self.first_name}, may the stars guide your journey..."
        }
        return fallbacks.get(section, "Content for this section...")
    
    def generate_all(self):
        print(f"\n🌟 Generating AI content for {self.name}...")
        print("=" * 50)
        
        # Get user's content preferences
        additional_topics = self.user.get('additional_topics', [])
        important_dates = self.user.get('important_dates', [])
        
        # Core sections with enhanced prompts using ALL data
        sections = [
            ('introduction', f"""Write a warm, personalized introduction (4-5 paragraphs, ~500 words).
Include:
1. Welcome them by name ({self.first_name})
2. Reference their specific main goals: {self.user.get('main_goals')}
3. Acknowledge their astrology knowledge level ({self.user.get('astrology_familiarity')})
4. Mention if they have a significant life event coming: {self.user.get('significant_life_event_soon')}
5. Make them feel this book was written just for them"""),
            
            ('sun_sign', f"""Write comprehensive {self.sun_sign} Sun analysis (5-6 paragraphs, ~600 words).
Include:
1. The essence of {self.sun_sign} energy
2. How it connects to their outlook: {self.user.get('outlook')}
3. How their dreams ("{self.user.get('life_dreams')}") align with {self.sun_sign} traits
4. {self.sun_sign} strengths and shadows
5. How it interacts with their {self.moon_sign} Moon and {self.rising_sign} Rising"""),
            
            ('moon_sign', f"""Write deep {self.moon_sign} Moon analysis (5-6 paragraphs, ~600 words).
Include:
1. Their emotional nature as a {self.moon_sign} Moon
2. What they need to feel secure
3. How they process emotions - connect to: {self.user.get('logic_vs_emotions')}
4. Their tendency to overthink: {self.user.get('overthink_relationships')}
5. How {self.moon_sign} Moon shapes their love language: {self.user.get('love_language')}"""),
            
            ('rising_sign', f"""Write about {self.rising_sign} Rising (4-5 paragraphs, ~500 words).
Include:
1. How others perceive them
2. Their public persona
3. Connect to insecurity with strangers: "{self.user.get('insecurity_with_strangers')}"
4. How it relates to need to be liked: {self.user.get('need_to_be_liked')}
5. Using this Rising energy effectively"""),
            
            ('personality', f"""Write extensive personality analysis (6-7 paragraphs, ~700 words).
Analyze EACH of these:
1. Outlook: {self.user.get('outlook')} - how it manifests
2. Decision Worry: "{self.user.get('decision_worry')}" - what this reveals
3. Need for Approval: {self.user.get('need_to_be_liked')} - roots and effects
4. Social Comfort: "{self.user.get('insecurity_with_strangers')}" - connect to Rising
5. Logic vs Emotions: {self.user.get('logic_vs_emotions')}
6. Dreams: "{self.user.get('life_dreams')}"
7. Motivations: "{self.user.get('motivations')}"
Weave all together into a cohesive portrait."""),
            
            ('love', f"""Write comprehensive love analysis (6-7 paragraphs, ~700 words).
Context:
- Status: {self.user.get('relationship_status')}
- Goals: {self.user.get('relationship_goals')}
- Unresolved feelings: {self.user.get('unresolved_romantic_feelings')}
Include:
1. Venus in {self.chart.get('venus', 'Unknown')} - how they love
2. Mars in {self.chart.get('mars', 'Unknown')} - passion style
3. Their love language ({self.user.get('love_language')}) explained astrologically
4. Why they overthink ({self.user.get('overthink_relationships')})
5. Desired partner traits: {self.user.get('desired_partner_traits')}
6. Specific guidance for their situation"""),
            
            ('career', f"""Write career and purpose analysis (6-7 paragraphs, ~700 words).
Their question: "{self.user.get('career_question')}"
Include:
1. Midheaven in {self.chart.get('midheaven', 'Unknown')} - career image
2. {self.sun_sign} professional strengths
3. Saturn in {self.chart.get('saturn', 'Unknown')} - lessons
4. North Node purpose direction
5. DIRECTLY answer their career question
6. Connect dreams "{self.user.get('life_dreams')}" to career paths"""),
            
            ('forecast', f"""Write 2026 yearly forecast (6-7 paragraphs, ~700 words).
Include:
1. Overall 2026 theme
2. Major planetary transits
3. Career and financial outlook
4. Love predictions
5. If significant event coming ({self.user.get('significant_life_event_soon')}), weave in guidance
6. Specific month references"""),
            
            ('numerology', f"""Write numerology analysis (5-6 paragraphs, ~600 words).
Numbers: Life Path {self.life_path}, Expression {self.expression_number}
Include:
1. Life Path meaning for them
2. Expression Number talents
3. How numbers complement their chart
4. Personal year number for 2026"""),
            
            ('tarot', f"""Write tarot section (5-6 paragraphs, ~600 words).
Include:
1. Birth cards for Sun ({self.sun_sign}), Moon ({self.moon_sign}), Rising ({self.rising_sign})
2. What each birth card means
3. Custom 5-card spread for their goals: {self.user.get('main_goals')}
4. Interpret each card for their situation
5. Overall message"""),
            
            ('crystals', f"""Write crystals and rituals section (5-6 paragraphs, ~600 words).
Include:
1. 5-7 power crystals for:
   - Sun in {self.sun_sign}
   - Moon in {self.moon_sign}
   - Venus in {self.chart.get('venus', 'Unknown')}
2. Why each resonates with their energy
3. New moon ritual for {self.sun_sign}
4. Full moon ritual for {self.moon_sign}
5. Daily grounding practice"""),
            
            ('closing', f"""Write warm closing (4-5 paragraphs, ~500 words).
Include:
1. Summarize their unique cosmic blueprint
2. Reference their goals ({self.user.get('main_goals')})
3. Acknowledge their journey
4. If significant event coming, wish them well
5. Personalized blessing referencing Sun/Moon/Rising"""),
        ]
        
        for section_name, prompt in sections:
            self.generate_section(section_name, prompt)
        
        # Important dates section (if user selected any)
        if important_dates:
            self.generate_section('important_dates', f"""They want to know these important dates:
{important_dates}

Write a section (4-5 paragraphs, ~500 words) addressing EACH date request:
- Provide specific date ranges or periods in 2026
- Explain astrological reasoning
- Give practical advice for these times""")
        
        # Batch compatibility
        print("  Generating: compatibility (batched)...")
        self.content['compatibility'] = {}
        
        for batch_start in [0, 6]:
            signs_batch = ZODIAC_ORDER[batch_start:batch_start+6]
            prompt = f"""Write compatibility for {self.sun_sign} with: {', '.join(signs_batch)}.

Consider their desired partner traits: {self.user.get('desired_partner_traits')}

For EACH sign, write 2 paragraphs (~150 words) and include PERCENTAGE: XX%

Format:
{signs_batch[0].upper()}:
[content]
PERCENTAGE: XX%

{signs_batch[1].upper()}:
[content]
PERCENTAGE: XX%

(continue for all 6 signs)"""
            
            result = call_claude_api(f"{prompt}\n\n{self._build_context()}", max_tokens=2500)
            if result:
                self._parse_compat(result, signs_batch)
        
        for sign in ZODIAC_ORDER:
            if sign not in self.content['compatibility']:
                self.content['compatibility'][sign] = {
                    'text': f"{self.sun_sign} and {sign} create a unique dynamic...",
                    'percentage': 70
                }
        
        # Batch monthly
        print("  Generating: monthly forecasts (batched)...")
        self.content['monthly'] = {}
        
        all_months = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        
        for batch_start in [0, 6]:
            months_batch = all_months[batch_start:batch_start+6]
            prompt = f"""Write 2026 monthly forecasts for: {', '.join(months_batch)}.

Consider their goals: {self.user.get('main_goals')}
Relationship status: {self.user.get('relationship_status')}

For EACH month, write 2 paragraphs (~150 words).

Format:
{months_batch[0].upper()}:
[content]

{months_batch[1].upper()}:
[content]

(continue for all 6 months)"""
            
            result = call_claude_api(f"{prompt}\n\n{self._build_context()}", max_tokens=2500)
            if result:
                self._parse_monthly(result, months_batch)
        
        for month in all_months:
            if month not in self.content['monthly']:
                self.content['monthly'][month] = f"{month} 2026 brings transformation and growth..."
        
        print("=" * 50)
        print("✅ All AI content generated!")
        return self.content
    
    def _parse_compat(self, text, signs):
        import re
        for sign in signs:
            pattern = rf'{sign.upper()}:\s*(.*?)(?=PERCENTAGE:\s*(\d+))'
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                percentage = int(match.group(2)) if match.group(2) else 70
                self.content['compatibility'][sign] = {
                    'text': content,
                    'percentage': percentage
                }
            else:
                simple_pattern = rf'{sign.upper()}:\s*(.*?)(?=(?:ARIES|TAURUS|GEMINI|CANCER|LEO|VIRGO|LIBRA|SCORPIO|SAGITTARIUS|CAPRICORN|AQUARIUS|PISCES):|\Z)'
                simple_match = re.search(simple_pattern, text, re.DOTALL | re.IGNORECASE)
                if simple_match:
                    content = simple_match.group(1).strip()
                    pct_match = re.search(r'(\d+)%', content)
                    percentage = int(pct_match.group(1)) if pct_match else 70
                    self.content['compatibility'][sign] = {
                        'text': content,
                        'percentage': percentage
                    }
    
    def _parse_monthly(self, text, months):
        import re
        for month in months:
            pattern = rf'{month.upper()}:\s*(.*?)(?=(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER):|\Z)'
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                self.content['monthly'][month] = match.group(1).strip()


# ============================================================
# PDF BOOK GENERATOR
# ============================================================

class OrastriaVisualBook:
    """Generate beautiful PDF book"""
    
    def __init__(self, user_data, chart_data, ai_content, output_path):
        self.user = user_data
        self.chart = chart_data
        self.content = ai_content
        self.output_path = output_path
        
        self.width, self.height = letter
        self.margin = 0.75 * inch
        self.page_num = 0
        self.c = canvas.Canvas(output_path, pagesize=letter)
        
        # Handle both 'name' and 'first_name' fields
        self.name = user_data.get("name") or f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or "Friend"
        self.first_name = user_data.get("first_name") or self.name.split()[0]
        
        self.sun_sign = chart_data.get("sun_sign", "Aries")
        self.moon_sign = chart_data.get("moon_sign", "Aries")
        self.rising_sign = chart_data.get("rising_sign", "Aries")
        
        # Get color theme
        color_choice = user_data.get('book_color', 'navy').lower()
        self.theme = COLOR_THEMES.get(color_choice, COLOR_THEMES['navy'])
        self.primary_color = self.theme.get('primary', NAVY)
        self.accent_color = self.theme.get('accent', GOLD)
        
        # Parse birth date
        bd = user_data.get("birth_date", "2000-01-01")
        if "-" in bd:
            parts = bd.split("-")
            months = ["", "January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
            self.birth_date_formatted = f"{months[int(parts[1])]} {int(parts[2])}, {parts[0]}"
        else:
            self.birth_date_formatted = bd
    
    def get_compat_color(self, percentage):
        """Get color based on compatibility percentage"""
        if percentage >= 80:
            return GREEN
        elif percentage >= 65:
            return YELLOW
        elif percentage >= 50:
            return ORANGE
        else:
            return RED
    
    def draw_cover(self):
        """Draw beautiful cover"""
        c = self.c
        
        c.setFillColor(self.primary_color)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        
        c.setStrokeColor(self.accent_color)
        c.setLineWidth(2)
        c.rect(0.4*inch, 0.4*inch, self.width - 0.8*inch, self.height - 0.8*inch)
        c.setLineWidth(1)
        c.rect(0.5*inch, 0.5*inch, self.width - 1*inch, self.height - 1*inch)
        
        c.setFont(FONT_SYMBOL_BOLD, 24)
        c.setFillColor(self.accent_color)
        c.drawCentredString(0.8*inch, self.height - 0.8*inch, '☉')
        c.drawCentredString(self.width - 0.8*inch, self.height - 0.8*inch, '☽')
        
        c.setFont(FONT_HEADING_BOLD, 36)
        c.drawCentredString(self.width/2, self.height - 1.8*inch, "YOUR COSMIC")
        c.drawCentredString(self.width/2, self.height - 2.3*inch, "BLUEPRINT")
        
        c.setLineWidth(1)
        c.line(2*inch, self.height - 2.55*inch, self.width - 2*inch, self.height - 2.55*inch)
        
        c.setFillColor(white)
        c.setFont(FONT_HEADING_BOLD, 28)
        c.drawCentredString(self.width/2, self.height - 3.2*inch, self.name)
        
        c.setFillColor(SOFT_GOLD)
        c.setFont(FONT_BODY, 12)
        birth_time = f"{self.user.get('birth_time', '')} {self.user.get('birth_time_period', '')}".strip()
        c.drawCentredString(self.width/2, self.height - 3.6*inch, f"{self.birth_date_formatted}  •  {birth_time}")
        c.drawCentredString(self.width/2, self.height - 3.85*inch, self.user.get('birth_place', ''))
        
        center_y = self.height / 2 - 0.3*inch
        c.setStrokeColor(self.accent_color)
        c.setLineWidth(2)
        c.circle(self.width/2, center_y, 85)
        c.setLineWidth(1)
        c.circle(self.width/2, center_y, 95)
        
        c.setFillColor(self.accent_color)
        c.setFont(FONT_SYMBOL_BOLD, 72)
        c.drawCentredString(self.width/2, center_y - 15, ZODIAC_SYMBOLS.get(self.sun_sign, '★'))
        
        c.setFont(FONT_HEADING_BOLD, 18)
        c.drawCentredString(self.width/2, center_y - 60, self.sun_sign.upper())
        
        c.setFont(FONT_SYMBOL, 11)
        c.setFillColor(white)
        big_three = f"☉ Sun: {self.sun_sign}  •  ☽ Moon: {self.moon_sign}  •  ↑ Rising: {self.rising_sign}"
        c.drawCentredString(self.width/2, center_y - 115, big_three)
        
        c.setFillColor(self.accent_color)
        c.setFont(FONT_HEADING_BOLD, 22)
        c.drawCentredString(self.width/2, 1.3*inch, "ORASTRIA")
        
        c.setFont(FONT_BODY, 10)
        c.drawCentredString(self.width/2, 1*inch, "Personalized Astrology  •  Written in the Stars")
        
        c.setFont(FONT_SYMBOL, 16)
        c.drawCentredString(0.8*inch, 0.8*inch, '☽')
        c.drawCentredString(self.width - 0.8*inch, 0.8*inch, '☽')
        
        c.showPage()
    
    def new_page(self):
        """Start new page with styling"""
        self.page_num += 1
        c = self.c
        
        c.setFillColor(CREAM)
        c.rect(0, 0, self.width, self.height, fill=True, stroke=False)
        
        c.setFillColor(GOLD)
        c.setFont(FONT_SYMBOL, 10)
        c.drawCentredString(50, self.height - 50, '✦')
        c.drawCentredString(self.width - 50, self.height - 50, '✦')
        c.drawCentredString(50, 50, '✦')
        c.drawCentredString(self.width - 50, 50, '✦')
        
        c.setFillColor(NAVY)
        c.setFont(FONT_BODY, 10)
        c.drawCentredString(self.width/2, 30, f"— {self.page_num} —")
        
        return self.height - 80
    
    def draw_chapter(self, title, subtitle=None):
        """Draw chapter title page"""
        y = self.new_page()
        c = self.c
        
        c.setFillColor(GOLD)
        c.setFont(FONT_SYMBOL, 14)
        c.drawCentredString(self.width/2, self.height - 180, "✧  ✦  ✧")
        
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
    
    def draw_birth_chart_wheel(self):
        """Draw a visual birth chart wheel diagram"""
        y = self.new_page()
        c = self.c
        
        # Title
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 24)
        c.drawCentredString(self.width/2, self.height - 100, "Your Birth Chart")
        
        c.setFillColor(HexColor('#666666'))
        c.setFont(FONT_BODY_ITALIC, 12)
        c.drawCentredString(self.width/2, self.height - 125, "A snapshot of the heavens at the moment you were born")
        
        # Chart wheel center
        center_x = self.width / 2
        center_y = self.height / 2 + 0.5*inch
        
        # Draw outer ring (houses)
        c.setStrokeColor(NAVY)
        c.setLineWidth(2)
        c.circle(center_x, center_y, 140)
        c.setLineWidth(1)
        c.circle(center_x, center_y, 110)
        c.circle(center_x, center_y, 60)
        
        # Draw house lines
        c.setStrokeColor(HexColor('#cccccc'))
        c.setLineWidth(0.5)
        for i in range(12):
            angle = (90 - i * 30) * math.pi / 180
            x1 = center_x + 60 * math.cos(angle)
            y1 = center_y + 60 * math.sin(angle)
            x2 = center_x + 140 * math.cos(angle)
            y2 = center_y + 140 * math.sin(angle)
            c.line(x1, y1, x2, y2)
        
        # Draw zodiac signs around wheel
        for i, sign in enumerate(ZODIAC_ORDER):
            angle = (75 - i * 30) * math.pi / 180
            x = center_x + 125 * math.cos(angle)
            y = center_y + 125 * math.sin(angle)
            
            # Highlight user's signs
            if sign == self.sun_sign:
                c.setFillColor(GOLD)
            elif sign == self.moon_sign:
                c.setFillColor(HexColor('#8899AA'))
            elif sign == self.rising_sign:
                c.setFillColor(HexColor('#AA7755'))
            else:
                c.setFillColor(NAVY)
            
            c.setFont(FONT_SYMBOL_BOLD, 14)
            c.drawCentredString(x, y - 5, ZODIAC_SYMBOLS.get(sign, '★'))
        
        # Center info
        c.setFont(FONT_SYMBOL_BOLD, 24)
        c.setFillColor(GOLD)
        c.drawCentredString(center_x, center_y + 10, '☉')
        c.setFillColor(HexColor('#8899AA'))
        c.drawCentredString(center_x + 15, center_y + 10, '☽')
        
        c.setFillColor(NAVY)
        c.setFont(FONT_BODY, 9)
        c.drawCentredString(center_x, center_y - 15, f"{self.sun_sign[:3]} / {self.moon_sign[:3]} / {self.rising_sign[:3]}")
        
        # Planet positions table
        y_table = 2.8*inch
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 14)
        c.drawCentredString(self.width/2, y_table + 0.4*inch, "Your Planetary Positions")
        
        # Draw table background
        table_width = 5*inch
        table_x = (self.width - table_width) / 2
        c.setFillColor(HexColor('#f5f5f5'))
        c.roundRect(table_x, y_table - 1.6*inch, table_width, 1.8*inch, 5, fill=1, stroke=0)
        
        planets = [
            ("☉", "Sun", self.sun_sign),
            ("☽", "Moon", self.moon_sign),
            ("↑", "Rising", self.rising_sign),
            ("☿", "Mercury", self.chart.get('mercury', 'Unknown')),
            ("♀", "Venus", self.chart.get('venus', 'Unknown')),
            ("♂", "Mars", self.chart.get('mars', 'Unknown')),
            ("♃", "Jupiter", self.chart.get('jupiter', 'Unknown')),
            ("♄", "Saturn", self.chart.get('saturn', 'Unknown')),
            ("MC", "Midheaven", self.chart.get('midheaven', 'Unknown')),
            ("☊", "North Node", self.chart.get('north_node', 'Unknown')),
        ]
        
        # Two columns
        c.setFont(FONT_BODY, 10)
        y = y_table
        col1_x = table_x + 20
        col2_x = table_x + table_width/2 + 20
        
        for i, (symbol, name, sign) in enumerate(planets):
            x = col1_x if i < 5 else col2_x
            row_y = y - (i % 5) * 0.3*inch
            
            c.setFillColor(GOLD)
            c.setFont(FONT_SYMBOL, 12)
            c.drawString(x, row_y, symbol)
            
            c.setFillColor(NAVY)
            c.setFont(FONT_BODY, 10)
            c.drawString(x + 25, row_y, name)
            
            c.setFillColor(HexColor('#444444'))
            c.drawString(x + 90, row_y, sign)
        
        c.showPage()
    
    def draw_pull_quote(self, quote, y, attribution=None):
        """Draw a highlighted pull quote box"""
        c = self.c
        
        if y < self.margin + 120:
            c.showPage()
            y = self.new_page()
        
        # Quote box background
        box_height = 80
        c.setFillColor(HexColor('#f8f5f0'))
        c.roundRect(self.margin + 20, y - box_height + 20, self.width - 2*self.margin - 40, box_height, 8, fill=1, stroke=0)
        
        # Left accent bar
        c.setFillColor(GOLD)
        c.rect(self.margin + 20, y - box_height + 20, 4, box_height, fill=1, stroke=0)
        
        # Quote mark
        c.setFont(FONT_HEADING_BOLD, 36)
        c.setFillColor(HexColor('#d4b87a'))
        c.drawString(self.margin + 35, y - 5, '"')
        
        # Quote text
        c.setFillColor(NAVY)
        c.setFont(FONT_BODY_ITALIC, 11)
        wrapper = textwrap.TextWrapper(width=70)
        lines = wrapper.wrap(quote)
        quote_y = y - 25
        for line in lines[:3]:
            c.drawString(self.margin + 50, quote_y, line)
            quote_y -= 16
        
        if attribution:
            c.setFont(FONT_BODY, 9)
            c.setFillColor(HexColor('#888888'))
            c.drawString(self.margin + 50, quote_y - 5, f"— {attribution}")
        
        return y - box_height - 20
    
    def draw_key_insight_box(self, title, points, y):
        """Draw a key insights box with bullet points"""
        c = self.c
        
        if y < self.margin + 150:
            c.showPage()
            y = self.new_page()
        
        box_height = 30 + len(points) * 22
        
        # Box background
        c.setFillColor(HexColor('#1a1f3c'))
        c.roundRect(self.margin, y - box_height + 10, self.width - 2*self.margin, box_height, 8, fill=1, stroke=0)
        
        # Title
        c.setFillColor(GOLD)
        c.setFont(FONT_HEADING_BOLD, 12)
        c.drawString(self.margin + 15, y - 5, f"✧ {title}")
        
        # Points
        c.setFillColor(white)
        c.setFont(FONT_BODY, 10)
        point_y = y - 28
        for point in points:
            c.drawString(self.margin + 25, point_y, f"• {point[:80]}")
            point_y -= 20
        
        return y - box_height - 15
    
    def draw_glossary_page(self):
        """Draw a glossary page for beginners"""
        self.draw_chapter("Astrology Glossary", "Key Terms Explained")
        y = self.new_page()
        c = self.c
        
        glossary_terms = [
            ("Sun Sign", "Your core identity and ego - determined by where the Sun was at your birth."),
            ("Moon Sign", "Your emotional nature and inner self - how you process feelings."),
            ("Rising Sign (Ascendant)", "The 'mask' you wear - how others perceive you at first meeting."),
            ("Venus", "Planet of love and beauty - shows how you express affection and what you value."),
            ("Mars", "Planet of action and desire - represents your drive, passion, and assertion."),
            ("Mercury", "Planet of communication - how you think, learn, and express ideas."),
            ("Jupiter", "Planet of expansion - where you find luck, growth, and opportunity."),
            ("Saturn", "Planet of discipline - your life lessons, responsibilities, and limitations."),
            ("Midheaven (MC)", "Your public image and career path - what you're known for professionally."),
            ("North Node", "Your soul's purpose - the direction you're meant to grow toward in this life."),
            ("Transit", "When a planet moves through a sign, creating temporary influences."),
            ("Element", "Fire, Earth, Air, or Water - the fundamental energy of each sign."),
        ]
        
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 16)
        c.drawString(self.margin, y, "Understanding Your Chart")
        y -= 30
        
        c.setFont(FONT_BODY, 10)
        c.setFillColor(HexColor('#666666'))
        c.drawString(self.margin, y, "Reference these terms as you read through your personalized analysis.")
        y -= 30
        
        for term, definition in glossary_terms:
            if y < self.margin + 60:
                c.showPage()
                y = self.new_page()
            
            c.setFillColor(NAVY)
            c.setFont(FONT_BODY_BOLD, 11)
            c.drawString(self.margin, y, term)
            
            c.setFillColor(HexColor('#444444'))
            c.setFont(FONT_BODY, 10)
            
            # Wrap definition
            wrapper = textwrap.TextWrapper(width=85)
            lines = wrapper.wrap(definition)
            def_y = y - 16
            for line in lines:
                c.drawString(self.margin + 10, def_y, line)
                def_y -= 14
            
            y = def_y - 10
        
        c.showPage()
    
    def draw_summary_page(self):
        """Draw a final summary page with key takeaways"""
        self.draw_chapter("Your Cosmic Summary", "Key Takeaways at a Glance")
        y = self.new_page()
        c = self.c
        
        # Big Three summary box
        c.setFillColor(HexColor('#1a1f3c'))
        c.roundRect(self.margin, y - 100, self.width - 2*self.margin, 110, 10, fill=1, stroke=0)
        
        c.setFillColor(GOLD)
        c.setFont(FONT_HEADING_BOLD, 16)
        c.drawCentredString(self.width/2, y - 15, "Your Big Three")
        
        # Three columns
        col_width = (self.width - 2*self.margin) / 3
        placements = [
            ("☉", "SUN", self.sun_sign),
            ("☽", "MOON", self.moon_sign),
            ("↑", "RISING", self.rising_sign),
        ]
        
        for i, (symbol, label, sign) in enumerate(placements):
            col_x = self.margin + col_width/2 + i * col_width
            
            c.setFont(FONT_SYMBOL_BOLD, 28)
            c.setFillColor(GOLD)
            c.drawCentredString(col_x, y - 45, symbol)
            
            c.setFont(FONT_BODY, 9)
            c.setFillColor(HexColor('#888888'))
            c.drawCentredString(col_x, y - 65, label)
            
            c.setFont(FONT_BODY_BOLD, 12)
            c.setFillColor(white)
            c.drawCentredString(col_x, y - 82, sign)
        
        y -= 130
        
        # Top compatible signs
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 14)
        c.drawString(self.margin, y, "✧ Your Top Compatible Signs")
        y -= 25
        
        # Get top 3 compatibility scores
        compat = self.content.get('compatibility', {})
        sorted_compat = sorted(
            [(sign, data.get('percentage', 70) if isinstance(data, dict) else 70) 
             for sign, data in compat.items()],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        for sign, pct in sorted_compat:
            c.setFillColor(GOLD)
            c.setFont(FONT_SYMBOL, 14)
            c.drawString(self.margin + 10, y, ZODIAC_SYMBOLS.get(sign, '★'))
            
            c.setFillColor(NAVY)
            c.setFont(FONT_BODY_BOLD, 11)
            c.drawString(self.margin + 35, y, sign)
            
            c.setFillColor(HexColor('#666666'))
            c.setFont(FONT_BODY, 11)
            c.drawString(self.margin + 130, y, f"{pct}%")
            y -= 22
        
        y -= 20
        
        # Key numbers
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 14)
        c.drawString(self.margin, y, "✧ Your Numbers")
        y -= 25
        
        life_path = calculate_life_path(self.user.get('birth_date', '2000-01-01'))
        expression = calculate_expression_number(self.name)
        
        c.setFont(FONT_BODY, 11)
        c.setFillColor(HexColor('#444444'))
        c.drawString(self.margin + 10, y, f"Life Path: {life_path}")
        c.drawString(self.margin + 150, y, f"Expression: {expression}")
        y -= 35
        
        # Key dates preview
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 14)
        c.drawString(self.margin, y, "✧ 2026 Highlights")
        y -= 25
        
        highlights = [
            "Career breakthrough windows in spring and fall",
            "Relationship growth opportunities mid-year",
            "Personal transformation period approaching",
        ]
        
        c.setFont(FONT_BODY, 10)
        c.setFillColor(HexColor('#444444'))
        for highlight in highlights:
            c.drawString(self.margin + 10, y, f"→ {highlight}")
            y -= 18
        
        y -= 25
        
        # Lucky elements box
        c.setFillColor(HexColor('#f8f5f0'))
        c.roundRect(self.margin, y - 70, self.width - 2*self.margin, 80, 8, fill=1, stroke=0)
        
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 12)
        c.drawCentredString(self.width/2, y - 10, "Your Lucky Elements")
        
        element = ZODIAC_DATA.get(self.sun_sign, {}).get('element', 'Fire')
        lucky_colors = {
            'Fire': 'Red, Orange, Gold',
            'Earth': 'Green, Brown, Tan',
            'Air': 'Yellow, Light Blue, White',
            'Water': 'Blue, Silver, Sea Green'
        }
        lucky_days = {
            'Fire': 'Tuesday, Sunday',
            'Earth': 'Friday, Saturday',
            'Air': 'Wednesday, Thursday',
            'Water': 'Monday, Friday'
        }
        
        c.setFont(FONT_BODY, 10)
        c.setFillColor(HexColor('#444444'))
        c.drawString(self.margin + 20, y - 35, f"Element: {element}")
        c.drawString(self.margin + 20, y - 52, f"Lucky Colors: {lucky_colors.get(element, 'Gold, Purple')}")
        c.drawString(self.width/2 + 20, y - 35, f"Lucky Days: {lucky_days.get(element, 'Sunday')}")
        c.drawString(self.width/2 + 20, y - 52, f"Power Crystal: {ZODIAC_DATA.get(self.sun_sign, {}).get('crystal', 'Clear Quartz')}")
        
        c.showPage()
    
    def draw_section_title(self, text, y):
        """Draw section title with underline"""
        c = self.c
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 18)
        c.drawString(self.margin, y, text)
        
        c.setStrokeColor(GOLD)
        c.setLineWidth(2)
        c.line(self.margin, y - 5, self.margin + 60, y - 5)
        
        return y - 35
    
    def draw_text(self, text, y, width=None):
        """Draw wrapped text with proper font"""
        if not text:
            return y
        
        c = self.c
        c.setFillColor(NAVY)
        c.setFont(FONT_BODY, 11)
        
        if width is None:
            width = self.width - 2 * self.margin
        
        wrapper = textwrap.TextWrapper(width=int(width / 5.5))
        paragraphs = text.split('\n\n') if '\n\n' in text else text.split('\n')
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            lines = wrapper.wrap(para)
            for line in lines:
                if y < self.margin + 50:
                    c.showPage()
                    y = self.new_page()
                    c.setFillColor(NAVY)
                    c.setFont(FONT_BODY, 11)
                
                c.drawString(self.margin, y, line)
                y -= 16
            
            y -= 8
        
        return y
    
    def draw_compat_entry(self, sign, data, y):
        """Draw compatibility entry with colored bar"""
        c = self.c
        
        if y < self.margin + 120:
            c.showPage()
            y = self.new_page()
        
        if isinstance(data, dict):
            text = data.get('text', '')
            percentage = data.get('percentage', 70)
        else:
            text = data
            import re
            match = re.search(r'(\d+)%', text)
            percentage = int(match.group(1)) if match else 70
        
        c.setFillColor(GOLD)
        c.setFont(FONT_SYMBOL_BOLD, 18)
        c.drawString(self.margin, y, ZODIAC_SYMBOLS.get(sign, '★'))
        
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 14)
        c.drawString(self.margin + 30, y, sign)
        
        bar_width = 120
        bar_height = 12
        bar_x = self.width - self.margin - bar_width - 50
        bar_y = y - 2
        
        c.setFillColor(LIGHT_GRAY)
        c.rect(bar_x, bar_y, bar_width, bar_height, fill=1, stroke=0)
        
        fill_width = bar_width * (percentage / 100)
        c.setFillColor(self.get_compat_color(percentage))
        c.rect(bar_x, bar_y, fill_width, bar_height, fill=1, stroke=0)
        
        c.setFillColor(NAVY)
        c.setFont(FONT_BODY_BOLD, 11)
        c.drawString(bar_x + bar_width + 10, y - 2, f"{percentage}%")
        
        y -= 25
        
        if text:
            sentences = text.split('.')[:3]
            short_text = '.'.join(sentences) + '.' if sentences else text[:200]
            y = self.draw_text(short_text, y, width=self.width - 2.5*self.margin)
        
        return y - 15
    
    def draw_monthly_entry(self, month, text, y):
        """Draw monthly forecast entry"""
        c = self.c
        
        if y < self.margin + 100:
            c.showPage()
            y = self.new_page()
        
        c.setFillColor(GOLD)
        c.setFont(FONT_SYMBOL, 12)
        c.drawString(self.margin, y, "✧")
        
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 14)
        c.drawString(self.margin + 20, y, f"{month} 2026")
        
        y -= 20
        
        if text:
            y = self.draw_text(text, y)
        
        return y - 10
    
    def build(self):
        """Build the complete book"""
        print(f"\n📖 Building PDF for {self.name}...")
        
        self.draw_cover()
        
        # Birth Chart Wheel (NEW)
        self.draw_birth_chart_wheel()
        
        # Glossary for beginners (NEW - at the start for reference)
        familiarity = self.user.get('astrology_familiarity', 'Beginner')
        if familiarity.lower() in ['beginner', 'new', 'none', 'just starting']:
            self.draw_glossary_page()
        
        # Introduction
        self.draw_chapter("Introduction", "Your Cosmic Journey Begins")
        y = self.new_page()
        y = self.draw_section_title(f"Welcome, {self.first_name}", y)
        y = self.draw_text(self.content.get('introduction', ''), y)
        self.c.showPage()
        
        # The Big Three
        self.draw_chapter("The Big Three", "Sun, Moon & Rising")
        
        y = self.new_page()
        self.c.setFillColor(GOLD)
        self.c.setFont(FONT_SYMBOL_BOLD, 48)
        self.c.drawCentredString(self.width/2, self.height - 120, ZODIAC_SYMBOLS.get(self.sun_sign, '★'))
        self.c.setFillColor(NAVY)
        self.c.setFont(FONT_HEADING_BOLD, 20)
        self.c.drawCentredString(self.width/2, self.height - 160, f"Your Sun in {self.sun_sign}")
        y = self.height - 200
        y = self.draw_text(self.content.get('sun_sign', ''), y)
        self.c.showPage()
        
        y = self.new_page()
        self.c.setFillColor(GOLD)
        self.c.setFont(FONT_SYMBOL_BOLD, 48)
        self.c.drawCentredString(self.width/2, self.height - 120, '☽')
        self.c.setFillColor(NAVY)
        self.c.setFont(FONT_HEADING_BOLD, 20)
        self.c.drawCentredString(self.width/2, self.height - 160, f"Your Moon in {self.moon_sign}")
        y = self.height - 200
        y = self.draw_text(self.content.get('moon_sign', ''), y)
        self.c.showPage()
        
        y = self.new_page()
        self.c.setFillColor(GOLD)
        self.c.setFont(FONT_SYMBOL_BOLD, 48)
        self.c.drawCentredString(self.width/2, self.height - 120, '↑')
        self.c.setFillColor(NAVY)
        self.c.setFont(FONT_HEADING_BOLD, 20)
        self.c.drawCentredString(self.width/2, self.height - 160, f"Your {self.rising_sign} Rising")
        y = self.height - 200
        y = self.draw_text(self.content.get('rising_sign', ''), y)
        self.c.showPage()
        
        # Personality
        self.draw_chapter("Your Inner World", "Deep Personality Analysis")
        y = self.new_page()
        y = self.draw_section_title("Understanding Your Psychology", y)
        y = self.draw_text(self.content.get('personality', ''), y)
        self.c.showPage()
        
        # Love
        self.draw_chapter("Love & Relationships", "Your Heart's Blueprint")
        y = self.new_page()
        y = self.draw_section_title("Your Romantic Nature", y)
        y = self.draw_text(self.content.get('love', ''), y)
        self.c.showPage()
        
        # Compatibility
        self.draw_chapter("Compatibility Guide", "Your Match with All 12 Signs")
        y = self.new_page()
        for sign in ZODIAC_ORDER:
            data = self.content.get('compatibility', {}).get(sign, {'text': '', 'percentage': 70})
            y = self.draw_compat_entry(sign, data, y)
        self.c.showPage()
        
        # Career
        self.draw_chapter("Career & Purpose", "Your Professional Destiny")
        y = self.new_page()
        y = self.draw_section_title("Your Career Blueprint", y)
        y = self.draw_text(self.content.get('career', ''), y)
        self.c.showPage()
        
        # Important Dates (if generated)
        if 'important_dates' in self.content and self.content['important_dates']:
            self.draw_chapter("Important Dates", "Key Moments in Your Future")
            y = self.new_page()
            y = self.draw_section_title("Your Significant Dates", y)
            y = self.draw_text(self.content.get('important_dates', ''), y)
            self.c.showPage()
        
        # 2026 Forecast
        self.draw_chapter("Your Year Ahead", "2026 Forecast")
        y = self.new_page()
        y = self.draw_section_title("2026 Overview", y)
        y = self.draw_text(self.content.get('forecast', ''), y)
        self.c.showPage()
        
        # Monthly Forecasts
        self.draw_chapter("Monthly Forecasts", "Your 2026 Month-by-Month Guide")
        y = self.new_page()
        all_months = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        for month in all_months:
            text = self.content.get('monthly', {}).get(month, '')
            y = self.draw_monthly_entry(month, text, y)
        self.c.showPage()
        
        # Numerology
        self.draw_chapter("Numerology", "The Numbers of Your Life")
        y = self.new_page()
        life_path = calculate_life_path(self.user.get('birth_date', '2000-01-01'))
        y = self.draw_section_title(f"Life Path {life_path}", y)
        y = self.draw_text(self.content.get('numerology', ''), y)
        self.c.showPage()
        
        # Tarot
        self.draw_chapter("Tarot Guidance", "Cards for Your Journey")
        y = self.new_page()
        y = self.draw_section_title("Your Tarot Reading", y)
        y = self.draw_text(self.content.get('tarot', ''), y)
        self.c.showPage()
        
        # Crystals
        self.draw_chapter("Crystals & Rituals", "Tools for Your Path")
        y = self.new_page()
        y = self.draw_section_title("Your Power Crystals", y)
        y = self.draw_text(self.content.get('crystals', ''), y)
        self.c.showPage()
        
        # Summary page (NEW - before closing)
        self.draw_summary_page()
        
        # Closing
        self.draw_chapter("Closing Thoughts", "Your Journey Continues")
        y = self.new_page()
        y = self.draw_section_title(f"Dear {self.first_name},", y)
        y = self.draw_text(self.content.get('closing', ''), y)
        
        y -= 40
        self.c.setFillColor(NAVY)
        self.c.setFont(FONT_BODY_ITALIC, 14)
        self.c.drawString(self.margin, y, "With cosmic blessings,")
        self.c.setFillColor(GOLD)
        self.c.setFont(FONT_HEADING_BOLD, 26)
        self.c.drawString(self.margin, y - 35, "ORASTRIA")
        
        self.c.save()
        print(f"✅ Book saved: {self.output_path}")
        print(f"📄 Total pages: {self.page_num}")
        return self.output_path


# ============================================================
# MAIN FUNCTIONS
# ============================================================

def generate_ai_book(user_data, chart_data, output_path):
    """
    Generate complete AI-powered astrology book.
    BACKWARD COMPATIBLE - uses provided chart_data.
    """
    ai_gen = AIContentGenerator(user_data, chart_data)
    content = ai_gen.generate_all()
    book = OrastriaVisualBook(user_data, chart_data, content, output_path)
    return book.build()


def generate_book(user_data, output_path):
    """
    Generate complete AI-powered astrology book with Prokerala integration.
    NEW FUNCTION - fetches chart from Prokerala API.
    """
    chart_data = None
    
    # Try to get chart from Prokerala
    if PROKERALA_CLIENT_ID and PROKERALA_CLIENT_SECRET:
        print("🔮 Fetching chart from Prokerala...")
        birth_date = user_data.get('birth_date', '')
        birth_time = user_data.get('birth_time', '12:00')
        birth_place = user_data.get('birth_place', '')
        
        # Convert 12-hour to 24-hour if needed
        time_period = user_data.get('birth_time_period', '').upper()
        if time_period == 'PM' and ':' in birth_time:
            parts = birth_time.split(':')
            hour = int(parts[0])
            if hour != 12:
                hour += 12
            birth_time = f"{hour:02d}:{parts[1]}"
        elif time_period == 'AM' and ':' in birth_time:
            parts = birth_time.split(':')
            hour = int(parts[0])
            if hour == 12:
                hour = 0
            birth_time = f"{hour:02d}:{parts[1]}"
        
        chart_data = get_chart_from_prokerala(birth_date, birth_time, birth_place)
        
        if chart_data:
            print(f"✅ Chart fetched: Sun in {chart_data.get('sun_sign')}, Moon in {chart_data.get('moon_sign')}, Rising in {chart_data.get('rising_sign')}")
    
    # Fall back to provided chart data or defaults
    if not chart_data:
        print("⚠️ Using provided/default chart data")
        chart_data = {
            'sun_sign': user_data.get('sun_sign') or 'Aries',
            'moon_sign': user_data.get('moon_sign') or 'Aries',
            'rising_sign': user_data.get('rising_sign') or 'Aries',
            'mercury': user_data.get('mercury') or 'Aries',
            'venus': user_data.get('venus') or 'Aries',
            'mars': user_data.get('mars') or 'Aries',
            'jupiter': user_data.get('jupiter') or 'Aries',
            'saturn': user_data.get('saturn') or 'Aries',
            'midheaven': user_data.get('midheaven') or 'Aries',
            'north_node': user_data.get('north_node') or 'Aries',
        }
    
    return generate_ai_book(user_data, chart_data, output_path)


if __name__ == "__main__":
    # Test with complete data
    user_data = {
        "first_name": "Taylor",
        "last_name": "Swift",
        "gender": "female",
        "birth_date": "1989-12-13",
        "birth_time": "05:17",
        "birth_time_period": "AM",
        "birth_place": "Reading, Pennsylvania, USA",
        "astrology_familiarity": "Intermediate",
        "main_goals": ["Discover my life path & purpose", "Improve my relationships"],
        "life_dreams": "Making significant impact in my field",
        "motivations": "Creating something unique",
        "relationship_status": "Single",
        "relationship_goals": ["Find a perfect partner"],
        "outlook": "Optimist",
        "decision_worry": "Somewhat agree",
        "need_to_be_liked": "Sometimes",
        "insecurity_with_strangers": "Somewhat agree",
        "love_language": "Words of affirmation",
        "logic_vs_emotions": "A bit of both",
        "overthink_relationships": "Often",
        "desired_partner_traits": ["Honest, open communication", "Emotional security"],
        "career_question": "What work will bring me joy and fulfillment?",
        "birth_chart_includes": ["My personality traits analysis", "In-depth compatibility guide"],
        "important_dates": ["When will I meet my perfect match", "Key dates for career changes"],
        "additional_topics": ["Unlocking mysteries with numerology", "Guided Tarot card readings"],
        "significant_life_event_soon": "Yes",
        "book_color": "red"
    }
    
    # Test with Prokerala (if credentials available)
    generate_book(user_data, "/tmp/orastria_test.pdf")
