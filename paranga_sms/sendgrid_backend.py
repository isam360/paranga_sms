import base64
import logging
from decouple import config
from django.core.mail.backends.base import BaseEmailBackend
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

logger = logging.getLogger(__name__)

class SendGridAPIEmailBackend(BaseEmailBackend):
    """
    Custom Django Email Backend for SendGrid with full attachment support.
    """

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        sent_count = 0
        client = SendGridAPIClient(config("SENDGRID_API_KEY"))

        for message in email_messages:
            try:
                mail = Mail(
                    from_email=message.from_email,
                    to_emails=[to for to in message.to],
                    subject=message.subject,
                    plain_text_content=message.body
                )

                # Handle attachments (supports multiple)
                for attachment in message.attachments:
                    # Django attachments can be (filename, content, mimetype)
                    if isinstance(attachment, tuple):
                        filename, content, mimetype = attachment
                        encoded_file = base64.b64encode(content).decode()
                        sg_attachment = Attachment(
                            FileContent(encoded_file),
                            FileName(filename),
                            FileType(mimetype),
                            Disposition("attachment")
                        )
                        mail.add_attachment(sg_attachment)

                # Send the email
                response = client.send(mail)
                if 200 <= response.status_code < 300:
                    sent_count += 1
                else:
                    logger.warning(f"SendGrid returned status {response.status_code} for {message.to}")

            except Exception as e:
                if not self.fail_silently:
                    raise
                logger.error(f"Failed to send email to {message.to}: {e}", exc_info=True)

        return sent_count
