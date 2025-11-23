import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Deep Research Agent", page_icon="🧠", layout="centered")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("⚙️ Report Settings")

# 1. Audience Selector
audience = st.sidebar.selectbox(
    "Target Audience",
    ["Executive (High-level, strategic)", "Technical (Deep dive, specs)", "General Public (Simple, clear)"]
)

# 2. Focus Selector
focus = st.sidebar.radio(
    "Report Focus",
    ["Market & Business", "Technology & Innovation", "Competitor Analysis"]
)

st.sidebar.markdown("---")
st.sidebar.info("Built with Gemini 2.0 Flash & Google Search Grounding")

# --- LOGIC ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 API Key Not Found! Please set GEMINI_API_KEY in your .env file.")
    st.stop()

client = genai.Client(api_key=api_key)

def get_research(query, audience_type, focus_area):
    # Dynamic System Instruction based on user selection
    sys_instruct = f"""
    You are a premier AI Research Analyst.
    Your Target Audience is: {audience_type}.
    Your Primary Focus is: {focus_area}.
    
    Structure the report in Markdown:
    ## 1. Executive Summary
    ## 2. Deep Dive Analysis (Focus on {focus_area})
    ## 3. Strategic Implications
    ## 4. Sources & Credibility
    
    Be professional, data-driven, and concise.
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=query,
        config=types.GenerateContentConfig(
            system_instruction=sys_instruct,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            response_modalities=["TEXT"], 
        )
    )
    return response

# --- MAIN UI ---
st.title("🧠 Deep Research Agent")
st.markdown(f"Generate a **{focus}** report for a **{audience.split(' ')[0]}** audience.")

query = st.text_input("Enter Research Topic:", placeholder="e.g. The future of solid state batteries")

if st.button("🚀 Generate Briefing", type="primary"):
    if not query:
        st.warning("Please enter a topic.")
    else:
        with st.spinner("Analyzing the internet..."):
            try:
                result = get_research(query, audience, focus)
                
                # Render Report
                st.markdown("---")
                st.markdown(result.text)
                
                # Render Sources
                try:
                    metadata = result.candidates[0].grounding_metadata
                    if metadata and metadata.search_entry_point:
                        st.markdown("### 📚 Verified Sources")
                        st.components.v1.html(metadata.search_entry_point.rendered_content, height=200, scrolling=True)
                except:
                    pass

                # Download Button
                st.download_button(
                    label="💾 Download Report",
                    data=result.text,
                    file_name="research_report.md",
                    mime="text/markdown"
                )
                
            except Exception as e:
                st.error(f"An error occurred: {e}")