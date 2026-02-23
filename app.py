#!/usr/bin/env python3
"""
Orastria AI Book Generator - Flask API v2.1
- Prokerala API integration for chart calculations
- Updated for shortened quiz (2026 version)
- Backward compatible with existing endpoints
"""

from flask import Flask, request, jsonify
import os
import uuid
import tempfile
import boto3
from botocore.config import Config

from orastria_ai_book_complete import generate_ai_book, generate_book

app = Flask(__name__)

# Backblaze B2 configuration
B2_KEY_ID = os.environ.get('B2_KEY_ID', '')
B2_APP_KEY = os.environ.get('B2_APP_KEY', '')
B2_BUCKET = os.environ.get('B2_BUCKET_NAME', os.environ.get('B2_BUCKET', 'orastria'))
B2_ENDPOINT = os.environ.get('B2_ENDPOINT', 'https://s3.us-east-005.backblazeb2.com')

# ----------------------------------------------------------------
# Color aliases — maps any user-supplied color string to a valid
# COLOR_THEMES key defined in orastria_ai_book_complete.py
# ----------------------------------------------------------------
COLOR_ALIASES = {
    'purple':       'dark purple',
    'dark_purple':  'dark purple',
    'darkpurple':   'dark purple',
    'violet':       'dark purple',
    'indigo':       'dark purple',
    'bright_black': 'brighter black',
    'brightblack':  'brighter black',
    'dark':         'black',
    'burgundy':     'maroon',
    'wine':         'maroon',
    'blue':         'navy',
    'dark_blue':    'navy',
    'cream':        'creamy',
    'beige':        'creamy',
    'ivory':        'creamy',
    'crimson':      'red',
    'scarlet':      'red',
    'forest':       'green',
    'dark_green':   'green',
}

VALID_COLORS = {'black', 'green', 'dark purple', 'brighter black', 'red', 'creamy', 'navy', 'maroon'}


def normalize_color(raw_color: str) -> str:
    """Normalize any color string to a valid COLOR_THEMES key."""
    if not raw_color:
        return 'navy'
    cleaned = raw_color.strip().lower()
    if cleaned in VALID_COLORS:
        return cleaned
    return COLOR_ALIASES.get(cleaned, 'navy')


def upload_to_b2(file_path, file_name):
    """Upload PDF to Backblaze B2 and return public URL."""
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=B2_ENDPOINT,
            aws_access_key_id=B2_KEY_ID,
            aws_secret_access_key=B2_APP_KEY,
            config=Config(signature_version='s3v4')
        )
        s3.upload_file(
            file_path,
            B2_BUCKET,
            file_name,
            ExtraArgs={'ContentType': 'application/pdf'}
        )
        url = f"{B2_ENDPOINT}/{B2_BUCKET}/{file_name}"
        return url
    except Exception as e:
        print(f"B2 upload error: {e}")
        return None


# ================================================================
# HEALTH CHECK
# ================================================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "orastria-ai-book-generator",
        "version": "2.1",
        "features": [
            "prokerala_integration",
            "shortened_quiz_support",
            "claude_ai_content",
            "colored_compatibility_bars",
            "custom_book_colors"
        ]
    })


# ================================================================
# PRIMARY ENDPOINT  — used by n8n / Bubble via generate-simple
# ================================================================

@app.route('/generate-simple', methods=['POST'])
def generate_simple():
    """
    Simplified endpoint accepting flat data from Bubble / n8n.
    Supports the 2026 shortened quiz schema.
    Required: first_name (or name), birth_date, birth_place
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # ── Color: accept cover_color, book_color, color, bookColor ──
        raw_color = (
            data.get('cover_color') or
            data.get('book_color') or
            data.get('bookColor') or
            data.get('color') or
            'navy'
        )
        book_color = normalize_color(raw_color)

        # ── Main goals: accept array or single string ──
        raw_goals = data.get('main_goals') or data.get('mainGoals') or data.get('goals')
        if raw_goals is None:
            # New quiz sends a single string field
            single_goal = data.get('main_goal') or data.get('mainGoal') or ''
            main_goals = [single_goal] if single_goal else []
        elif isinstance(raw_goals, str):
            main_goals = [raw_goals] if raw_goals else []
        else:
            main_goals = raw_goals  # already a list

        # ── Build normalised user_data dict ──
        user_data = {
            # Identity
            "first_name":   data.get('first_name') or data.get('firstName') or '',
            "last_name":    data.get('last_name')  or data.get('lastName')  or '',
            "name": (
                data.get('name') or
                f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
            ),
            "gender": data.get('gender') or '',
            "email":  data.get('email')  or '',
            "user_id": data.get('user_id') or '',

            # Birth info — new quiz sends pre-formatted ISO values
            "birth_date":  data.get('birth_date')  or data.get('date_birth')   or data.get('birthDate') or data.get('dob') or '',
            "birth_time":  data.get('birth_time')  or data.get('birthTime')    or '12:00',
            "birth_time_period": data.get('birth_time_period') or data.get('birthTimePeriod') or '',
            "birth_place": data.get('birth_place') or data.get('place_of_birth') or data.get('birthPlace') or data.get('location') or '',

            # Astrology knowledge — new quiz omits this, default to Intermediate
            # so every user doesn't automatically get the beginner glossary
            "astrology_familiarity": (
                data.get('astrology_familiarity') or
                data.get('astrologyFamiliarity') or
                data.get('familiarity') or
                'Intermediate'
            ),

            # Goals — new quiz: single main_goal string
            "main_goals":  main_goals,
            "life_dreams": data.get('life_dreams') or data.get('lifeDreams') or data.get('dreams') or '',
            "motivations": data.get('motivations') or data.get('motivation') or '',

            # Relationships — new quiz sends relationship_status directly
            "relationship_status":       data.get('relationship_status') or data.get('relationshipStatus') or '',
            "relationship_goals":        data.get('relationship_goals')  or data.get('relationshipGoals')  or [],
            "relationship_satisfaction": data.get('relationship_satisfaction') or data.get('relationshipSatisfaction') or '',
            "unresolved_romantic_feelings": (
                data.get('unresolved_romantic_feelings') or
                data.get('unresolvedFeelings') or
                'No'
            ),

            # Personality — omitted from new quiz; left empty for graceful AI fallback
            "decision_worry":           data.get('decision_worry')           or '',
            "need_to_be_liked":         data.get('need_to_be_liked')         or '',
            "insecurity_with_strangers": data.get('insecurity_with_strangers') or '',
            "outlook":                  data.get('outlook') or '',

            # Love — new quiz sends logic_vs_emotions
            "love_language":          data.get('love_language')          or data.get('loveLanguage')          or '',
            "logic_vs_emotions":      data.get('logic_vs_emotions')      or data.get('logicVsEmotions')      or '',
            "overthink_relationships": data.get('overthink_relationships') or data.get('overthinkRelationships') or '',
            "desired_partner_traits": data.get('desired_partner_traits')  or data.get('desiredPartnerTraits')  or [],

            # Career
            "career_question": data.get('career_question') or data.get('careerQuestion') or '',

            # Book preferences (omitted from new quiz — empty lists deactivate those sections)
            "birth_chart_includes": data.get('birth_chart_includes') or data.get('birthChartIncludes') or [],
            "important_dates":      data.get('important_dates')      or data.get('importantDates')      or [],
            "additional_topics":    data.get('additional_topics')    or data.get('additionalTopics')    or [],

            # Life events
            "significant_life_event_soon": (
                data.get('significant_life_event_soon') or
                data.get('significantLifeEvent') or
                'No'
            ),

            # Book customization (already normalised above)
            "book_color": book_color,

            # Purchase / tracking metadata (passed through, not used in book)
            "sun_sign":           data.get('sun_sign')   or data.get('sunSign')   or '',
            "moon_sign":          data.get('moon_sign')  or data.get('moonSign')  or '',
            "rising_sign":        data.get('rising_sign') or data.get('risingSign') or data.get('ascendant') or '',
            "mercury":            data.get('mercury')    or '',
            "venus":              data.get('venus')      or '',
            "mars":               data.get('mars')       or '',
            "jupiter":            data.get('jupiter')    or '',
            "saturn":             data.get('saturn')     or '',
            "midheaven":          data.get('midheaven')  or '',
            "north_node":         data.get('north_node') or data.get('northNode') or '',

            # Stripe / tracking
            "stripe_session_id":  data.get('stripe_session_id')  or '',
            "purchase_timestamp": data.get('purchase_timestamp') or '',
            "price":              data.get('price')    or '',
            "currency":           data.get('currency') or '',
            "variant":            data.get('variant')  or '',
            "fbclid":             data.get('fbclid')   or '',
            "submitted_at":       data.get('submitted_at') or '',
        }

        # Ensure name is always set
        if not user_data['name'] or not user_data['name'].strip():
            user_data['name'] = user_data['first_name'] or 'Friend'

        # ── Validate minimum required fields ──
        missing = []
        if not user_data['first_name'] and not user_data['name']:
            missing.append('first_name')
        if not user_data['birth_date']:
            missing.append('birth_date')
        if not user_data['birth_place']:
            missing.append('birth_place')
        if missing:
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

        # ── Generate ──
        book_id   = str(uuid.uuid4())[:8]
        name      = user_data['name'] or user_data['first_name']
        safe_name = "".join(c for c in name if c.isalnum() or c == ' ').replace(' ', '_')
        filename  = f"orastria_{safe_name}_{book_id}.pdf"

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            temp_path = tmp.name

        print(f"🌟 Generating book for {name} | color={book_color} | goals={main_goals}")
        generate_book(user_data, temp_path)

        download_url = upload_to_b2(temp_path, filename)
        os.unlink(temp_path)

        return jsonify({
            "success": True,
            "download_url": download_url,
            "filename": filename,
            "user": name,
            "book_color": book_color,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ================================================================
# LEGACY ENDPOINT — /generate  (kept for backward compatibility)
# ================================================================

@app.route('/generate', methods=['POST'])
def generate_book_endpoint():
    """
    Legacy endpoint. Accepts user_data + chart_data as separate objects.
    Use /generate-simple for new integrations.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        user_data  = data.get('user_data', {})
        chart_data = data.get('chart_data', {})

        name = user_data.get('name') or f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
        if not name:
            return jsonify({"error": "Missing user name"}), 400
        if not chart_data.get('sun_sign'):
            return jsonify({"error": "Missing sun_sign in chart_data"}), 400

        # Normalise color on legacy path too
        user_data['book_color'] = normalize_color(
            user_data.get('book_color') or user_data.get('cover_color') or 'navy'
        )

        book_id   = str(uuid.uuid4())[:8]
        safe_name = "".join(c for c in name if c.isalnum() or c == ' ').replace(' ', '_')
        filename  = f"orastria_{safe_name}_{book_id}.pdf"

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            temp_path = tmp.name

        print(f"🌟 Generating AI book for {name}...")
        generate_ai_book(user_data, chart_data, temp_path)

        download_url = upload_to_b2(temp_path, filename)
        os.unlink(temp_path)

        if download_url:
            return jsonify({
                "success": True,
                "download_url": download_url,
                "filename": filename,
                "message": f"Book generated for {name}"
            })
        else:
            return jsonify({"success": False, "error": "Failed to upload to storage"}), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ================================================================
# FIELD REFERENCE
# ================================================================

@app.route('/fields', methods=['GET'])
def list_fields():
    """List all supported input fields for /generate-simple."""
    return jsonify({
        "required_fields": ["first_name (or name)", "birth_date", "birth_place"],
        "new_quiz_fields": {
            "description": "Fields sent by the 2026 shortened quiz",
            "fields": [
                "first_name", "last_name", "email", "user_id",
                "date_birth (or birth_date)", "birth_time", "place_of_birth (or birth_place)",
                "sun_sign", "gender", "relationship_status",
                "main_goal", "logic_vs_emotions", "cover_color",
                "variant", "stripe_session_id", "purchase_timestamp",
                "price", "currency", "fbclid", "submitted_at"
            ]
        },
        "optional_legacy_fields": {
            "goals": ["main_goals", "life_dreams", "motivations"],
            "relationships": ["relationship_goals", "relationship_satisfaction", "unresolved_romantic_feelings"],
            "personality": ["decision_worry", "need_to_be_liked", "insecurity_with_strangers", "outlook"],
            "love": ["love_language", "overthink_relationships", "desired_partner_traits"],
            "career": ["career_question"],
            "book_preferences": ["birth_chart_includes", "important_dates", "additional_topics"],
            "life_events": ["significant_life_event_soon"],
        },
        "book_color_options": list({
            "navy", "black", "green", "dark purple", "brighter black",
            "red", "creamy", "maroon"
        }),
        "color_aliases": COLOR_ALIASES,
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
