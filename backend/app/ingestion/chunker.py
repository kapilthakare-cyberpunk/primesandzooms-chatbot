"""Text chunking for RAG ingestion."""

from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.config import get_settings


class TextChunker:
    """Splits documents into smaller chunks for embedding."""
    
    def __init__(
        self, 
        chunk_size: int | None = None, 
        chunk_overlap: int | None = None
    ):
        """Initialize chunker with size parameters.
        
        Args:
            chunk_size: Maximum characters per chunk (default from settings)
            chunk_overlap: Overlap between chunks for context continuity
        """
        settings = get_settings()
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks while preserving metadata.
        
        Args:
            documents: List of Document objects to chunk
            
        Returns:
            List of chunked Document objects
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
        """Chunk a raw text string.
        
        Args:
            text: Raw text to chunk
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of chunked Document objects
        """
        doc = Document(page_content=text, metadata=metadata or {})
        return self.chunk_documents([doc])
