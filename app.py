#!/usr/bin/env python3
"""
Orastria AI Book Generator - Flask API
Deploy to Railway
"""

from flask import Flask, request, jsonify
import os
import uuid
import tempfile
import boto3
from botocore.config import Config

# Import the book generator
from orastria_ai_book_complete import generate_ai_book

app = Flask(__name__)

# Backblaze B2 configuration (use your existing setup)
B2_KEY_ID = os.environ.get('B2_KEY_ID', 'your_key_id')
B2_APP_KEY = os.environ.get('B2_APP_KEY', 'your_app_key')
B2_BUCKET = os.environ.get('B2_BUCKET', 'orastria-books')
B2_ENDPOINT = os.environ.get('B2_ENDPOINT', 'https://s3.us-west-004.backblazeb2.com')

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
        
        # Generate download URL
        url = f"{B2_ENDPOINT}/{B2_BUCKET}/{file_name}"
        return url
    except Exception as e:
        print(f"B2 upload error: {e}")
        return None


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "orastria-ai-book-generator"})


@app.route('/generate', methods=['POST'])
def generate_book():
    """
    Generate a personalized AI astrology book
    
    Expected JSON payload:
    {
        "user_data": {
            "name": "Taylor Swift",
            "birth_date": "1989-12-13",
            "birth_time": "05:17",
            "birth_time_period": "AM",
            "birth_place": "West Reading, Pennsylvania, USA",
            "astrology_familiarity": "Intermediate",
            "main_goals": ["Discover my life path & purpose"],
            "outlook": "Optimist",
            "decision_worry": "Somewhat agree",
            "need_to_be_liked": "Sometimes",
            "logic_vs_emotions": "A bit of both",
            "life_dreams": "Making significant impact",
            "motivations": "Creating something unique",
            "relationship_status": "Single",
            "love_language": "Words of affirmation",
            "overthink_relationships": "Often",
            "career_question": "What work will bring me joy?"
        },
        "chart_data": {
            "sun_sign": "Sagittarius",
            "moon_sign": "Cancer",
            "rising_sign": "Scorpio",
            "mercury": "Capricorn",
            "venus": "Aquarius",
            "mars": "Scorpio",
            "jupiter": "Cancer",
            "saturn": "Capricorn",
            "midheaven": "Leo",
            "north_node": "Aquarius"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        user_data = data.get('user_data', {})
        chart_data = data.get('chart_data', {})
        
        if not user_data.get('name'):
            return jsonify({"error": "Missing user name"}), 400
        
        if not chart_data.get('sun_sign'):
            return jsonify({"error": "Missing sun_sign in chart_data"}), 400
        
        # Generate unique filename
        book_id = str(uuid.uuid4())[:8]
        safe_name = "".join(c for c in user_data['name'] if c.isalnum() or c == ' ').replace(' ', '_')
        filename = f"orastria_{safe_name}_{book_id}.pdf"
        
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            temp_path = tmp.name
        
        # Generate the book
        print(f"🌟 Generating AI book for {user_data['name']}...")
        generate_ai_book(user_data, chart_data, temp_path)
        
        # Upload to B2
        download_url = upload_to_b2(temp_path, filename)
        
        # Clean up
        os.unlink(temp_path)
        
        if download_url:
            return jsonify({
                "success": True,
                "download_url": download_url,
                "filename": filename,
                "message": f"Book generated for {user_data['name']}"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to upload to storage"
            }), 500
            
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/generate-simple', methods=['POST'])
def generate_simple():
    """
    Simplified endpoint that accepts flat data from n8n webhook
    """
    try:
        data = request.get_json()
        
        # Extract and organize data
        user_data = {
            "name": f"{data.get('name', '')} {data.get('last_name', '')}".strip(),
            "birth_date": data.get('birth_date', ''),
            "birth_time": data.get('birth_time', ''),
            "birth_time_period": data.get('birth_time_period', ''),
            "birth_place": data.get('birth_place', ''),
            "astrology_familiarity": data.get('astrology_familiarity', 'Beginner'),
            "main_goals": data.get('main_goals', []),
            "outlook": data.get('outlook', 'Optimist'),
            "decision_worry": data.get('decision_worry', ''),
            "need_to_be_liked": data.get('need_to_be_liked', ''),
            "logic_vs_emotions": data.get('logic_vs_emotions', ''),
            "life_dreams": data.get('life_dreams', ''),
            "motivations": data.get('motivations', ''),
            "relationship_status": data.get('relationship_status', ''),
            "love_language": data.get('love_language', ''),
            "overthink_relationships": data.get('overthink_relationships', ''),
            "career_question": data.get('career_question', ''),
        }
        
        chart_data = {
            "sun_sign": data.get('sun_sign', 'Aries'),
            "moon_sign": data.get('moon_sign', 'Aries'),
            "rising_sign": data.get('rising_sign', 'Aries'),
            "mercury": data.get('mercury', ''),
            "venus": data.get('venus', ''),
            "mars": data.get('mars', ''),
            "jupiter": data.get('jupiter', ''),
            "saturn": data.get('saturn', ''),
            "midheaven": data.get('midheaven', ''),
            "north_node": data.get('north_node', ''),
        }
        
        # Use the main generate logic
        book_id = str(uuid.uuid4())[:8]
        safe_name = "".join(c for c in user_data['name'] if c.isalnum() or c == ' ').replace(' ', '_')
        filename = f"orastria_{safe_name}_{book_id}.pdf"
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            temp_path = tmp.name
        
        generate_ai_book(user_data, chart_data, temp_path)
        
        download_url = upload_to_b2(temp_path, filename)
        os.unlink(temp_path)
        
        return jsonify({
            "success": True,
            "download_url": download_url,
            "filename": filename
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
