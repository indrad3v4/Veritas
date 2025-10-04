"""
Notification Domain Entity
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from .enums import NotificationType

class Notification(BaseModel):
    """
    Notification entity for real-time user updates

    Business Rules:
    - Each notification targets specific user
    - Must reference source report
    - Auto-expire after 30 days
    """

    id: str = Field(..., description="Unique notification ID")
    user_id: str = Field(..., description="Target user ID")
    report_id: str = Field(..., description="Related report ID")

    # Notification content
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")

    # Additional context
    context: Dict[str, Any] = Field(default_factory=dict)

    # Status
    read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def mark_as_read(self):
        """Mark notification as read"""
        self.read = True
        self.read_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if notification has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
