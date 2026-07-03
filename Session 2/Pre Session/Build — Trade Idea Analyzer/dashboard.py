import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Set page config
st.set_page_config(page_title="Trade Idea Analyzer", layout="wide")

st.title("Trade Idea Analyzer 💡")
st.markdown("Get a structured second opinion on your trade thesis.")

# Sidebar for API Configuration
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Groq API Key", type="password", help="Enter your Groq API Key. Get one at console.groq.com")

# Fallback to environment variable if not provided in UI
if not api_key:
    api_key = os.getenv("GROQ_API_KEY", "")

st.markdown("### Your Trade Thesis")
thesis = st.text_area(
    "Describe your trade idea, rationale, and any key factors you are watching:", 
    height=150, 
    placeholder="e.g., I'm considering going long on XYZ because they recently announced a new product line, and their competitor is facing supply chain issues..."
)

system_prompt = """
You are an experienced, analytical trading colleague providing a second opinion on a written trade thesis.
Analyze the user's trade thesis and provide a structured response.

Your response MUST contain EXACTLY these three labeled sections, formatted as markdown headers:

### Supporting Points
List the valid points, logical reasoning, and strengths of the thesis.

### Risk Flags
Identify potential pitfalls, missing information, counter-arguments, and micro/macro risks the user might have overlooked.

### Confidence Note
Assess whether the thesis provides enough detail to be a solid plan. 

CRITICAL CONSTRAINTS:
1. NEVER tell the user to buy, sell, short, or take any specific financial action.
2. EXPLICITLY state if there isn't enough information in the thesis to properly judge it.
3. Keep the tone objective and professional.
"""

if st.button("Analyze Trade Idea", type="primary"):
    if not thesis.strip():
        st.warning("Please enter a trade thesis to analyze.")
    elif not api_key:
        st.error("Please enter your Groq API Key in the sidebar.")
    else:
        try:
            client = Groq(api_key=api_key)
            
            with st.spinner("Analyzing your thesis with Groq..."):
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": thesis,
                        }
                    ],
                    model="llama-3.1-8b-instant", # Using a highly capable model on Groq for reasoning
                    temperature=0.3, # Lower temperature for more analytical/objective response
                )
                
                response_content = chat_completion.choices[0].message.content
                
                st.markdown("---")
                st.markdown("## Analysis Result")
                st.write(response_content)
                
        except Exception as e:
            st.error(f"An error occurred while connecting to Groq: {str(e)}")
            st.info("Make sure your API key is correct and you have the `groq` python package installed (`pip install groq`).")
