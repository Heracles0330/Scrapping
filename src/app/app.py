import streamlit as st
import os
import time
import json
import sys
from pathlib import Path

# Get the absolute path to the project root
project_root = Path(__file__).parent.absolute()
sys.path.append(os.path.join(project_root, "../.."))

from src.rag.llm import LLM

# Page configuration
st.set_page_config(
    page_title="Cheese Assistant",
    page_icon="🧀",
    layout="wide"
)

# Load CSS
def load_css(css_file):
    with open(css_file, "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Load the CSS
css_path = os.path.join(os.path.dirname(__file__), "style.css")
load_css(css_path)

# Initialize LLM if not already in session state
if 'llm' not in st.session_state:
    st.session_state.llm = LLM()

# Initialize chat history if not already in session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Initialize context data
if 'last_context' not in st.session_state:
    st.session_state.last_context = []

# Initialize processing state
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Function to handle message submission
def submit_message():
    if st.session_state.user_input:
        user_message = st.session_state.user_input
        
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_message})
        
        # Set processing flag to true to indicate we need to generate a response
        st.session_state.processing = True
        
        # Reset input
        st.session_state.user_input = ""

# Sidebar content
with st.sidebar:
    st.image("src/app/logo.png", width=250)
    st.title("Cheese Expert")
    
    st.markdown("""
    **Welcome to the Cheese Expert Assistant!**
    
    Ask me anything about cheese - from flavor profiles and textures to culinary uses and shopping recommendations.
    
    I'm powered by a specialized RAG system with detailed cheese knowledge.
    """)
    
    st.markdown("---")
    
    # Clear button in sidebar
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.experimental_rerun()
    
    # Download button in sidebar - replaced Save Chat
    if st.session_state.messages:
        # Prepare chat content
        chat_content = ""
        for message in st.session_state.messages:
            chat_content += f"{message['role'].upper()}: {message['content']}\n\n"
        
        # Create download button
        st.download_button(
            label="Download Chat",
            data=chat_content,
            file_name=f"cheese_chat_{st.session_state.llm.session_id}.txt",
            mime="text/plain"
        )
    
    # Toggle to show context
    st.markdown("---")
    show_context = st.checkbox("Show RAG Context")

# Main chat area
st.markdown("<div class='chat-header'><h1>🧀 Cheese Expert Assistant</h1></div>", unsafe_allow_html=True)

# Create a container for the chat interface with fixed height
chat_container = st.container()
with chat_container:
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    
    # Display chat messages from history
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='assistant-message'>{message['content']}</div>", unsafe_allow_html=True)
    
    # Check if we need to process a new message
    if st.session_state.processing:
        # Get the last user message
        last_user_message = st.session_state.messages[-1]["content"]
        
        # Create an empty placeholder for streaming
        message_placeholder = st.empty()
        
        # Initialize a variable to collect the full response
        full_response = ""
        
        # Get response and context
        with st.spinner("Thinking..."):
            # Modify LLM to capture context or simulate it here
            response, context = st.session_state.llm.answer_question_with_context(last_user_message)
            
            # Store context for display
            st.session_state.last_context = context
            
            # Simulate streaming
            chunks = [response[i:i+10] for i in range(0, len(response), 10)]
            
            for chunk in chunks:
                full_response += chunk
                message_placeholder.markdown(f"<div class='assistant-message'>{full_response}</div>", unsafe_allow_html=True)
                time.sleep(0.03)  # Slightly faster streaming
        
        # Add assistant response to history after streaming is complete
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Reset processing flag
        st.session_state.processing = False
        
        # Rerun to update UI without the spinner
        st.experimental_rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# Display RAG context if toggle is on
if show_context and st.session_state.last_context:
    st.markdown("### RAG Context Data")
    st.markdown("The following cheese information was retrieved and sent to the AI:")
    
    for i, doc in enumerate(st.session_state.last_context, 1):
        with st.expander(f"Cheese {i}: {doc.get('metadata', {}).get('title', 'Unknown')}"):
            st.json(doc)

# User input section - moved below the chat container
st.markdown("<div class='user-input-container'>", unsafe_allow_html=True)
st.text_input("Ask me about cheese:", key="user_input", on_change=submit_message)
st.markdown("</div>", unsafe_allow_html=True)

# Add CSS to adjust the chat container height
st.markdown("""
<style>
.chat-container {
    max-height: calc(60vh - 100px) !important;
    overflow-y: auto;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
}
.user-input-container {
    margin-top: 1rem;
    position: relative;
    bottom: 0;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)