import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from fpdf import FPDF

# --- CONFIG ---
st.set_page_config(page_title="Deep Research Agent", page_icon="🧠", layout="centered")

# --- STATE MANAGEMENT (MEMORY) ---
# This checks: "Do we have messages saved? If not, create an empty list."
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- PDF FUNCTION ---
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
    clean_text = text.replace('*', '').replace('#', '')
    clean_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    return bytes(pdf.output(dest='S')) 

# --- API SETUP ---
load_dotenv()
try:
    if "GEMINI_API_KEY" in os.environ:
        api_key = os.getenv("GEMINI_API_KEY")
    else:
        api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("🔑 API Key Not Found!")
    st.stop()

client = genai.Client(api_key=api_key)

# --- UI HEADER ---
st.title("🧠 Deep Research Chat")
st.caption("Ask follow-up questions. I now remember context.")

# --- 1. DISPLAY HISTORY ---
# We loop through the saved messages and print them on screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 2. HANDLE INPUT ---
if prompt := st.chat_input("What would you like to research?"):
    
    # A. Display User Message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    # Save it to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # B. Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # We construct a "Context String" from previous messages
                # This is the "Memory" trick: We feed the history back into the prompt.
                history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-4:]])
                
                full_prompt = f"""
                HISTORY OF CONVERSATION:
                {history_text}
                
                NEW USER QUERY:
                {prompt}
                
                SYSTEM INSTRUCTION:
                You are a Research Analyst. Use the history to understand context.
                If the user asks a follow-up (e.g., "Why?"), refer to the previous info.
                Always use Google Search for the NEW query.
                """
                
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        response_modalities=["TEXT"], 
                    )
                )
                
                # Display AI Response
                st.markdown(response.text)
                
                # Show Sources if available
                if response.candidates[0].grounding_metadata.search_entry_point:
                     st.components.v1.html(response.candidates[0].grounding_metadata.search_entry_point.rendered_content, height=200, scrolling=True)
                
                # Save AI Response to history
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                # PDF Download (Optional: Only for the latest answer)
                pdf_data = create_pdf(response.text)
                st.download_button("📄 Download PDF", data=pdf_data, file_name="briefing.pdf", mime="application/pdf")
                
            except Exception as e:
                st.error(f"Error: {e}")