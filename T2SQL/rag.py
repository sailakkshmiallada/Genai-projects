import os
import pandas as pd
from typing import List, Optional
from ragatouille import RAGPretrainedModel

class RAGSearch:
    def __init__(self, model_name: Optional[str] = None, index_name: Optional[str] = None):
        """
        Initialize the RAGSearch class with either a pretrained model or an existing index.

        :param model_name: The name of the pretrained model to load.
        :param index_name: The name of the index to load.
        """
        if index_name and os.path.exists(f".ragatouille/colbert/indexes/{index_name}"):
            print("Loading model from index")
            self.model = RAGPretrainedModel.from_index(f".ragatouille/colbert/indexes/{index_name}")
        elif model_name:
            print("Loading pretrained model")
            self.model = RAGPretrainedModel.from_pretrained(model_name)
        else:
            raise ValueError("Either model_name or index_name must be provided.")

    def index_documents(self, docs: List[str], index_name: str, max_document_length: int = 256, 
                        split_documents: bool = False, use_faiss: bool = True) -> None:
        """
        Index the documents using the RAG model.

        :param docs: List of document strings to index.
        :param index_name: Name of the index.
        :param max_document_length: Maximum length of each document.
        :param split_documents: Whether to split documents.
        :param use_faiss: Whether to use FAISS for indexing.
        """
        self.model.index(
            collection=docs,
            index_name=index_name,
            max_document_length=max_document_length,
            split_documents=split_documents,
            use_faiss=use_faiss
        )

    def search_documents(self, query: str, k: int, index_name: str = "table_info", threshold: float = 0.0) -> List[str]:
        """
        Search the indexed documents using the RAG model.

        :param query: The search query.
        :param k: Number of top results to return.
        :param index_name: Name of the index to search.
        :param threshold: Minimum score threshold for filtering results.
        :return: List of document contents that match the query.
        """
        results = self.model.search(query=query, k=k, index_name=index_name)
        return [doc['content'] for doc in results if doc['score'] >= threshold]

    def ingest(self, df: pd.DataFrame, index_name: str = "table_info") -> None:
        """
        Ingests data from a DataFrame into a RAGSearch index.

        :param df: DataFrame containing the data to be ingested.
        :param index_name: Name of the index where documents will be stored.
        """
        docs = self._prepare_documents(df)
        self.index_documents(docs, index_name)

#     @staticmethod
#     def _prepare_documents(df: pd.DataFrame) -> List[str]:
#         """
#         Prepare documents from a DataFrame.

#         :param df: DataFrame containing the data.
#         :return: List of document strings.
#         """
#         docs = []
#         for _, row in df.iterrows():
#             table_info = (
#                 f"Table: {row['table_name']}\n"
#                 f"Column: {row['table_column']}\n"
#                 f"Data Type: {row['column_data_type']}\n"
#                 f"Definition: {row['column_definition']}\n"
#                 f"Comments: {row['comments']}\n"
#                 f"Keywords: {row['keywords']}"
#             )
#             docs.append(table_info)
#         return docs
    @staticmethod
    def _prepare_documents(df: pd.DataFrame) -> List[str]:
        """
        Prepare documents from a DataFrame.

        :param df: DataFrame containing the data.
        :return: List of document strings.
        """
        docs = []
        for _, row in df.iterrows():
            table_info = (
                f"Keywords: {row['Keywords']}\n"
                f"Table Name: {row['Table_Name']}\n"
                f"Column: {row['Field_Name']}\n"
                f"Data Type: {row['Data_Type']}\n"
                f"Definition: {row['Field_Defination']}\n"
                f"Field Description: {row['Description']}"
                
            )
            docs.append(table_info)
        return docs

def load_or_ingest(index_name: str, data_frame: Optional[pd.DataFrame] = None) -> RAGSearch:
    """
    Load an existing RAG model from an index or ingest data to create a new index.

    :param index_name: Name of the index.
    :param data_frame: DataFrame for ingestion.
    :return: RAGSearch instance.
    """
    path_to_index = f".ragatouille/colbert/indexes/{index_name}"

    if os.path.exists(path_to_index):
        print("Index is available")
        if data_frame is not None:
            print("DataFrame provided. Re-ingesting data.")
            rag_search = RAGSearch(model_name="colbert-ir/colbertv2.0")
            rag_search.ingest(data_frame, index_name=index_name)
        # Always return the RAGSearch instance initialized with the index_name
        return RAGSearch(index_name=index_name)
    else:
        if data_frame is None:
            raise ValueError("DataFrame must be provided for ingestion if the index does not exist.")

        print("Index does not exist. Creating new index.")
        rag_search = RAGSearch(model_name="colbert-ir/colbertv2.0")
        rag_search.ingest(data_frame, index_name=index_name)
        # Always return the RAGSearch instance initialized with the index_name
        return RAGSearch(index_name=index_name)