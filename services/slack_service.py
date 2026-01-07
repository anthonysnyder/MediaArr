"""
Slack notification service
"""

import requests
import os


class SlackService:
    """Handles Slack webhook notifications"""

    def __init__(self, webhook_url: str = None):
        """
        Initialize Slack service with webhook URL.

        Args:
            webhook_url: Slack webhook URL (optional)
        """
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL')

    def send_notification(self, message: str, local_path: str = None, image_url: str = None):
        """
        Send a notification to Slack about artwork downloads.

        Args:
            message: Notification message
            local_path: Local path where artwork was saved (optional)
            image_url: URL of the artwork image to display (optional)

        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.webhook_url:
            print("Slack webhook URL not configured, skipping notification")
            return False

        try:
            payload = {"text": message}

            # Add attachment with image if provided
            if local_path or image_url:
                payload["attachments"] = [{}]

                if local_path:
                    payload["attachments"][0]["text"] = f"Saved to: {local_path}"

                if image_url:
                    payload["attachments"][0]["image_url"] = image_url

            response = requests.post(self.webhook_url, json=payload)

            if response.status_code == 200:
                print(f"Slack notification sent successfully")
                return True
            else:
                print(f"Failed to send Slack notification. Status code: {response.status_code}")
                return False

        except Exception as e:
            print(f"Error sending Slack notification: {e}")
            return False
