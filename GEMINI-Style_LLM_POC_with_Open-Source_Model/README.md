# RAG implementation

## Overview
This project implements a Retrieval-Augmented Generation (RAG) system that combines a knowledge base with real-time web search to provide accurate and up-to-date answers to user questions. The system uses a vector database to store and retrieve relevant information, and enhances responses with web search results.

## Features
- **Hybrid Knowledge Retrieval**: Combines local knowledge base with real-time web search
- **PDF Document Integration**: Ability to extract and index content from PDF documents
- **Vector-based Similarity Search**: Uses embeddings to find the most relevant information
- **Automatic Knowledge Updates**: Can automatically update the knowledge base with latest news
- **Contextual Question Answering**: Provides answers based on multiple sources of information

## Components
- **Language Model**: Google's FLAN-T5-Large for text generation
- **Embeddings**: Sentence Transformers (all-mpnet-base-v2) for semantic search
- **Vector Store**: Chroma DB for efficient similarity search
- **Web Search**: DuckDuckGo search integration for real-time information
- **PDF Processing**: PyPDF2 for extracting text from PDF documents

## Dependencies
- transformers
- langchain and langchain-community
- sentence-transformers
- chromadb
- PyPDF2
- duckduckgo-search

## Key Functions
- `add_to_knowledge_base()`: Adds text to the vector database
- `update_knowledge_base_with_news()`: Retrieves and adds latest news
- `add_pdf_to_knowledge_base()`: Extracts and adds content from PDF files
- `get_recent_relevant_info()`: Retrieves relevant information from the knowledge base
- `answer_question()`: Combines knowledge base and web search to answer questions

## Usage
The system can answer a variety of questions by:
1. Retrieving relevant information from its knowledge base
2. Searching the web for up-to-date information
3. Combining both sources to generate a comprehensive answer

## Example Questions
- Factual questions (e.g., "What is the capital of France?")
- Current events (e.g., "Who is the captain of Indian Cricket team as of 2024?")
- General knowledge (e.g., "What can you tell me about Virat Kohli?")
- Latest developments (e.g., "What are the latest developments in renewable energy?")
- Specialized queries (e.g., chess puzzles)

## Limitations
- The in-memory database does not persist between runs
- Limited by the quality of the underlying language model
- Web search results may vary in quality and relevance

