"""
Telegram Bot Service for Primes and Zooms
Handles message processing and RAG integration
"""

import logging
import httpx
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependencies
_rag_engine = None

def get_rag_engine():
    global _rag_engine
    if _rag_engine is None:
        from app.services.rag_engine import RAGEngine
        _rag_engine = RAGEngine(get_settings())
    return _rag_engine


class TelegramBot:
    """Telegram Bot service with RAG integration."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = f"https://api.telegram.org/bot{self.settings.TELEGRAM_BOT_TOKEN}"
        
    async def _make_request(self, method: str, data: dict = None) -> dict:
        """Make a request to Telegram Bot API."""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/{method}"
            if data:
                response = await client.post(url, json=data)
            else:
                response = await client.get(url)
            return response.json()
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = "Markdown",
        reply_to_message_id: Optional[int] = None
    ) -> bool:
        """Send a message to a chat."""
        try:
            data = {
                "chat_id": chat_id,
                "text": text,
            }
            if parse_mode:
                data["parse_mode"] = parse_mode
            if reply_to_message_id:
                data["reply_to_message_id"] = reply_to_message_id
                
            result = await self._make_request("sendMessage", data)
            return result.get("ok", False)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def send_typing_action(self, chat_id: int) -> None:
        """Send typing indicator."""
        try:
            await self._make_request("sendChatAction", {
                "chat_id": chat_id,
                "action": "typing"
            })
        except Exception:
            pass  # Non-critical
    
    async def set_webhook(self, webhook_url: str) -> bool:
        """Set the webhook URL for receiving updates."""
        try:
            result = await self._make_request("setWebhook", {
                "url": webhook_url,
                "allowed_updates": ["message", "callback_query"]
            })
            if result.get("ok"):
                logger.info(f"Webhook set to: {webhook_url}")
                return True
            logger.error(f"Failed to set webhook: {result}")
            return False
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False
    
    async def delete_webhook(self) -> bool:
        """Delete the webhook (switch to polling mode)."""
        try:
            result = await self._make_request("deleteWebhook")
            return result.get("ok", False)
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False
    
    async def get_updates(self, offset: int = 0, timeout: int = 30) -> list:
        """Get updates using long polling (for development)."""
        try:
            result = await self._make_request("getUpdates", {
                "offset": offset,
                "timeout": timeout,
                "allowed_updates": ["message"]
            })
            return result.get("result", [])
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []
    
    def _get_welcome_message(self, user_name: str) -> str:
        """Generate welcome message."""
        return f"""🎬 *Welcome to Primes and Zooms, {user_name}!*

I'm your rental assistant for premium camera and video equipment in Pune.

*How can I help you today?*
• Ask about our equipment (cameras, lenses, lighting)
• Learn about rental pricing and packages
• Understand our booking process
• Get shop location and contact info

Just type your question and I'll find the answer! 📸

_Type /help to see all commands_"""
    
    def _get_help_message(self) -> str:
        """Generate help message."""
        return """📋 *Available Commands*

/start - Welcome message
/help - Show this help
/equipment - Browse equipment categories
/contact - Get our contact information

*Or just ask me anything!* For example:
• "What cameras do you have?"
• "How much does it cost to rent a Sony A7S III?"
• "What's your cancellation policy?"
• "Do you require a security deposit?"

I'll search our knowledge base and give you accurate answers! 🎯"""
    
    def _get_equipment_message(self) -> str:
        """Generate equipment categories message."""
        return """📸 *Equipment Categories at Primes and Zooms*

🎥 *Cameras*
• Cinema cameras (RED, ARRI, Blackmagic)
• Mirrorless (Sony, Canon, Nikon)
• DSLRs

🔭 *Lenses*
• Prime lenses (Zeiss, Sigma Art)
• Zoom lenses (24-70mm, 70-200mm)
• Cinema lenses
• Specialty (Macro, Tilt-shift)

💡 *Lighting*
• LED panels
• Softboxes
• RGB lights
• Light stands & modifiers

🎤 *Audio*
• Wireless microphones
• Boom mics
• Audio recorders

🎬 *Grip & Support*
• Tripods & monopods
• Gimbals & stabilizers
• Sliders
• Rigs & cages

_Ask me about any specific equipment for details and pricing!_"""
    
    def _get_contact_message(self) -> str:
        """Generate contact information message."""
        return """📍 *Contact Primes and Zooms*

🏪 *Visit Us:*
Pune, Maharashtra, India

🌐 *Website:*
[www.primesandzooms.com](https://www.primesandzooms.com)

📞 *Get in Touch:*
Visit our website for current contact details and booking.

⏰ *Rental Process:*
1. Browse equipment online
2. Check availability
3. Book your rental
4. Pick up or get delivery

_Visit our website for the most up-to-date information!_"""
    
    async def handle_command(self, command: str, chat_id: int, user_name: str) -> str:
        """Handle bot commands."""
        command = command.lower().strip()
        
        if command in ["/start", "/start@primesandzooms_bot"]:
            return self._get_welcome_message(user_name)
        elif command in ["/help", "/help@primesandzooms_bot"]:
            return self._get_help_message()
        elif command in ["/equipment", "/equipment@primesandzooms_bot"]:
            return self._get_equipment_message()
        elif command in ["/contact", "/contact@primesandzooms_bot"]:
            return self._get_contact_message()
        else:
            return None  # Not a recognized command
    
    async def handle_message(self, text: str, chat_id: int, user_name: str) -> str:
        """Handle incoming message and generate response using RAG."""
        # Check if it's a command
        if text.startswith("/"):
            response = await self.handle_command(text, chat_id, user_name)
            if response:
                return response
            # If unrecognized command, treat as question
            text = text.lstrip("/")
        
        # Use RAG engine to generate response
        try:
            rag = get_rag_engine()
            response = await rag.query(text)
            
            # Format for Telegram
            answer = response.get("answer", "I'm sorry, I couldn't find an answer to that question.")
            
            # Add helpful footer for low-confidence responses
            if len(response.get("sources", [])) == 0:
                answer += "\n\n_💡 For specific questions about availability and pricing, please visit [primesandzooms.com](https://www.primesandzooms.com) or contact us directly._"
            
            return answer
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return """I apologize, but I'm having trouble accessing our information right now. 🔧

Please try again in a moment, or visit [primesandzooms.com](https://www.primesandzooms.com) for immediate assistance."""
    
    async def process_webhook_update(self, update: dict) -> None:
        """Process an incoming webhook update."""
        try:
            message = update.get("message", {})
            if not message:
                return
            
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")
            user = message.get("from", {})
            user_name = user.get("first_name", "there")
            
            if not chat_id or not text:
                return
            
            # Send typing indicator
            await self.send_typing_action(chat_id)
            
            # Process message and get response
            response = await self.handle_message(text, chat_id, user_name)
            
            # Send response
            await self.send_message(chat_id, response)
            
            logger.info(f"Processed message from {user_name} ({chat_id})")
            
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}")


# Singleton instance
telegram_bot = TelegramBot()
