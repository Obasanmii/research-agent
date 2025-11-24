import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from fpdf import FPDF 

#PAGE CONFIGURATION
st.set_page_config(page_title="Deep Research Agent", page_icon="🧠", layout="centered")

#SIDEBAR 
st.sidebar.header("⚙️ Report Settings")
audience = st.sidebar.selectbox("Target Audience", ["Executive", "Technical", "General Public"])
focus = st.sidebar.radio("Report Focus", ["Market & Business", "Technology", "Competitor Analysis"])

#PDF GENERATION FUNCTION (The Engineer's Fix)
def create_pdf(text):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'Deep Research Briefing', 0, 1, 'C')

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # 1. Clean the text (FPDF doesn't like Markdown symbols like ** or ##)
    clean_text = text.replace('*', '').replace('#', '')
    
    # 2. Stripping emojis off
    clean_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 10, txt=clean_text)
    return bytes(pdf.output(dest='S'))

#LOGIC
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        st.error("🔑 API Key Not Found! Check .env or Streamlit Secrets.")
        st.stop()

client = genai.Client(api_key=api_key)

def get_research(query, audience_type, focus_area):
    sys_instruct = f"""
    You are a premier AI Research Analyst.
    Your Target Audience is: {audience_type}.
    Your Primary Focus is: {focus_area}.
    Structure the report in Markdown.
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

#MAIN UI
st.title("🧠 Deep Research Agent")
query = st.text_input("Enter Research Topic:", placeholder="e.g. Nvidia's Strategy")

if st.button("🚀 Generate Briefing", type="primary"):
    if not query:
        st.warning("Please enter a topic.")
    else:
        with st.spinner("Analyzing..."):
            try:
                result = get_research(query, audience, focus)
                st.markdown("---")
                st.markdown(result.text)
                
                #DOWNLOAD SECTION
                col1, col2 = st.columns(2)
                
                with col1:
                    # Original Markdown Download
                    st.download_button(
                        label="💾 Download Markdown",
                        data=result.text,
                        file_name="report.md",
                        mime="text/markdown"
                    )
                
                with col2:
                    # New PDF Download
                    pdf_data = create_pdf(result.text)
                    st.download_button(
                        label="📄 Download PDF",
                        data=pdf_data,
                        file_name="report.pdf",
                        mime="application/pdf"
                    )
                
            except Exception as e:
                st.error(f"An error occurred: {e}")