# Conversation Chatbot

This is a conversation chatbot that provides assistance with coding tasks. It can be configured to use either the Groq API or the OpenAI API for generating responses.

## Installation

To install and run the chatbot, follow these steps:

1. Create a virtual environment using either `python` or `conda`.

   - Using `python`:

     ```
     python -m venv env
     source env/bin/activate
     ```

   - Using `conda`:

     ```
     conda create -n env python=3.12
     conda activate env
     ```

2. Install the required packages using `pip`:

   ```
   pip install -r requirements.txt
   ```

3. Add your API keys for either Groq or OpenAI to the .env file.

4. Run the chatbot using `streamlit`:

   ```
   streamlit run app.py
   ```

## Usage

The chatbot can be used to assist with coding tasks such as debugging, code review, and generating code snippets. To use the chatbot, simply enter your question or request in the input field and press enter. The chatbot will generate a response based on the input and the configured API.

## Configuration

The chatbot can be configured to use either the Groq API or the OpenAI API for generating responses. To configure the chatbot, add your API keys to the  .env file.
