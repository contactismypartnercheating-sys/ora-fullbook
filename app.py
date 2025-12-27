#!/usr/bin/env python3
"""
Orastria AI Book Generator - Flask API
- Prokerala API integration for chart calculations
- ALL questionnaire fields for deep personalization
- Backward compatible with existing endpoints
"""

from flask import Flask, request, jsonify
import os
import uuid
import tempfile
import boto3
from botocore.config import Config

# Import both functions for flexibility
from orastria_ai_book_complete import generate_ai_book, generate_book

app = Flask(__name__)

# Backblaze B2 configuration
B2_KEY_ID = os.environ.get('B2_KEY_ID', '')
B2_APP_KEY = os.environ.get('B2_APP_KEY', '')
B2_BUCKET = os.environ.get('B2_BUCKET_NAME', os.environ.get('B2_BUCKET', 'orastria'))
B2_ENDPOINT = os.environ.get('B2_ENDPOINT', 'https://s3.us-east-005.backblazeb2.com')


def upload_to_b2(file_path, file_name):
    """Upload PDF to Backblaze B2"""
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


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "orastria-ai-book-generator",
        "version": "2.0",
        "features": [
            "prokerala_integration",
            "all_questionnaire_fields",
            "claude_ai_content",
            "colored_compatibility_bars",
            "custom_book_colors"
        ]
    })


@app.route('/generate', methods=['POST'])
def generate_book_endpoint():
    """
    Generate a personalized AI astrology book.
    BACKWARD COMPATIBLE - accepts user_data and chart_data separately.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        user_data = data.get('user_data', {})
        chart_data = data.get('chart_data', {})
        
        name = user_data.get('name') or f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
        if not name:
            return jsonify({"error": "Missing user name"}), 400
        
        if not chart_data.get('sun_sign'):
            return jsonify({"error": "Missing sun_sign in chart_data"}), 400
        
        book_id = str(uuid.uuid4())[:8]
        safe_name = "".join(c for c in name if c.isalnum() or c == ' ').replace(' ', '_')
        filename = f"orastria_{safe_name}_{book_id}.pdf"
        
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
            return jsonify({
                "success": False,
                "error": "Failed to upload to storage"
            }), 500
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/generate-simple', methods=['POST'])
def generate_simple():
    """
    Simplified endpoint that accepts flat data from Bubble/n8n.
    Uses Prokerala for chart calculations if credentials available.
    Supports ALL questionnaire fields.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Map various possible field names to our standard format
        user_data = {
            # Personal
            "first_name": data.get('first_name') or data.get('firstName') or data.get('name', ''),
            "last_name": data.get('last_name') or data.get('lastName') or '',
            "name": data.get('name') or f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
            "gender": data.get('gender') or '',
            "email": data.get('email') or '',
            
            # Birth
            "birth_date": data.get('birth_date') or data.get('birthDate') or data.get('dob') or '',
            "birth_time": data.get('birth_time') or data.get('birthTime') or '12:00',
            "birth_time_period": data.get('birth_time_period') or data.get('birthTimePeriod') or 'PM',
            "birth_place": data.get('birth_place') or data.get('birthPlace') or data.get('location') or '',
            
            # Knowledge
            "astrology_familiarity": data.get('astrology_familiarity') or data.get('astrologyFamiliarity') or data.get('familiarity') or 'Beginner',
            
            # Goals
            "main_goals": data.get('main_goals') or data.get('mainGoals') or data.get('goals') or [],
            "life_dreams": data.get('life_dreams') or data.get('lifeDreams') or data.get('dreams') or '',
            "motivations": data.get('motivations') or data.get('motivation') or '',
            
            # Relationships
            "relationship_status": data.get('relationship_status') or data.get('relationshipStatus') or '',
            "relationship_goals": data.get('relationship_goals') or data.get('relationshipGoals') or [],
            "relationship_satisfaction": data.get('relationship_satisfaction') or data.get('relationshipSatisfaction') or '',
            "unresolved_romantic_feelings": data.get('unresolved_romantic_feelings') or data.get('unresolvedFeelings') or data.get('unresolvedRomanticFeelings') or 'No',
            
            # Personality
            "decision_worry": data.get('decision_worry') or data.get('decisionWorry') or '',
            "need_to_be_liked": data.get('need_to_be_liked') or data.get('needToBeLiked') or '',
            "insecurity_with_strangers": data.get('insecurity_with_strangers') or data.get('insecurityWithStrangers') or '',
            "outlook": data.get('outlook') or 'Realist',
            
            # Love
            "love_language": data.get('love_language') or data.get('loveLanguage') or '',
            "logic_vs_emotions": data.get('logic_vs_emotions') or data.get('logicVsEmotions') or 'A bit of both',
            "overthink_relationships": data.get('overthink_relationships') or data.get('overthinkRelationships') or '',
            "desired_partner_traits": data.get('desired_partner_traits') or data.get('desiredPartnerTraits') or [],
            
            # Career
            "career_question": data.get('career_question') or data.get('careerQuestion') or '',
            
            # Book preferences
            "birth_chart_includes": data.get('birth_chart_includes') or data.get('birthChartIncludes') or [],
            "important_dates": data.get('important_dates') or data.get('importantDates') or [],
            "additional_topics": data.get('additional_topics') or data.get('additionalTopics') or [],
            
            # Life events
            "significant_life_event_soon": data.get('significant_life_event_soon') or data.get('significantLifeEvent') or data.get('significantLifeEventSoon') or 'No',
            
            # Book customization
            "book_color": data.get('book_color') or data.get('bookColor') or data.get('color') or 'navy',
            
            # Fallback chart data (used if Prokerala fails)
            "sun_sign": data.get('sun_sign') or data.get('sunSign') or '',
            "moon_sign": data.get('moon_sign') or data.get('moonSign') or '',
            "rising_sign": data.get('rising_sign') or data.get('risingSign') or data.get('ascendant') or '',
            "mercury": data.get('mercury') or '',
            "venus": data.get('venus') or '',
            "mars": data.get('mars') or '',
            "jupiter": data.get('jupiter') or '',
            "saturn": data.get('saturn') or '',
            "midheaven": data.get('midheaven') or '',
            "north_node": data.get('north_node') or data.get('northNode') or '',
        }
        
        # Ensure name is set
        if not user_data['name'] or user_data['name'].strip() == '':
            user_data['name'] = user_data['first_name'] or 'Friend'
        
        # Validate minimum required fields
        if not user_data['first_name'] and not user_data['name']:
            return jsonify({"error": "Missing name or first_name"}), 400
        
        if not user_data['birth_date']:
            return jsonify({"error": "Missing birth_date"}), 400
        
        if not user_data['birth_place']:
            return jsonify({"error": "Missing birth_place"}), 400
        
        # Generate
        book_id = str(uuid.uuid4())[:8]
        name = user_data['name'] or user_data['first_name']
        safe_name = "".join(c for c in name if c.isalnum() or c == ' ').replace(' ', '_')
        filename = f"orastria_{safe_name}_{book_id}.pdf"
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            temp_path = tmp.name
        
        # Use generate_book which includes Prokerala integration
        generate_book(user_data, temp_path)
        
        download_url = upload_to_b2(temp_path, filename)
        os.unlink(temp_path)
        
        return jsonify({
            "success": True,
            "download_url": download_url,
            "filename": filename
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/fields', methods=['GET'])
def list_fields():
    """List all supported questionnaire fields"""
    return jsonify({
        "required_fields": ["first_name (or name)", "birth_date", "birth_place"],
        "all_supported_fields": {
            "personal": ["first_name", "last_name", "gender", "email"],
            "birth": ["birth_date", "birth_time", "birth_time_period", "birth_place"],
            "knowledge": ["astrology_familiarity"],
            "goals": ["main_goals", "life_dreams", "motivations"],
            "relationships": ["relationship_status", "relationship_goals", "relationship_satisfaction", "unresolved_romantic_feelings"],
            "personality": ["decision_worry", "need_to_be_liked", "insecurity_with_strangers", "outlook"],
            "love": ["love_language", "logic_vs_emotions", "overthink_relationships", "desired_partner_traits"],
            "career": ["career_question"],
            "book_preferences": ["birth_chart_includes", "important_dates", "additional_topics"],
            "life_events": ["significant_life_event_soon"],
            "customization": ["book_color"],
            "fallback_chart": ["sun_sign", "moon_sign", "rising_sign", "mercury", "venus", "mars", "jupiter", "saturn", "midheaven", "north_node"]
        },
        "book_color_options": ["black", "green", "dark purple", "brighter black", "red", "creamy", "navy", "maroon"]
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
