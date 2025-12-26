#!/usr/bin/env python3
"""
Orastria AI-Powered Complete Book Generator
Combines AI content generation with PDF creation
Deploy to Railway with your existing setup
"""

import requests
import json
import time
import math
import os
import subprocess
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import textwrap

# ============================================================
# CONFIGURATION
# ============================================================

REPLICATE_URL = os.environ.get('REPLICATE_MODEL_URL', 'https://api.replicate.com/v1/models/anthropic/claude-3.5-sonnet/predictions')
REPLICATE_API_KEY = os.environ.get('REPLICATE_API_KEY', '')  # Set in Railway environment variables

# Find and register DejaVu fonts
def find_font(font_name):
    """Find font file path across different systems"""
    import glob
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '.'
    
    possible_paths = [
        os.path.join(script_dir, 'fonts', font_name),
        f'/app/fonts/{font_name}',
        f'/usr/share/fonts/truetype/dejavu/{font_name}',
        f'/usr/share/fonts/dejavu/{font_name}',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Search nix store
    try:
        matches = glob.glob('/nix/store/*dejavu*/share/fonts/truetype/*.ttf', recursive=True)
        for match in matches:
            if font_name in match:
                return match
    except:
        pass
    
    return None

dejavu_regular = find_font('DejaVuSans.ttf')
dejavu_bold = find_font('DejaVuSans-Bold.ttf')

if dejavu_regular:
    pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_regular))
if dejavu_bold:
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', dejavu_bold))

FONT_REGULAR = 'DejaVuSans' if dejavu_regular else 'Helvetica'
FONT_BOLD = 'DejaVuSans-Bold' if dejavu_bold else 'Helvetica-Bold'

# Brand Colors
NAVY = HexColor('#1a1f3c')
GOLD = HexColor('#c9a961')
CREAM = HexColor('#f8f5f0')
SOFT_GOLD = HexColor('#d4b87a')

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
# NUMEROLOGY CALCULATIONS
# ============================================================

def calculate_life_path(birth_date):
    """Calculate numerology life path number from birth date"""
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
    """Calculate expression number from name"""
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
# AI CONTENT GENERATION (Claude API via Replicate)
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
        
        for _ in range(90):  # Max 90 seconds
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
                print(f"API failed: {result_data.get('error')}")
                return None
        
        return None
        
    except Exception as e:
        print(f"API Error: {e}")
        return None


class AIContentGenerator:
    """Generate personalized AI content for all book sections"""
    
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
        """Build full context for AI prompts"""
        return f"""
User Profile:
- Name: {self.name}
- Birth Date: {self.user.get('birth_date')}
- Birth Time: {self.user.get('birth_time')} {self.user.get('birth_time_period', '')}
- Birth Place: {self.user.get('birth_place')}

Astrological Chart:
- Sun Sign: {self.sun_sign} ({ZODIAC_DATA[self.sun_sign]['element']}, ruled by {ZODIAC_DATA[self.sun_sign]['ruler']})
- Moon Sign: {self.moon_sign} ({ZODIAC_DATA[self.moon_sign]['element']})
- Rising Sign: {self.rising_sign} ({ZODIAC_DATA[self.rising_sign]['element']})
- Mercury: {self.chart.get('mercury', 'Unknown')}
- Venus: {self.chart.get('venus', 'Unknown')}
- Mars: {self.chart.get('mars', 'Unknown')}
- Jupiter: {self.chart.get('jupiter', 'Unknown')}
- Saturn: {self.chart.get('saturn', 'Unknown')}
- Midheaven: {self.chart.get('midheaven', 'Unknown')}
- North Node: {self.chart.get('north_node', 'Unknown')}

Quiz Responses:
- Astrology Knowledge: {self.user.get('astrology_familiarity', 'Beginner')}
- Main Goals: {', '.join(self.user.get('main_goals', ['Self-discovery']))}
- Outlook: {self.user.get('outlook', 'Optimist')}
- Decision Worry: {self.user.get('decision_worry', 'Sometimes')}
- Need to be Liked: {self.user.get('need_to_be_liked', 'Sometimes')}
- Logic vs Emotions: {self.user.get('logic_vs_emotions', 'Both')}
- Life Dreams: {self.user.get('life_dreams', 'Making an impact')}
- Motivations: {self.user.get('motivations', 'Creating something unique')}
- Relationship Status: {self.user.get('relationship_status', 'Unknown')}
- Love Language: {self.user.get('love_language', 'Quality time')}
- Overthink Relationships: {self.user.get('overthink_relationships', 'Sometimes')}
- Career Question: {self.user.get('career_question', 'Finding fulfillment')}

Numerology:
- Life Path Number: {self.life_path}
- Expression Number: {self.expression_number}
"""
    
    def generate_section(self, section_name, specific_prompt, max_tokens=1500):
        """Generate a specific section with fallback"""
        print(f"  Generating: {section_name}...")
        
        full_prompt = f"""You are writing a personalized astrology book. {specific_prompt}

{self._build_context()}

Write in second person ("you"). Be warm, insightful, and specific to THIS person's chart and answers. Avoid generic content."""

        result = call_claude_api(full_prompt, max_tokens)
        
        if result:
            self.content[section_name] = result
        else:
            self.content[section_name] = self._get_fallback(section_name)
        
        return self.content[section_name]
    
    def _get_fallback(self, section):
        """Provide fallback content if API fails"""
        fallbacks = {
            'introduction': f"Dear {self.first_name}, welcome to your personalized cosmic blueprint. Your unique combination of {self.sun_sign} Sun, {self.moon_sign} Moon, and {self.rising_sign} Rising creates a fascinating tapestry of energy that shapes every aspect of your life.",
            'sun_sign': f"As a {self.sun_sign} Sun, you embody the {ZODIAC_DATA[self.sun_sign]['element']} element's essence. Ruled by {ZODIAC_DATA[self.sun_sign]['ruler']}, you possess natural gifts and a unique approach to life that sets you apart.",
            'moon_sign': f"Your {self.moon_sign} Moon reveals your emotional nature and inner world. This {ZODIAC_DATA[self.moon_sign]['element']} Moon shapes how you process feelings and what you need to feel secure.",
            'rising_sign': f"With {self.rising_sign} Rising, you present a {ZODIAC_DATA[self.rising_sign]['element']} energy to the world. This is the mask you wear and the first impression you make.",
            'personality': f"Your personality is a unique blend of your {self.sun_sign} core identity, {self.moon_sign} emotional nature, and {self.rising_sign} outer expression.",
            'love': f"In love, your Venus and Mars placements reveal your romantic style and desires. Your {self.user.get('love_language', 'unique')} love language shows how you give and receive affection.",
            'career': f"Your professional path is illuminated by your Midheaven and supported by your natural talents. Your dreams of {self.user.get('life_dreams', 'making an impact')} align with your cosmic purpose.",
            'forecast': f"2026 brings significant opportunities for growth and transformation for {self.sun_sign}. Key themes include expansion, relationships, and personal evolution.",
            'numerology': f"Your Life Path Number {self.life_path} reveals your soul's journey. Combined with Expression Number {self.expression_number}, you have a unique numerological blueprint.",
            'tarot': f"The tarot cards aligned with your chart offer guidance for your current journey. Your Sun, Moon, and Rising signs each connect to specific Major Arcana cards.",
            'crystals': f"Certain crystals resonate with your unique chart. These stones can amplify your strengths and support your growth.",
            'closing': f"Dear {self.first_name}, may the wisdom in these pages guide you toward your highest potential. The stars have blessed you with a unique cosmic blueprint—now it's time to live it fully."
        }
        return fallbacks.get(section, f"Content for {section}...")
    
    def generate_all(self):
        """Generate all book content - optimized for fewer API calls"""
        print(f"\n🌟 Generating AI content for {self.name}...")
        print("=" * 50)
        
        # Main sections (12 API calls)
        self.generate_section('introduction', 
            "Write a warm, personalized introduction (3-4 paragraphs, ~350 words) welcoming them to their cosmic blueprint. Reference their birth moment as unique, their goals for seeking this book, and what they'll discover.")
        
        self.generate_section('sun_sign',
            f"Write a deep analysis of their {self.sun_sign} Sun (4-5 paragraphs, ~450 words). Cover the essence of {self.sun_sign}, how it manifests based on their quiz answers, strengths, shadows, and how it interacts with their Moon and Rising.")
        
        self.generate_section('moon_sign',
            f"Write about their {self.moon_sign} Moon (4 paragraphs, ~400 words). Cover emotional nature, security needs, intuitive gifts, and how this Moon colors their relationships and love language.")
        
        self.generate_section('rising_sign',
            f"Write about their {self.rising_sign} Rising (3-4 paragraphs, ~350 words). Cover first impressions, public persona, and how to use this Rising energy to their advantage.")
        
        self.generate_section('personality',
            f"Write a deep personality analysis (4-5 paragraphs, ~450 words) integrating their quiz answers about outlook, decision-making, need for approval, dreams, and motivations with their chart placements.")
        
        self.generate_section('love',
            f"Write about love and relationships (4-5 paragraphs, ~450 words). Cover Venus in {self.chart.get('venus')}, Mars in {self.chart.get('mars')}, their love language, and relationship patterns.")
        
        self.generate_section('career',
            f"Write about career and purpose (4 paragraphs, ~400 words). Address their Midheaven in {self.chart.get('midheaven')}, professional strengths, ideal paths, and their specific career question.")
        
        self.generate_section('forecast',
            f"Write 2026 yearly forecast (5 paragraphs, ~500 words). Cover overall themes, opportunities, challenges, love forecast, and career highlights with specific month references.")
        
        self.generate_section('numerology',
            f"Write numerology analysis (3-4 paragraphs, ~350 words). Explain Life Path {self.life_path} and Expression Number {self.expression_number} meanings and how they complement the chart.")
        
        self.generate_section('tarot',
            f"Create a tarot reading (4 paragraphs, ~400 words). Include birth cards for their Sun/Moon/Rising and a 5-card spread relevant to their goals.")
        
        self.generate_section('crystals',
            f"Write about crystals and rituals (3-4 paragraphs, ~350 words). Recommend 5 crystals for their specific placements and moon rituals for their Sun and Moon signs.")
        
        self.generate_section('closing',
            f"Write a warm closing (3 paragraphs, ~300 words). Summarize their unique blueprint, empower them, and end with an inspiring blessing.")
        
        # Compatibility - BATCHED into 2 API calls instead of 12
        print("  Generating: compatibility (batched)...")
        self.content['compatibility'] = {}
        
        # Batch 1: First 6 signs
        signs_batch1 = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo"]
        prompt1 = f"""Write compatibility analysis for {self.sun_sign} with each of these signs. For EACH sign, write 2 paragraphs (~150 words) covering chemistry, strengths, challenges, and give a percentage.

Format your response EXACTLY like this:
ARIES:
[content]
PERCENTAGE: XX%

TAURUS:
[content]
PERCENTAGE: XX%

(continue for Gemini, Cancer, Leo, Virgo)"""
        
        result1 = call_claude_api(f"{prompt1}\n\n{self._build_context()}", max_tokens=2500)
        if result1:
            self._parse_compatibility_batch(result1, signs_batch1)
        
        # Batch 2: Last 6 signs
        signs_batch2 = ["Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        prompt2 = f"""Write compatibility analysis for {self.sun_sign} with each of these signs. For EACH sign, write 2 paragraphs (~150 words) covering chemistry, strengths, challenges, and give a percentage.

Format your response EXACTLY like this:
LIBRA:
[content]
PERCENTAGE: XX%

SCORPIO:
[content]
PERCENTAGE: XX%

(continue for Sagittarius, Capricorn, Aquarius, Pisces)"""
        
        result2 = call_claude_api(f"{prompt2}\n\n{self._build_context()}", max_tokens=2500)
        if result2:
            self._parse_compatibility_batch(result2, signs_batch2)
        
        # Fill in any missing signs with fallback
        for sign in ZODIAC_ORDER:
            if sign not in self.content['compatibility']:
                self.content['compatibility'][sign] = f"{self.sun_sign} and {sign} create a unique dynamic worth exploring..."
        
        # Monthly forecasts - BATCHED into 2 API calls instead of 12
        print("  Generating: monthly forecasts (batched)...")
        self.content['monthly'] = {}
        
        # Batch 1: Jan-Jun
        months_h1 = ["January", "February", "March", "April", "May", "June"]
        prompt_h1 = f"""Write 2026 monthly forecasts for this person for January through June. For EACH month, write 2 paragraphs (~150 words) covering the month's energy, key dates, and advice.

Format your response EXACTLY like this:
JANUARY:
[content]

FEBRUARY:
[content]

(continue for March, April, May, June)"""
        
        result_h1 = call_claude_api(f"{prompt_h1}\n\n{self._build_context()}", max_tokens=2500)
        if result_h1:
            self._parse_monthly_batch(result_h1, months_h1)
        
        # Batch 2: Jul-Dec
        months_h2 = ["July", "August", "September", "October", "November", "December"]
        prompt_h2 = f"""Write 2026 monthly forecasts for this person for July through December. For EACH month, write 2 paragraphs (~150 words) covering the month's energy, key dates, and advice.

Format your response EXACTLY like this:
JULY:
[content]

AUGUST:
[content]

(continue for September, October, November, December)"""
        
        result_h2 = call_claude_api(f"{prompt_h2}\n\n{self._build_context()}", max_tokens=2500)
        if result_h2:
            self._parse_monthly_batch(result_h2, months_h2)
        
        # Fill in any missing months with fallback
        all_months = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        for month in all_months:
            if month not in self.content['monthly']:
                self.content['monthly'][month] = f"{month} 2026 brings opportunities for growth and transformation..."
        
        print("=" * 50)
        print("✅ All AI content generated!")
        return self.content
    
    def _parse_compatibility_batch(self, text, signs):
        """Parse batched compatibility response"""
        for sign in signs:
            # Try to find the section for this sign
            import re
            pattern = rf'{sign.upper()}:\s*(.*?)(?=(?:ARIES|TAURUS|GEMINI|CANCER|LEO|VIRGO|LIBRA|SCORPIO|SAGITTARIUS|CAPRICORN|AQUARIUS|PISCES):|\Z)'
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                self.content['compatibility'][sign] = match.group(1).strip()
    
    def _parse_monthly_batch(self, text, months):
        """Parse batched monthly forecast response"""
        for month in months:
            import re
            pattern = rf'{month.upper()}:\s*(.*?)(?=(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER):|\Z)'
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                self.content['monthly'][month] = match.group(1).strip()


# ============================================================
# PDF BOOK GENERATOR
# ============================================================

class OrastriaAIBook:
    """Generate the complete PDF book with AI content"""
    
    def __init__(self, user_data, chart_data, ai_content, output_path):
        self.user = user_data
        self.chart = chart_data
        self.content = ai_content
        self.output_path = output_path
        
        self.width, self.height = letter
        self.margin = 0.7 * inch
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
            self.birth_year, self.birth_month, self.birth_day = parts[0], parts[1], parts[2]
            # Format nicely
            months = ["", "January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
            self.birth_date_formatted = f"{months[int(self.birth_month)]} {int(self.birth_day)}, {self.birth_year}"
        else:
            self.birth_date_formatted = bd
    
    def draw_cover(self):
        """Draw the cover page"""
        c = self.c
        
        # Navy background
        c.setFillColor(NAVY)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        
        # Double border
        c.setStrokeColor(GOLD)
        c.setLineWidth(2)
        c.rect(0.4*inch, 0.4*inch, self.width - 0.8*inch, self.height - 0.8*inch)
        c.setLineWidth(1)
        c.rect(0.5*inch, 0.5*inch, self.width - 1*inch, self.height - 1*inch)
        
        # Top decorations
        c.setFont(FONT_BOLD, 24)
        c.setFillColor(GOLD)
        c.drawCentredString(0.8*inch, self.height - 0.8*inch, '☉')
        c.drawCentredString(self.width - 0.8*inch, self.height - 0.8*inch, '☽')
        
        # Title
        c.setFont(FONT_BOLD, 32)
        c.drawCentredString(self.width/2, self.height - 1.8*inch, "YOUR COSMIC")
        c.drawCentredString(self.width/2, self.height - 2.25*inch, "BLUEPRINT")
        
        # Line
        c.setLineWidth(1)
        c.line(2.2*inch, self.height - 2.5*inch, self.width - 2.2*inch, self.height - 2.5*inch)
        
        # Name
        c.setFillColor(white)
        c.setFont(FONT_BOLD, 26)
        c.drawCentredString(self.width/2, self.height - 3.2*inch, self.name)
        
        # Birth info
        c.setFillColor(SOFT_GOLD)
        c.setFont(FONT_REGULAR, 12)
        birth_time = f"{self.user.get('birth_time', '')} {self.user.get('birth_time_period', '')}".strip()
        c.drawCentredString(self.width/2, self.height - 3.6*inch, f"{self.birth_date_formatted}  •  {birth_time}")
        c.drawCentredString(self.width/2, self.height - 3.85*inch, self.user.get('birth_place', ''))
        
        # Zodiac circle
        center_y = self.height / 2 - 0.3*inch
        c.setStrokeColor(GOLD)
        c.setLineWidth(2)
        c.circle(self.width/2, center_y, 85)
        c.setLineWidth(1)
        c.circle(self.width/2, center_y, 95)
        
        # Zodiac symbol
        c.setFillColor(GOLD)
        c.setFont(FONT_BOLD, 64)
        c.drawCentredString(self.width/2, center_y - 20, ZODIAC_SYMBOLS.get(self.sun_sign, '★'))
        
        # Sign name
        c.setFont(FONT_BOLD, 16)
        c.drawCentredString(self.width/2, center_y - 55, self.sun_sign.upper())
        
        # Big Three
        c.setFont(FONT_REGULAR, 11)
        c.setFillColor(white)
        big_three = f"☉ Sun: {self.sun_sign}  •  ☽ Moon: {self.moon_sign}  •  ↑ Rising: {self.rising_sign}"
        c.drawCentredString(self.width/2, center_y - 115, big_three)
        
        # Branding
        c.setFillColor(GOLD)
        c.setFont(FONT_BOLD, 20)
        c.drawCentredString(self.width/2, 1.3*inch, "ORASTRIA")
        
        c.setFont(FONT_REGULAR, 10)
        c.drawCentredString(self.width/2, 1*inch, "Personalized Astrology  •  Written in the Stars")
        
        # Bottom moons
        c.setFont(FONT_REGULAR, 18)
        c.drawCentredString(0.8*inch, 0.8*inch, '☽')
        c.drawCentredString(self.width - 0.8*inch, 0.8*inch, '☽')
        
        c.showPage()
    
    def new_page(self, header=True):
        """Start new page with decorations"""
        self.page_num += 1
        c = self.c
        
        c.setFillColor(CREAM)
        c.rect(0, 0, self.width, self.height, fill=True, stroke=False)
        
        # Corner stars
        c.setFillColor(GOLD)
        c.setFont(FONT_REGULAR, 10)
        c.drawCentredString(50, self.height - 50, '✦')
        c.drawCentredString(self.width - 50, self.height - 50, '✦')
        c.drawCentredString(50, 50, '✦')
        c.drawCentredString(self.width - 50, 50, '✦')
        
        if header:
            c.setFillColor(NAVY)
            c.setFont(FONT_REGULAR, 10)
            c.drawCentredString(self.width/2, 35, f"— {self.page_num} —")
        
        return self.height - 80
    
    def draw_chapter(self, title, subtitle=None):
        """Draw chapter title page"""
        y = self.new_page()
        c = self.c
        
        c.setFillColor(GOLD)
        c.setFont(FONT_BOLD, 14)
        c.drawCentredString(self.width/2, self.height - 180, "✧ ✦ ✧")
        
        c.setFillColor(NAVY)
        c.setFont(FONT_BOLD, 28)
        c.drawCentredString(self.width/2, self.height - 280, title)
        
        if subtitle:
            c.setFont(FONT_REGULAR, 14)
            c.setFillColor(SOFT_GOLD)
            c.drawCentredString(self.width/2, self.height - 315, subtitle)
        
        c.setFillColor(GOLD)
        c.setFont(FONT_BOLD, 14)
        c.drawCentredString(self.width/2, self.height - 360, "✧ ✦ ✧")
        
        c.showPage()
    
    def draw_section_title(self, text, y):
        """Draw section title"""
        self.c.setFillColor(NAVY)
        self.c.setFont(FONT_BOLD, 16)
        self.c.drawString(self.margin, y, text)
        self.c.setStrokeColor(GOLD)
        self.c.setLineWidth(1.5)
        self.c.line(self.margin, y - 5, self.margin + 50, y - 5)
        return y - 30
    
    def draw_ai_content(self, text, y, width=None):
        """Draw AI-generated text content with word wrapping"""
        if not text:
            return y
        
        c = self.c
        c.setFillColor(NAVY)
        c.setFont(FONT_REGULAR, 11)
        
        if width is None:
            width = self.width - 2 * self.margin
        
        wrapper = textwrap.TextWrapper(width=int(width / 5.5))  # Approximate chars
        
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
                    c.setFont(FONT_REGULAR, 11)
                
                c.drawString(self.margin, y, line)
                y -= 15
            
            y -= 8  # Paragraph spacing
        
        return y
    
    def draw_compat_bar(self, sign, text, y):
        """Draw compatibility entry"""
        c = self.c
        if y < self.margin + 80:
            c.showPage()
            y = self.new_page()
        
        # Sign header
        c.setFillColor(GOLD)
        c.setFont(FONT_BOLD, 14)
        c.drawString(self.margin, y, ZODIAC_SYMBOLS.get(sign, '★'))
        c.setFillColor(NAVY)
        c.setFont(FONT_BOLD, 12)
        c.drawString(self.margin + 25, y, sign)
        
        y -= 20
        
        # Content
        y = self.draw_ai_content(text, y)
        
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
        y = self.draw_ai_content(self.content.get('introduction', ''), y)
        self.c.showPage()
        
        # The Big Three
        self.draw_chapter("The Big Three", "Sun, Moon & Rising")
        
        # Sun Sign
        y = self.new_page()
        self.c.setFillColor(GOLD)
        self.c.setFont(FONT_BOLD, 36)
        self.c.drawCentredString(self.width/2, self.height - 100, ZODIAC_SYMBOLS.get(self.sun_sign, '★'))
        self.c.setFillColor(NAVY)
        self.c.setFont(FONT_BOLD, 18)
        self.c.drawCentredString(self.width/2, self.height - 140, f"Your Sun in {self.sun_sign}")
        y = self.height - 180
        y = self.draw_ai_content(self.content.get('sun_sign', ''), y)
        self.c.showPage()
        
        # Moon Sign
        y = self.new_page()
        self.c.setFillColor(GOLD)
        self.c.setFont(FONT_BOLD, 36)
        self.c.drawCentredString(self.width/2, self.height - 100, '☽')
        self.c.setFillColor(NAVY)
        self.c.setFont(FONT_BOLD, 18)
        self.c.drawCentredString(self.width/2, self.height - 140, f"Your Moon in {self.moon_sign}")
        y = self.height - 180
        y = self.draw_ai_content(self.content.get('moon_sign', ''), y)
        self.c.showPage()
        
        # Rising Sign
        y = self.new_page()
        self.c.setFillColor(GOLD)
        self.c.setFont(FONT_BOLD, 36)
        self.c.drawCentredString(self.width/2, self.height - 100, '↑')
        self.c.setFillColor(NAVY)
        self.c.setFont(FONT_BOLD, 18)
        self.c.drawCentredString(self.width/2, self.height - 140, f"Your {self.rising_sign} Rising")
        y = self.height - 180
        y = self.draw_ai_content(self.content.get('rising_sign', ''), y)
        self.c.showPage()
        
        # Personality
        self.draw_chapter("Your Inner World", "Deep Personality Analysis")
        y = self.new_page()
        y = self.draw_section_title("Understanding Your Psychology", y)
        y = self.draw_ai_content(self.content.get('personality', ''), y)
        self.c.showPage()
        
        # Love
        self.draw_chapter("Love & Relationships", "Your Heart's Blueprint")
        y = self.new_page()
        y = self.draw_section_title("Your Romantic Nature", y)
        y = self.draw_ai_content(self.content.get('love', ''), y)
        self.c.showPage()
        
        # Compatibility
        self.draw_chapter("Compatibility Guide", "Your Match with All 12 Signs")
        y = self.new_page()
        for sign in ZODIAC_ORDER:
            y = self.draw_compat_bar(sign, self.content.get('compatibility', {}).get(sign, ''), y)
        self.c.showPage()
        
        # Career
        self.draw_chapter("Career & Purpose", "Your Professional Destiny")
        y = self.new_page()
        y = self.draw_section_title("Your Career Blueprint", y)
        y = self.draw_ai_content(self.content.get('career', ''), y)
        self.c.showPage()
        
        # 2026 Forecast
        self.draw_chapter("Your Year Ahead", "2026 Forecast")
        y = self.new_page()
        y = self.draw_section_title("2026 Overview", y)
        y = self.draw_ai_content(self.content.get('forecast', ''), y)
        self.c.showPage()
        
        # Monthly Forecasts
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        for month in months:
            y = self.new_page()
            self.c.setFillColor(GOLD)
            self.c.setFont(FONT_BOLD, 12)
            self.c.drawCentredString(self.width/2, self.height - 80, "✧ ✦ ✧")
            self.c.setFillColor(NAVY)
            self.c.setFont(FONT_BOLD, 22)
            self.c.drawCentredString(self.width/2, self.height - 120, f"{month} 2026")
            y = self.height - 160
            y = self.draw_ai_content(self.content.get('monthly', {}).get(month, ''), y)
            self.c.showPage()
        
        # Numerology
        self.draw_chapter("Numerology", "The Numbers of Your Life")
        y = self.new_page()
        life_path = calculate_life_path(self.user.get('birth_date', '2000-01-01'))
        y = self.draw_section_title(f"Life Path {life_path}", y)
        y = self.draw_ai_content(self.content.get('numerology', ''), y)
        self.c.showPage()
        
        # Tarot
        self.draw_chapter("Tarot Guidance", "Cards for Your Journey")
        y = self.new_page()
        y = self.draw_section_title("Your Tarot Reading", y)
        y = self.draw_ai_content(self.content.get('tarot', ''), y)
        self.c.showPage()
        
        # Crystals
        self.draw_chapter("Crystals & Rituals", "Tools for Your Path")
        y = self.new_page()
        y = self.draw_section_title("Your Power Crystals", y)
        y = self.draw_ai_content(self.content.get('crystals', ''), y)
        self.c.showPage()
        
        # Closing
        self.draw_chapter("Closing Thoughts", "Your Journey Continues")
        y = self.new_page()
        y = self.draw_section_title(f"Dear {self.first_name},", y)
        y = self.draw_ai_content(self.content.get('closing', ''), y)
        
        # Final branding
        y -= 40
        self.c.setFillColor(NAVY)
        self.c.setFont(FONT_BOLD, 14)
        self.c.drawString(self.margin, y, "With cosmic blessings,")
        self.c.setFillColor(GOLD)
        self.c.setFont(FONT_BOLD, 24)
        self.c.drawString(self.margin, y - 30, "ORASTRIA")
        
        self.c.save()
        print(f"✅ Book saved: {self.output_path}")
        print(f"📄 Total pages: {self.page_num}")
        return self.output_path


# ============================================================
# MAIN FUNCTION - Call this from your Flask API
# ============================================================

def generate_ai_book(user_data, chart_data, output_path):
    """
    Main function to generate a complete AI-powered astrology book
    
    Args:
        user_data: dict with user info and quiz answers
        chart_data: dict with astrological placements
        output_path: where to save the PDF
    
    Returns:
        path to generated PDF
    """
    # Generate AI content
    ai_gen = AIContentGenerator(user_data, chart_data)
    content = ai_gen.generate_all()
    
    # Build PDF
    book = OrastriaAIBook(user_data, chart_data, content, output_path)
    return book.build()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    # Example user data
    user_data = {
        "name": "Taylor Swift",
        "birth_date": "1989-12-13",
        "birth_time": "05:17",
        "birth_time_period": "AM",
        "birth_place": "West Reading, Pennsylvania, USA",
        "astrology_familiarity": "Intermediate",
        "main_goals": ["Discover my life path & purpose", "Improve my relationships"],
        "outlook": "Optimist",
        "decision_worry": "Somewhat agree",
        "need_to_be_liked": "Sometimes",
        "logic_vs_emotions": "A bit of both",
        "life_dreams": "Making significant impact in my field",
        "motivations": "Creating something unique",
        "relationship_status": "Single",
        "love_language": "Words of affirmation",
        "overthink_relationships": "Often",
        "career_question": "What work will bring me joy and fulfillment?",
    }
    
    chart_data = {
        "sun_sign": "Sagittarius",
        "moon_sign": "Cancer",
        "rising_sign": "Scorpio",
        "mercury": "Capricorn",
        "venus": "Aquarius",
        "mars": "Scorpio",
        "jupiter": "Cancer",
        "saturn": "Capricorn",
        "midheaven": "Leo",
        "north_node": "Aquarius",
    }
    
    output = generate_ai_book(user_data, chart_data, "/tmp/orastria_ai_test.pdf")
    print(f"\n🎉 Generated: {output}")
