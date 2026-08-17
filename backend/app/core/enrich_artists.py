import psycopg
from pydantic import BaseModel
from openai import OpenAI
import os
from ddgs import DDGS
import json
from dotenv import load_dotenv

# Define the Structured Output Schema for EDM Taxonomy
class EDMEnrichment(BaseModel):
    micro_subgenres: str
    bpm_and_rhythm: str
    mood_and_energy: str
    sonic_textures: str

load_dotenv()

LEMONADE_URL = os.getenv("LEMONADE_AI_URL", "http://localhost:13305/v1")
LEMONADE_API_KEY = os.getenv("LEMONADE_API_KEY", "sk-local-dummy-key")
# 2. Configure the Local LLM Client
client = OpenAI(
    base_url=LEMONADE_URL,
    api_key=LEMONADE_API_KEY
)

def search_artist_info(artist_name: str) -> str:
    # Fetches web snippets for an artist using DuckDuckGo.
    query = f"{artist_name} electronic music genre bio sound soundcloud bandcamp"
    print(f"  -> Searching web for: '{query}'...")
    
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No specific web results found."
        print(f"DDG Results: {results}")
        
        # Combine titles and snippets into a clean context string
        context_snippets = []
        for r in results:
            context_snippets.append(f"Title: {r.get('title')}\nSnippet: {r.get('body')}")
        
        return "\n\n".join(context_snippets)
    except Exception as e:
        # May add MusicBrainz integration here later.
        print(f"  -> Search error: {e}")
        return "Search failed."

def enrich_database():
    # 3. Connect to PostgreSQL
    # connString built in pieces as special characters can break psychopg's parsing
    conn = psycopg.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST") or "127.0.0.1",
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME")
    )
    cur = conn.cursor()

    # 4. Target missing data, including string placeholders like "null"
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

        full_prompt = f"""
        "You are an expert electronic music taxonomist. Return ONLY valid JSON matching the schema."
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
            # 5. Call the local model using Structured Outputs.  Tuned format for Gemma.
            response = client.chat.completions.create(
                model="Gemma-4-12B-it-MTP-GGUF", 
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                response_format={
                    "type": "json_object",
                    # "schema": EDMEnrichment.model_json_schema()
                },
                temperature=0.2
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
            
            # 6. Update the record in PostgreSQL
            cur.execute(
                """
                UPDATE artists 
                SET genre = %s, description = %s 
                WHERE id = %s
                """,
                (genre_field, description_field, artist_id)
            )
            
            # Commit after each successful update so progress isn't lost if the script fails
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