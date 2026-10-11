import psycopg
from pydantic import BaseModel
from openai import OpenAI
import os
from ddgs import DDGS
import json
import re
from dotenv import load_dotenv

# Define the Structured Output Schema for EDM Taxonomy
class EDMEnrichment(BaseModel):
    micro_subgenres: str
    bpm_and_rhythm: str
    mood_and_energy: str
    sonic_textures: str

# Boilerplate patterns for SoundCloud, Bandcamp, and general media sites
JUNK_PATTERNS = [
    r"\b\d+([\.,]\d+)?\s*(followers|following|tracks|plays|likes|subscribers)\b",
    r"tracks on (desktop|mobile|iOS|Android)",
    r"discover followers on",
    r"listen to (music|albums|songs|tracks) (online|for free)?",
    r"(download|stream) in (mp3|flac|wav|24-bit)",
    r"includes unlimited streaming via the free Bandcamp app",
    r"name your price",
    r"buy (digital|vinyl|cassette|album)",
    r"all rights reserved",
    r"stream tracks, albums, playlists",
]

load_dotenv()

LEMONADE_URL = os.getenv("LEMONADE_AI_URL", "http://localhost:13305/v1")
LEMONADE_API_KEY = os.getenv("LEMONADE_API_KEY", "sk-local-dummy-key")
# Configure the Local LLM Client
client = OpenAI(
    base_url=LEMONADE_URL,
    api_key=LEMONADE_API_KEY
)

def sanitize_snippet(text: str) -> str:
    """Strips platform marketing fluff and boilerplate from search snippets."""
    if not text:
        return ""
        
    sentences = re.split(r'(?<=[.!?]) +', text)
    clean_sentences = []

    for sentence in sentences:
        if not any(re.search(pattern, sentence, re.IGNORECASE) for pattern in JUNK_PATTERNS):
            clean_sentences.append(sentence.strip())

    return " ".join(clean_sentences)

def search_artist_info(artist_name: str) -> str:
    # Exclude platform fluff sites, target high-signal music terms
    query = f'"{artist_name}" EDM electronic music genre bio style -site:facebook.com -site:instagram.com -site:twitter.com -site:tiktok.com'
    print(f"  -> Searching web for: '{query}'...")
    
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No specific web results found."
        
        # Combine titles and sanitized snippets into a clean context string
        context_snippets = []
        for r in results:
            title = r.get('title', '')
            raw_body = r.get('body', '')
            clean_body = sanitize_snippet(raw_body)
            
            if clean_body:
                context_snippets.append(f"Title: {title}\nSnippet: {clean_body}")
        
        if not context_snippets:
            return "No specific web results found."
            
        return "\n\n".join(context_snippets)
    except Exception as e:
        print(f"  -> Search error: {e}")
        return "Search failed."

def enrich_database():
    # Connect to PostgreSQL
    conn = psycopg.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST") or "127.0.0.1",
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME")
    )
    cur = conn.cursor()

    # Target missing data, including string placeholders like "null"
    query = """
        SELECT id, name 
        FROM artists 
        WHERE genre = 'Unknown' 
           OR description LIKE 'Event/Performance%'
    """
    
    cur.execute(query)
    artists_to_process = cur.fetchall()

    if not artists_to_process:
        print("No artists need enrichment. Everything is up to date!")
        return

    print(f"Found {len(artists_to_process)} artists needing enrichment...")

    for artist_id, artist_name in artists_to_process:
        print(f"Processing: {artist_name}...")

        web_context = search_artist_info(artist_name)
        if web_context == "No specific web results found." or web_context == "Search failed.":
            continue
            
        schema_json = json.dumps(EDMEnrichment.model_json_schema(), indent=2)

        # Updated prompt strictly forbidding reasoning steps
        full_prompt = f"""
        "You are a fast EDM metadata extraction system. Do NOT analyze, explain, or output reasoning steps. Output ONLY the raw, minimal JSON matching the schema immediately."
        
        Analyze the electronic dance music (EDM) artist '{artist_name}'. 

        Web Search Context:
        ---
        {web_context}
        ---

        Based on the Web Search Context and your internal knowledge, analyze {artist_name}.
        Return a metadata profile for an EDM recommendation system, adhering to this schema:
        {schema_json}

        Provide:
        1. Micro-subgenres (e.g., Melodic Techno, Tech House, Dubstep, Liquid DnB).
        2. BPM Range and Rhythmic Feel (e.g., 128 BPM 4-on-the-floor, 140 BPM half-time).
        3. Mood & Energy (e.g., Dark, Hypnotic, Euphoric, Heavy, Chill).
        4. Key Sonic Elements (e.g., Acid 303 basslines, heavy sub-bass drops, vocal chop hooks).
        """
        
        try:
            # Call the local model using Structured Outputs and speed optimizations
            response = client.chat.completions.create(
                model="gemma-4-12b-it-GGUF-UD-Q5_K_XL", 
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                response_format={
                    "type": "json_object",
                },
                temperature=0.2,
                max_tokens=1024
            )

            raw_json = response.choices[0].message.content
            data = EDMEnrichment.model_validate_json(raw_json)
            
            # Format the output tightly for Nomic's embedding model down the line
            genre_field = data.micro_subgenres
            description_field = (
                f"BPM/Rhythm: {data.bpm_and_rhythm} | "
                f"Vibe: {data.mood_and_energy} | "
                f"Sound: {data.sonic_textures}"
            )
            
            # Update the record in PostgreSQL
            cur.execute(
                """
                UPDATE artists 
                SET genre = %s, description = %s 
                WHERE id = %s
                """,
                (genre_field, description_field, artist_id)
            )
            
            conn.commit()
            print(f"  -> Successfully updated metadata.")
            
        except Exception as e:
            print(f"  -> Error processing {artist_name}: {e}")
            conn.rollback()

    cur.close()
    conn.close()
    print("Enrichment complete!")

if __name__ == "__main__":
    enrich_database()