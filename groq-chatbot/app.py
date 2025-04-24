# Python Standard Libraries
import os
import random

# External Libraries
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# Internal Modules
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder
)

# Load environment variables
load_dotenv()

# Get API keys from environment variables
GROQ_API_KEY = os.environ['GROQ_API_KEY']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

# Constants
USER_AVATAR = "./icon.jpeg"
ASSISTANT_AVATAR = "https://ask.vanna.ai/static/img/vanna_circle.png"

# Initialize session state for chat messages
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'buffer_memory' not in st.session_state:
    st.session_state.buffer_memory = None

def clear_chat_history():
    """
    Clears the chat history by resetting the session state for chat messages.
    """
    st.session_state["messages"] = []
    st.session_state.buffer_memory = None

def main():
    st.set_page_config(layout="wide")
    st.title("RGPT")
    st.subheader("AI-powered copilot for queries")
    
    st.sidebar.button('Clear Chat', on_click=clear_chat_history)

    # Add customization options to the sidebar
    st.sidebar.title('Model')
    model = st.sidebar.selectbox(
        "Choose a model",
        ['llama3-70b-8192','gpt-4o','gpt-4-32k','mixtral-8x7b-32768','llama3-8b-8192']
    )
    with st.sidebar.expander("Advanced"):
        conversational_memory_length = st.slider('Conversational memory length:', 1, 10, value = 5)
        temperature_length = st.slider('Temperature:', 0.0, 1.0, value = 0.0,step=0.1)
        Max_Tokens_length = st.slider('Max Tokens:', 0, 32768, value = 1024,step=1024)
        Stream = st.toggle("Stream",value=True)

    user_question = st.chat_input('Enter your question here...' , key="message")

    # session state variable
    if st.session_state.buffer_memory is None:
        st.session_state.buffer_memory=ConversationBufferWindowMemory(k=conversational_memory_length,return_messages=True)
    system_prompt = """
                    You are interacting with a helpful AI assistant who can adapt to different roles. When you ask questions related to programming, Python, data science, or AI, the assistant will respond as an expert in these fields, providing in-depth explanations, code snippets, and insightful advice. The assistant will ensure that all code responses adhere to strict coding standards, including:
                        1. Provide an in-depth explanation, including relevant code snippets and insightful advice.
                        2. Ensure that all code responses adhere to the following strict coding standards:
                            a. Functional and efficient code
                            b. Well-commented code with proper docstrings
                            c. No hardcoded values
                            d. Modularized code with clear separation of concerns
                            e. Code organized using classes and objects, following object-oriented programming principles
                            f. Optimized code that minimizes time and space complexity
                            g. Production-ready code that is scalable, reliable, and maintainable
                        3. Provide code that is:
                            a. Modular, reusable, and easy to maintain
                            b. Focused on readability and scalability
                            c. Optimized for performance, with minimal time and space complexity
                            d. Ready for production use, with consideration for scalability, reliability, and maintainability
                        For all other topics, the assistant will respond as a helpful assistant or conversational genius

                    """
    system_msg_template = SystemMessagePromptTemplate.from_template(template=system_prompt)
    human_msg_template = HumanMessagePromptTemplate.from_template(template="{input}")
    prompt_template = ChatPromptTemplate.from_messages([system_msg_template, MessagesPlaceholder(variable_name="history"), human_msg_template])

    for messages in st.session_state.messages:
        avatar_url = ASSISTANT_AVATAR if messages["role"] == "assistant" or messages["role"] == "str" else USER_AVATAR 
        with st.chat_message(messages["role"], avatar=avatar_url):
            st.write(messages["content"])   # Keep user  messages in markdown container

    if model in ['gpt-4o','gpt-4-32k']:
        llm = ChatOpenAI(model_name=model, 
                         openai_api_key=OPENAI_API_KEY, 
                         temperature=temperature_length, 
                         max_tokens=Max_Tokens_length,
                         top_p=1)
    else :
        llm = ChatGroq(
                groq_api_key=GROQ_API_KEY, 
                model_name=model,
                temperature=temperature_length,
                max_tokens=Max_Tokens_length,
                top_p=1,
                stop=None,
                streaming=Stream)
    
    conversation = ConversationChain(
            llm=llm,
            memory=st.session_state.buffer_memory,
            prompt=prompt_template,
            verbose=True
    )
    
    if user_question:
        st.chat_message("user",avatar=USER_AVATAR).write(user_question)
        st.session_state.messages.append({"role": "user", "content": user_question})
        response = conversation(user_question)
        st.chat_message("assistant",avatar=ASSISTANT_AVATAR).write(response['response'])
        st.session_state.messages.append({"role": "assistant", "content": response['response']}) 

if __name__ == "__main__":
    main()

# import os
# import streamlit as st
# from dotenv import load_dotenv
# from langchain.chains import ConversationChain
# from langchain.chains.conversation.memory import ConversationBufferWindowMemory
# from langchain.chat_models import ChatOpenAI,AzureChatOpenAI
# from langchain_groq import ChatGroq
# from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate, MessagesPlaceholder

# # Load environment variables
# load_dotenv()

# # Configuration
# class Config:
#     USER_AVATAR = "./icon.jpeg"
#     ASSISTANT_AVATAR = "https://ask.vanna.ai/static/img/vanna_circle.png"
#     GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
#     OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
#     AZURE_OPENAI_KEY = os.environ.get('AZURE_OPENAI_API_KEY')
#     AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT')


# # Initialize session state
# def init_session_state():
#     if 'messages' not in st.session_state:
#         st.session_state.messages = []
#     if 'buffer_memory' not in st.session_state:
#         st.session_state.buffer_memory = ConversationBufferWindowMemory(k=5, return_messages=True)

# # Clear chat history
# def clear_chat_history():
#     st.session_state.messages = []
#     st.session_state.buffer_memory = None

# # UI Components
# def render_sidebar():
#     st.sidebar.button('Clear Chat', on_click=clear_chat_history)
#     model = st.sidebar.selectbox("Choose a model", ['llama3-70b-8192', 'gpt-4o', 'gpt-4-32k', 'mixtral-8x7b-32768', 'llama3-8b-8192'])
#     with st.sidebar.expander("Advanced"):
#         conversational_memory_length = st.slider('Conversational memory length:', 1, 10, value=5)
#         temperature_length = st.slider('Temperature:', 0.0, 1.0, value=0.0, step=0.1)
#         max_tokens_length = st.slider('Max Tokens:', 0, 32768, value=1024, step=1024)
#         stream = st.toggle("Stream", value=True)
#     return model, conversational_memory_length, temperature_length, max_tokens_length, stream

# def render_chat_messages():
#     for message in st.session_state.messages:
#         avatar_url = Config.ASSISTANT_AVATAR if message["role"] == "assistant" else Config.USER_AVATAR
#         with st.chat_message(message["role"], avatar=avatar_url):
#             st.write(message["content"])

# # Model Factory
# def get_model(model_name, temperature, max_tokens, stream):
#     if model_name in ['gpt-4o']:
#         return ChatOpenAI(model_name=model_name, openai_api_key=Config.OPENAI_API_KEY, temperature=temperature, max_tokens=max_tokens, top_p=1)
#     elif model_name == 'gpt-4-32k':
#         return AzureChatOpenAI(api_key=Config.AZURE_OPENAI_KEY, model_name=model_name, temperature=temperature, max_tokens=max_tokens, top_p=1, stop=None, streaming=stream)
#     else:
#         return ChatGroq(groq_api_key=Config.GROQ_API_KEY, model_name=model_name, temperature=temperature, max_tokens=max_tokens, top_p=1, stop=None, streaming=stream)

# # Main Function
# def main():
#     st.set_page_config(layout="wide")
#     st.title("RGPT")
#     st.subheader("AI-powered copilot for queries")

#     init_session_state()
#     model, conversational_memory_length, temperature_length, max_tokens_length, stream = render_sidebar()
#     user_question = st.chat_input('Enter your question here...', key="message")
#     render_chat_messages()

#     if user_question:
#         st.session_state.messages.append({"role": "user", "content": user_question})
#         model_instance = get_model(model, temperature_length, max_tokens_length, stream)
#         conversation = ConversationChain(llm=model_instance, memory=st.session_state.buffer_memory, prompt=ChatPromptTemplate.default(), verbose=True)
#         response = conversation(user_question)
#         st.session_state.messages.append({"role": "assistant", "content": response['response']})

# if __name__ == "__main__":
#     main()