#!/usr/bin/env python3
"""
Orastria AI-Powered Book Generator v5
With improved visuals: Raleway/Garamond fonts, colored compatibility bars, zodiac symbols
"""

import requests
import json
import time
import math
import os
import urllib.request
from datetime import datetime

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
    # Determine font directory
    if os.path.exists('/app'):
        font_dir = '/app/fonts'
    else:
        font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
    
    os.makedirs(font_dir, exist_ok=True)
    
    # Download fonts if needed
    for font_name, url in FONT_URLS.items():
        font_path = os.path.join(font_dir, font_name)
        if not os.path.exists(font_path):
            try:
                print(f"Downloading {font_name}...")
                urllib.request.urlretrieve(url, font_path)
            except Exception as e:
                print(f"Failed to download {font_name}: {e}")
    
    # Register fonts
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

# Initialize fonts
FONTS = ensure_fonts()

# Font assignments
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

# Compatibility bar colors
GREEN = HexColor('#2ecc71')
YELLOW = HexColor('#f1c40f')
ORANGE = HexColor('#e67e22')
RED = HexColor('#e74c3c')
LIGHT_GRAY = HexColor('#ecf0f1')

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
    "Aries": {"element": "Fire", "modality": "Cardinal", "ruler": "Mars"},
    "Taurus": {"element": "Earth", "modality": "Fixed", "ruler": "Venus"},
    "Gemini": {"element": "Air", "modality": "Mutable", "ruler": "Mercury"},
    "Cancer": {"element": "Water", "modality": "Cardinal", "ruler": "Moon"},
    "Leo": {"element": "Fire", "modality": "Fixed", "ruler": "Sun"},
    "Virgo": {"element": "Earth", "modality": "Mutable", "ruler": "Mercury"},
    "Libra": {"element": "Air", "modality": "Cardinal", "ruler": "Venus"},
    "Scorpio": {"element": "Water", "modality": "Fixed", "ruler": "Pluto"},
    "Sagittarius": {"element": "Fire", "modality": "Mutable", "ruler": "Jupiter"},
    "Capricorn": {"element": "Earth", "modality": "Cardinal", "ruler": "Saturn"},
    "Aquarius": {"element": "Air", "modality": "Fixed", "ruler": "Uranus"},
    "Pisces": {"element": "Water", "modality": "Mutable", "ruler": "Neptune"}
}

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
    """Generate personalized AI content"""
    
    def __init__(self, user_data, chart_data):
        self.user = user_data
        self.chart = chart_data
        self.name = user_data.get("name", "Friend")
        self.first_name = self.name.split()[0]
        self.sun_sign = chart_data.get("sun_sign", "Aries")
        self.moon_sign = chart_data.get("moon_sign", "Aries")
        self.rising_sign = chart_data.get("rising_sign", "Aries")
        self.life_path = calculate_life_path(user_data.get("birth_date", "2000-01-01"))
        self.expression_number = calculate_expression_number(self.name)
        self.content = {}
    
    def _build_context(self):
        return f"""
User: {self.name}
Birth: {self.user.get('birth_date')} at {self.user.get('birth_time')} {self.user.get('birth_time_period', '')}
Place: {self.user.get('birth_place')}

Chart:
- Sun: {self.sun_sign} ({ZODIAC_DATA[self.sun_sign]['element']})
- Moon: {self.moon_sign} ({ZODIAC_DATA[self.moon_sign]['element']})
- Rising: {self.rising_sign} ({ZODIAC_DATA[self.rising_sign]['element']})
- Venus: {self.chart.get('venus', 'Unknown')}
- Mars: {self.chart.get('mars', 'Unknown')}
- Midheaven: {self.chart.get('midheaven', 'Unknown')}

Quiz:
- Outlook: {self.user.get('outlook', 'Optimist')}
- Dreams: {self.user.get('life_dreams', '')}
- Love Language: {self.user.get('love_language', '')}
- Career Question: {self.user.get('career_question', '')}

Numerology: Life Path {self.life_path}, Expression {self.expression_number}
"""
    
    def generate_section(self, section_name, prompt, max_tokens=1500):
        print(f"  Generating: {section_name}...")
        full_prompt = f"{prompt}\n\nContext:\n{self._build_context()}\n\nWrite in second person. Be warm and specific."
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
            'closing': f"Dear {self.first_name}, may the stars guide your journey..."
        }
        return fallbacks.get(section, "Content for this section...")
    
    def generate_all(self):
        print(f"\n🌟 Generating AI content for {self.name}...")
        print("=" * 50)
        
        sections = [
            ('introduction', "Write a warm introduction (3-4 paragraphs, ~350 words) welcoming them to their cosmic blueprint."),
            ('sun_sign', f"Write about their {self.sun_sign} Sun (4-5 paragraphs, ~450 words). Cover essence, strengths, shadows."),
            ('moon_sign', f"Write about their {self.moon_sign} Moon (4 paragraphs, ~400 words). Cover emotions, needs, intuition."),
            ('rising_sign', f"Write about their {self.rising_sign} Rising (3-4 paragraphs, ~350 words). Cover first impressions, persona."),
            ('personality', "Write a personality analysis (4-5 paragraphs, ~450 words) integrating their chart and quiz answers."),
            ('love', "Write about love and relationships (4-5 paragraphs, ~450 words). Cover Venus, Mars, love style."),
            ('career', "Write about career and purpose (4 paragraphs, ~400 words). Cover strengths, ideal paths."),
            ('forecast', "Write 2026 forecast (5 paragraphs, ~500 words). Cover themes, opportunities, key months."),
            ('numerology', f"Write about Life Path {self.life_path} and Expression {self.expression_number} (3-4 paragraphs, ~350 words)."),
            ('tarot', "Create a tarot reading (4 paragraphs, ~400 words) with birth cards and a 5-card spread."),
            ('crystals', "Write about crystals and rituals (3-4 paragraphs, ~350 words). Recommend 5 crystals and moon rituals."),
            ('closing', "Write a warm closing (3 paragraphs, ~300 words) with an inspiring blessing."),
        ]
        
        for section_name, prompt in sections:
            self.generate_section(section_name, prompt)
        
        # Batch compatibility
        print("  Generating: compatibility (batched)...")
        self.content['compatibility'] = {}
        
        for batch_start in [0, 6]:
            signs_batch = ZODIAC_ORDER[batch_start:batch_start+6]
            prompt = f"""Write compatibility for {self.sun_sign} with: {', '.join(signs_batch)}.

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
                # Try simpler pattern
                simple_pattern = rf'{sign.upper()}:\s*(.*?)(?=(?:ARIES|TAURUS|GEMINI|CANCER|LEO|VIRGO|LIBRA|SCORPIO|SAGITTARIUS|CAPRICORN|AQUARIUS|PISCES):|\Z)'
                simple_match = re.search(simple_pattern, text, re.DOTALL | re.IGNORECASE)
                if simple_match:
                    content = simple_match.group(1).strip()
                    # Extract percentage from content
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
# PDF BOOK GENERATOR WITH VISUAL IMPROVEMENTS
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
        
        self.name = user_data.get("name", "Friend")
        self.first_name = self.name.split()[0]
        self.sun_sign = chart_data.get("sun_sign", "Aries")
        self.moon_sign = chart_data.get("moon_sign", "Aries")
        self.rising_sign = chart_data.get("rising_sign", "Aries")
        
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
        
        # Navy background
        c.setFillColor(NAVY)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        
        # Double gold border
        c.setStrokeColor(GOLD)
        c.setLineWidth(2)
        c.rect(0.4*inch, 0.4*inch, self.width - 0.8*inch, self.height - 0.8*inch)
        c.setLineWidth(1)
        c.rect(0.5*inch, 0.5*inch, self.width - 1*inch, self.height - 1*inch)
        
        # Sun and Moon in corners (using symbol font)
        c.setFont(FONT_SYMBOL_BOLD, 24)
        c.setFillColor(GOLD)
        c.drawCentredString(0.8*inch, self.height - 0.8*inch, '☉')
        c.drawCentredString(self.width - 0.8*inch, self.height - 0.8*inch, '☽')
        
        # Title
        c.setFont(FONT_HEADING_BOLD, 36)
        c.drawCentredString(self.width/2, self.height - 1.8*inch, "YOUR COSMIC")
        c.drawCentredString(self.width/2, self.height - 2.3*inch, "BLUEPRINT")
        
        # Decorative line
        c.setLineWidth(1)
        c.line(2*inch, self.height - 2.55*inch, self.width - 2*inch, self.height - 2.55*inch)
        
        # Name
        c.setFillColor(white)
        c.setFont(FONT_HEADING_BOLD, 28)
        c.drawCentredString(self.width/2, self.height - 3.2*inch, self.name)
        
        # Birth info
        c.setFillColor(SOFT_GOLD)
        c.setFont(FONT_BODY, 12)
        birth_time = f"{self.user.get('birth_time', '')} {self.user.get('birth_time_period', '')}".strip()
        c.drawCentredString(self.width/2, self.height - 3.6*inch, f"{self.birth_date_formatted}  •  {birth_time}")
        c.drawCentredString(self.width/2, self.height - 3.85*inch, self.user.get('birth_place', ''))
        
        # Zodiac circle with symbol
        center_y = self.height / 2 - 0.3*inch
        c.setStrokeColor(GOLD)
        c.setLineWidth(2)
        c.circle(self.width/2, center_y, 85)
        c.setLineWidth(1)
        c.circle(self.width/2, center_y, 95)
        
        # Zodiac symbol (using DejaVu for proper rendering)
        c.setFillColor(GOLD)
        c.setFont(FONT_SYMBOL_BOLD, 72)
        c.drawCentredString(self.width/2, center_y - 15, ZODIAC_SYMBOLS.get(self.sun_sign, '★'))
        
        # Sign name
        c.setFont(FONT_HEADING_BOLD, 18)
        c.drawCentredString(self.width/2, center_y - 60, self.sun_sign.upper())
        
        # Big Three line
        c.setFont(FONT_SYMBOL, 11)
        c.setFillColor(white)
        big_three = f"☉ Sun: {self.sun_sign}  •  ☽ Moon: {self.moon_sign}  •  ↑ Rising: {self.rising_sign}"
        c.drawCentredString(self.width/2, center_y - 115, big_three)
        
        # Branding
        c.setFillColor(GOLD)
        c.setFont(FONT_HEADING_BOLD, 22)
        c.drawCentredString(self.width/2, 1.3*inch, "ORASTRIA")
        
        c.setFont(FONT_BODY, 10)
        c.drawCentredString(self.width/2, 1*inch, "Personalized Astrology  •  Written in the Stars")
        
        # Bottom moons
        c.setFont(FONT_SYMBOL, 16)
        c.drawCentredString(0.8*inch, 0.8*inch, '☽')
        c.drawCentredString(self.width - 0.8*inch, 0.8*inch, '☽')
        
        c.showPage()
    
    def new_page(self):
        """Start new page with styling"""
        self.page_num += 1
        c = self.c
        
        # Cream background
        c.setFillColor(CREAM)
        c.rect(0, 0, self.width, self.height, fill=True, stroke=False)
        
        # Corner decorations
        c.setFillColor(GOLD)
        c.setFont(FONT_SYMBOL, 10)
        c.drawCentredString(50, self.height - 50, '✦')
        c.drawCentredString(self.width - 50, self.height - 50, '✦')
        c.drawCentredString(50, 50, '✦')
        c.drawCentredString(self.width - 50, 50, '✦')
        
        # Page number
        c.setFillColor(NAVY)
        c.setFont(FONT_BODY, 10)
        c.drawCentredString(self.width/2, 30, f"— {self.page_num} —")
        
        return self.height - 80
    
    def draw_chapter(self, title, subtitle=None):
        """Draw chapter title page"""
        y = self.new_page()
        c = self.c
        
        # Decorative stars
        c.setFillColor(GOLD)
        c.setFont(FONT_SYMBOL, 14)
        c.drawCentredString(self.width/2, self.height - 180, "✧  ✦  ✧")
        
        # Title
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 32)
        c.drawCentredString(self.width/2, self.height - 280, title)
        
        if subtitle:
            c.setFillColor(SOFT_GOLD)
            c.setFont(FONT_BODY_ITALIC, 16)
            c.drawCentredString(self.width/2, self.height - 320, subtitle)
        
        # Bottom stars
        c.setFillColor(GOLD)
        c.setFont(FONT_SYMBOL, 14)
        c.drawCentredString(self.width/2, self.height - 380, "✧  ✦  ✧")
        
        c.showPage()
    
    def draw_section_title(self, text, y):
        """Draw section title with underline"""
        c = self.c
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 18)
        c.drawString(self.margin, y, text)
        
        # Gold underline
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
        
        # Handle both dict and string formats
        if isinstance(data, dict):
            text = data.get('text', '')
            percentage = data.get('percentage', 70)
        else:
            text = data
            # Try to extract percentage from text
            import re
            match = re.search(r'(\d+)%', text)
            percentage = int(match.group(1)) if match else 70
        
        # Sign header with symbol
        c.setFillColor(GOLD)
        c.setFont(FONT_SYMBOL_BOLD, 18)
        c.drawString(self.margin, y, ZODIAC_SYMBOLS.get(sign, '★'))
        
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 14)
        c.drawString(self.margin + 30, y, sign)
        
        # Percentage and bar
        bar_width = 120
        bar_height = 12
        bar_x = self.width - self.margin - bar_width - 50
        bar_y = y - 2
        
        # Background bar
        c.setFillColor(LIGHT_GRAY)
        c.rect(bar_x, bar_y, bar_width, bar_height, fill=1, stroke=0)
        
        # Colored progress bar
        fill_width = bar_width * (percentage / 100)
        c.setFillColor(self.get_compat_color(percentage))
        c.rect(bar_x, bar_y, fill_width, bar_height, fill=1, stroke=0)
        
        # Percentage text
        c.setFillColor(NAVY)
        c.setFont(FONT_BODY_BOLD, 11)
        c.drawString(bar_x + bar_width + 10, y - 2, f"{percentage}%")
        
        y -= 25
        
        # Content text (abbreviated)
        if text:
            # Only show first 2-3 sentences
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
        
        # Month header
        c.setFillColor(GOLD)
        c.setFont(FONT_SYMBOL, 12)
        c.drawString(self.margin, y, "✧")
        
        c.setFillColor(NAVY)
        c.setFont(FONT_HEADING_BOLD, 14)
        c.drawString(self.margin + 20, y, f"{month} 2026")
        
        y -= 20
        
        # Content
        if text:
            y = self.draw_text(text, y)
        
        return y - 10
    
    def build(self):
        """Build the complete book"""
        print(f"\n📖 Building PDF for {self.name}...")
        
        # Cover
        self.draw_cover()
        
        # Introduction
        self.draw_chapter("Introduction", "Your Cosmic Journey Begins")
        y = self.new_page()
        y = self.draw_section_title(f"Welcome, {self.first_name}", y)
        y = self.draw_text(self.content.get('introduction', ''), y)
        self.c.showPage()
        
        # The Big Three
        self.draw_chapter("The Big Three", "Sun, Moon & Rising")
        
        # Sun Sign
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
        
        # Moon Sign
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
        
        # Rising Sign
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
        
        # Closing
        self.draw_chapter("Closing Thoughts", "Your Journey Continues")
        y = self.new_page()
        y = self.draw_section_title(f"Dear {self.first_name},", y)
        y = self.draw_text(self.content.get('closing', ''), y)
        
        # Final branding
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
# MAIN FUNCTION
# ============================================================

def generate_ai_book(user_data, chart_data, output_path):
    """Generate complete AI-powered astrology book"""
    ai_gen = AIContentGenerator(user_data, chart_data)
    content = ai_gen.generate_all()
    book = OrastriaVisualBook(user_data, chart_data, content, output_path)
    return book.build()


if __name__ == "__main__":
    user_data = {
        "name": "Taylor Swift",
        "birth_date": "1989-12-13",
        "birth_time": "05:17",
        "birth_time_period": "AM",
        "birth_place": "Reading, Pennsylvania",
        "outlook": "Optimist",
        "love_language": "Words of affirmation",
    }
    
    chart_data = {
        "sun_sign": "Sagittarius",
        "moon_sign": "Cancer",
        "rising_sign": "Scorpio",
        "venus": "Aquarius",
        "mars": "Scorpio",
    }
    
    generate_ai_book(user_data, chart_data, "/tmp/orastria_visual_test.pdf")
