# Orastria AI Book Generator API

Generates personalized astrology books using Claude AI.

## Setup on Railway

1. Create new project on Railway
2. Connect this GitHub repo
3. Add environment variables:
   - `B2_KEY_ID` - Backblaze key ID
   - `B2_APP_KEY` - Backblaze app key
   - `B2_BUCKET` - Bucket name (e.g., orastria-books)
   - `B2_ENDPOINT` - B2 endpoint URL

## API Endpoints

### POST /generate
Full generation with structured data.

### POST /generate-simple  
Simplified endpoint for n8n webhooks - accepts flat JSON.

### GET /health
Health check endpoint.

## Cost Estimate
- ~$0.05-0.15 per book (Claude API via Replicate)
- ~30-60 seconds generation time

## Content Generated
- Personalized introduction
- Sun, Moon, Rising analysis (AI-generated for their specific combo)
- Deep personality analysis (based on quiz answers)
- Love & relationships
- Compatibility with all 12 signs
- Career & purpose
- 2026 yearly forecast
- 12 monthly forecasts
- Numerology (calculated)
- Tarot reading
- Crystals & rituals
- Closing thoughts
