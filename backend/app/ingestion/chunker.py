"""Text chunking for RAG ingestion."""

from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.config import settings


class TextChunker:
    """Splits documents into smaller chunks for embedding."""
    
    def __init__(
        self, 
        chunk_size: int | None = None, 
        chunk_overlap: int | None = None
    ):
        """
        Create a TextChunker configured with chunk size and overlap, using defaults from settings when arguments are None.
        
        Parameters:
            chunk_size (int | None): Maximum number of characters per chunk; if None, uses settings.CHUNK_SIZE.
            chunk_overlap (int | None): Number of characters to overlap between consecutive chunks; if None, uses settings.CHUNK_OVERLAP.
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split each Document into smaller Document chunks and annotate each chunk's metadata with its position.
        
        Preserves the original Document.metadata for every chunk and adds two keys: "chunk_index" (zero-based index of the chunk within the source document) and "total_chunks" (total number of chunks produced from the source document).
        
        Parameters:
            documents (List[Document]): Documents to split into chunks.
        
        Returns:
            List[Document]: Chunk Documents where each Document.page_content is a chunk of the original text and Document.metadata contains the original metadata plus "chunk_index" and "total_chunks".
        """
        chunks = []
        
        for doc in documents:
            # Split the document
            doc_chunks = self.splitter.split_text(doc.page_content)
            
            # Create new documents for each chunk with inherited metadata
            for i, chunk_text in enumerate(doc_chunks):
                chunk_metadata = doc.metadata.copy()
                chunk_metadata["chunk_index"] = i
                chunk_metadata["total_chunks"] = len(doc_chunks)
                
                chunks.append(Document(
                    page_content=chunk_text,
                    metadata=chunk_metadata
                ))
        
        return chunks
    
    def chunk_text(self, text: str, metadata: dict | None = None) -> List[Document]:
        """
        Split a raw text string into Document chunks, attaching optional metadata to each chunk.
        
        Parameters:
            text (str): Text to split into chunks.
            metadata (dict | None): Optional metadata to include on every returned Document; defaults to an empty dict.
        
        Returns:
            List[Document]: Documents representing the resulting chunks. Each Document preserves the provided metadata and includes `chunk_index` and `total_chunks` metadata keys.
        """
        doc = Document(page_content=text, metadata=metadata or {})
        return self.chunk_documents([doc])