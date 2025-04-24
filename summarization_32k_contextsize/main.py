from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import CTransformers
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from transformers import BartTokenizer, BartForConditionalGeneration
import PyPDF2
import torch
import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM

DATA_PATH = 'data/'
DB_FAISS_PATH = 'vector_db/db_faiss'

prompt_template = """Write a concise summary of the following:
"{text}"
CONCISE SUMMARY:"""
prompt = PromptTemplate.from_template(prompt_template)

#Vector DB creation and embeddings storage
def create_vector_db(embeddings):
    loader = DirectoryLoader(DATA_PATH,
                             glob='*.pdf',
                             loader_cls=PyPDFLoader)

    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500,
                                                   chunk_overlap=50)
    texts = text_splitter.split_documents(documents)

    db = FAISS.from_documents(texts, embeddings)
    db.save_local(DB_FAISS_PATH)

#Load LLM
def load_llm():
    # Load the locally downloaded model here
    # llm = CTransformers(
    #     model = "TheBloke/Llama-2-7B-Chat-GGML",
    #     model_type="llama",
    #     temperature = 0.5
    # )
    llm = AutoModelForCausalLM.from_pretrained("togethercomputer/LLaMA-2-7B-32K", trust_remote_code=True,
                                                 torch_dtype=torch.float16)

    return llm

# For Summarizing pdf using b
def summarize_pdf(pdf_file):
    # Read the PDF file
    st.info('Extracting text from PDF', icon="ℹ️")
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

    # Summarize the text
    st.info('Encoding text', icon="ℹ️")
    inputs = tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=1024, truncation=True)

    st.info('Generating Summary', icon="ℹ️")
    summary_ids = model.generate(inputs, max_length=150, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def main():
    # App layout
    st.title("PDF Summarization App")

    # File uploader
    uploaded_file = st.file_uploader("Upload a PDF or text file", type=["pdf"])

    model_choice = st.selectbox("Choose summarization model:", ["T5", "LLM"])
    if st.button('Generate'):
        # Process input
        if uploaded_file and uploaded_file.type == "application/pdf":
            with st.spinner('Processing...'):
                # If selected LLM for summary generation
                filepath = "data/" + uploaded_file.name
                with open(filepath, "wb") as temp_file:
                    temp_file.write(uploaded_file.read())

                if model_choice == "LLM":
                    st.info('Creating Vectors', icon="ℹ️")
                    create_vector_db(embeddings)

                    st.info('Loading LLM', icon="ℹ️")
                    llm = load_llm()
                    llm_chain = LLMChain(llm=llm, prompt=prompt)
                    stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")

                    st.info('Loading DB', icon="ℹ️")
                    db = FAISS.load_local(DB_FAISS_PATH, embeddings)

                    st.info('Generating Summary', icon="ℹ️")
                    summary = stuff_chain.run(db)
                    st.write(summary)

                else:
                    summary = summarize_pdf(filepath)
                    st.write(summary)
            st.success("Summary Generated")
        else:
            st.warning("Please upload PDF")


if __name__ == "__main__":
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                       model_kwargs={'device': 'cpu'})
    model_name = "facebook/bart-large-cnn"
    tokenizer = BartTokenizer.from_pretrained(model_name)
    model = BartForConditionalGeneration.from_pretrained(model_name)
    main()