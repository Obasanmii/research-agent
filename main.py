import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 1. Define the Persona
sys_instruct = """You are a High-Level Tech Analyst. 
When asked a topic, do not just answer the question. 
Write a mini-briefing (Markdown format) with these headers:
## 1. Executive Summary (The bottom line)
## 2. Key Details (Bulleted list of facts)
## 3. Market/Strategic Implications (Why this matters)

Keep it concise but insightful. ALWAYS use the search tool to get current data."""

def analyst_agent(user_query):
    print(f"🕵️‍♂️ Analyst is researching: {user_query}...")
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_query,
        config=types.GenerateContentConfig(
            # 2. Assign the Persona
            system_instruction=sys_instruct,
            tools=[types.Tool(
                google_search=types.GoogleSearch() 
            )],
            response_modalities=["TEXT"], 
        )
    )
    return response

if __name__ == "__main__":
    topic = input("Enter a research topic (e.g., 'Latest updates on Nvidia Blackwell chips'): ")
    
    try:
        result = analyst_agent(topic)
        
        # 3. Print the Markdown Report
        print("\n" + "="*40)
        print(result.text)
        print("="*40 + "\n")
        
        # We will suppress the raw HTML source dump for now to keep the terminal clean
        # We know it works.
            
    except Exception as e:
        print(f"\n❌ Error: {e}")