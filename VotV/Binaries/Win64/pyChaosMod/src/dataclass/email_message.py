import logging
from dataclasses import dataclass
from typing import Optional, Tuple, List

@dataclass
class EmailMessage:
    subject: str
    body: str
    user: str = "user"

class EmailCommandProcessor:
    valid_users = [
        "Dr_Bao",
        "Prof_Lea",
        "Auto",
        "Dr_Max",
        "Dr_Ken",
        "Dr_Ena",
        "Dr_Ula",
        "Dr_Ler",
        "user",
        "Dr_Noa"
    ]

    @staticmethod
    def validate_user(user: Optional[str]) -> str:
        """
        Validate user against the valid_users list.
        Returns "user" if the provided user is not in the valid_users list.
        """
        if user and user in EmailCommandProcessor.valid_users:
            return user
        return "user"

    @staticmethod
    def find_field(content: str, field_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Find a field in the content string, preserving case of the value.
        Returns tuple of (value, remaining_content) or (None, None) if not found.
        """
        marker = field_name.lower() + ':'
        
        # Find the start of our field
        field_start = content.lower().find(marker)
        if field_start == -1:
            return None, None
            
        # Find the start of the next field
        remaining_content = content[field_start + len(marker):]
        next_field_markers = ['subject:', 'body:', 'user:']
        next_field_pos = float('inf')
        
        for next_marker in next_field_markers:
            pos = remaining_content.lower().find(next_marker)
            if pos != -1 and pos < next_field_pos:
                next_field_pos = pos
                
        # Extract the value
        if next_field_pos != float('inf'):
            value = remaining_content[:next_field_pos].strip()
            remaining = remaining_content[next_field_pos:]
        else:
            value = remaining_content.strip()
            remaining = ""
            
        return value, remaining

    @staticmethod
    def parse_email_string(content: str) -> Optional[EmailMessage]:
        """
        Parse an email string in the format 'subject:hello body:hello user:username'
        where user is optional.
        """
        try:
            logging.debug(f"Parsing email string: {content}")
            
            # Find subject
            subject, remaining = EmailCommandProcessor.find_field(content, 'subject')
            if not subject:
                logging.debug("Failed to find valid 'subject:' marker")
                return None
                
            # Find body
            body, remaining = EmailCommandProcessor.find_field(remaining or content, 'body')
            if not body:
                logging.debug("Failed to find valid 'body:' marker")
                return None
                
            # Find optional user
            user = None
            if remaining:
                user_value, _ = EmailCommandProcessor.find_field(remaining, 'user')
                if user_value:
                    user = EmailCommandProcessor.validate_user(user_value)
            
            if not user:
                user = "user"
            
            logging.debug(f"Successfully parsed - subject: {subject}, body: {body}, user: {user}")
            return EmailMessage(subject=subject, body=body, user=user)
            
        except Exception as e:
            logging.exception(f"Error parsing email string: {str(e)}")
            return None

    @staticmethod
    def is_valid_email_format(content: str) -> bool:
        """
        Check if the email string has valid format.
        """
        result = EmailCommandProcessor.parse_email_string(content) is not None
        logging.debug(f"Email format validation result: {result} for content: {content}")
        return result