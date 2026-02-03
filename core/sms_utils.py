import africastalking
from decouple import config
import logging

logger = logging.getLogger(__name__)

def send_sms(numbers, message):
    """
    Send SMS using Africa's Talking.
    numbers: list of phone numbers (e.g. ['+255710000000'])
    message: plain text to send
    """
    username = config("AFRICASTALKING_USERNAME")
    api_key = config("AFRICASTALKING_API_KEY")
    sender_id = config("AFRICASTALKING_SENDER_ID")

    africastalking.initialize(username, api_key)
    sms = africastalking.SMS

    try:
        # ✅ This actually sends the message
        response = sms.send(message, numbers, sender_id)

        # Log details to the console only (not inside the SMS)
        logger.info(f"SMS sent successfully to {numbers}: {response}")

        # Return metadata for internal use, not for sending
        return response

    except Exception as e:
        logger.error(f"SMS sending failed: {e}", exc_info=True)
        return {"error": str(e)}
