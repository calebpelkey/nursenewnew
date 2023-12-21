import streamlit as st
import os
from PyPDF2 import PdfReader
import docx
import functionscode
import io
import requests
import json
import openai

# Function to handle user queries. It combines user queries with the document text and sends them to the OpenAI API.
def handle_query(query, document_texts, api_key, model):
    # Join all document texts for the query context
    combined_text = "\n\n".join(document_texts)
    prompt = f"Based on the nursing resume knowledge base:\n\n{combined_text}\n\nUser: {query}\nAI:"
    response = get_openai_chat_response(api_key, model, prompt, max_tokens=1000)
    return response

# Function to extract text from a PDF file.
def extract_text_from_pdf(file_stream):
    reader = PdfReader(file_stream)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# Function to extract text from a DOCX file.
def extract_text_from_docx(file_stream):
    doc = docx.Document(file_stream)
    text = [paragraph.text for paragraph in doc.paragraphs]
    return '\n'.join(text)

# Function to get a response from the OpenAI chat model.
def get_openai_chat_response(api_key, model, prompt, max_tokens):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    data = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': max_tokens
    }
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    return response.json()

# The main function of the script, setting up the Streamlit interface and handling the application logic.
def main():
    st.title("Nursing Resume Assistant")

    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'user_input' not in st.session_state:
        st.session_state['user_input'] = ""

    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key is None:
        st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        return
    model = 'gpt-4-1106-preview'

    # Handle multiple document uploads
    uploaded_files = st.file_uploader("Upload your documents", type=["pdf", "docx", "txt"], accept_multiple_files=True)

    # Initialize or update the session state for storing document texts
    if 'document_texts' not in st.session_state:
        st.session_state['document_texts'] = []

    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.type == "application/pdf":
                text = extract_text_from_pdf(io.BytesIO(uploaded_file.read()))
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text = extract_text_from_docx(io.BytesIO(uploaded_file.read()))
            else:
                text = uploaded_file.getvalue().decode("utf-8")
            st.session_state['document_texts'].append(text)

    user_input = st.text_input("Enter your query related to the uploaded document:", value=st.session_state.user_input)

    if st.button("Get AI Response"):
        st.session_state['history'].append(('user', user_input))
        response = handle_query(user_input, st.session_state['document_texts'], openai_api_key, model)

        if 'choices' in response and response['choices']:
            ai_response = response['choices'][0]['message']['content']
            st.session_state['history'].append(('ai', ai_response))
        else:
            st.error("No response received from the AI.")

        st.session_state.user_input = ""
        st.experimental_rerun()

    for i, (role, text) in enumerate(st.session_state['history']):
        if role == 'user':
            st.markdown(f"**User:**\n{text}", unsafe_allow_html=True)
        else:
            st.markdown(f"**AI:**\n{text}", unsafe_allow_html=True)
        if i < len(st.session_state['history']) - 1:
            st.text("")  # Add space after each entry except the last

if __name__ == "__main__":
    main()
