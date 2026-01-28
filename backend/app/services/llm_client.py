"""OpenAI LLM client wrapper."""

from typing import List, Dict, AsyncGenerator
from openai import AsyncOpenAI

from app.config import settings


class LLMClient:
    """Wrapper for OpenAI API calls."""
    
    def __init__(self):
        """
        Initialize the LLM client and load model configuration from settings.
        
        Creates an AsyncOpenAI client using the configured API key and stores the selected model name, temperature, and max token limit on the instance as `self.client`, `self.model`, `self.temperature`, and `self.max_tokens`.
        """
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
    
    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Request a chat completion from the configured model.
        
        Parameters:
            messages (List[Dict[str, str]]): Sequence of message objects, each with keys 'role' (e.g., 'user'|'assistant'|'system') and 'content' (the message text).
        
        Returns:
            str: The assistant's response text from the first choice.
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content
    
    async def chat_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Stream assistant token fragments for a chat conversation.
        
        Parameters:
            messages (List[Dict[str, str]]): Conversation messages; each dict must include 'role' and 'content'.
        
        Yields:
            str: Token fragment produced by the assistant as it is streamed.
        """
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def embed(self, text: str) -> List[float]:
        """
        Create an embedding vector for the given text.
        
        Parameters:
            text (str): Text to encode into an embedding.
        
        Returns:
            List[float]: A list of floats representing the embedding vector for the input text.
        """
        response = await self.client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text
        )
        
        return response.data[0].embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple input texts.
        
        Parameters:
            texts (List[str]): Texts to convert into embedding vectors.
        
        Returns:
            List[List[float]]: Embedding vector for each input text, in the same order as `texts`.
        """
        response = await self.client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texts
        )
        
        return [item.embedding for item in response.data]