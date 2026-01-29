"""
Telegram Webhook Routes
Handles incoming updates from Telegram Bot API
"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import logging
import hmac
import hashlib

from app.config import get_settings
from app.services.telegram_bot import telegram_bot

settings = get_settings()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/telegram", tags=["telegram"])


class WebhookSetup(BaseModel):
    """Request model for setting up webhook"""
    webhook_url: str


class SendMessageRequest(BaseModel):
    """Request model for sending a message"""
    chat_id: int
    text: str
    parse_mode: Optional[str] = None


@router.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receive incoming updates from Telegram.
    This endpoint should be set as the webhook URL in Telegram.
    """
    try:
        # Verify the request is from Telegram (optional but recommended)
        # You can add X-Telegram-Bot-Api-Secret-Token header verification here
        
        update_data = await request.json()
        logger.info(f"Received Telegram update: {update_data.get('update_id')}")
        
        # Process in background to respond quickly to Telegram
        background_tasks.add_task(telegram_bot.process_webhook_update, update_data)
        
        return {"ok": True}
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Return 200 anyway to prevent Telegram from retrying
        return {"ok": True, "error": str(e)}


@router.post("/webhook/setup")
async def setup_webhook(request: WebhookSetup):
    """
    Set up the Telegram webhook URL.
    Call this once after deployment with your public URL.
    
    Example:
    POST /telegram/webhook/setup
    {"webhook_url": "https://your-domain.com/telegram/webhook"}
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status_code=400,
            detail="TELEGRAM_BOT_TOKEN not configured"
        )
    
    success = await telegram_bot.set_webhook(request.webhook_url)
    
    if success:
        return {
            "ok": True,
            "message": f"Webhook set to: {request.webhook_url}"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to set webhook"
        )


@router.delete("/webhook")
async def delete_webhook():
    """
    Delete the current webhook (switch to polling mode).
    Useful for local development.
    """
    success = await telegram_bot.delete_webhook()
    
    if success:
        return {"ok": True, "message": "Webhook deleted"}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete webhook"
        )


@router.post("/send")
async def send_message(request: SendMessageRequest):
    """
    Send a message to a specific chat.
    Useful for sending notifications or proactive messages.
    
    Example:
    POST /telegram/send
    {"chat_id": 123456789, "text": "Hello!", "parse_mode": "Markdown"}
    """
    success = await telegram_bot.send_message(
        chat_id=request.chat_id,
        text=request.text,
        parse_mode=request.parse_mode
    )
    
    if success:
        return {"ok": True, "message": "Message sent"}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send message"
        )


@router.get("/health")
async def telegram_health():
    """Check if Telegram bot is configured and ready"""
    if not settings.TELEGRAM_BOT_TOKEN:
        return {
            "ok": False,
            "status": "not_configured",
            "message": "TELEGRAM_BOT_TOKEN not set"
        }
    
    return {
        "ok": True,
        "status": "ready",
        "message": "Telegram bot is configured"
    }
