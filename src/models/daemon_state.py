from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta

class DaemonProcessState(BaseModel):
    """
    Represents the state of the autonomous background operation daemon.
    """
    daemon_start_timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp when the daemon was started.")
    last_check_timestamp: Optional[datetime] = Field(None, description="Timestamp of the last email check.")
    last_successful_fetch_timestamp: Optional[datetime] = Field(None, description="Timestamp of last successful email fetch. Used as 'since' filter for next run.")
    check_interval_duration: timedelta = Field(timedelta(minutes=15), description="Duration between email checks.")
    total_processing_cycles: int = Field(0, description="Total number of processing cycles completed.")
    emails_processed_count: int = Field(0, description="Total number of emails processed successfully.")
    error_count: int = Field(0, description="Total number of errors encountered.")
    current_status: str = Field("stopped", description="Current status of the daemon (running, stopped, error).")
    last_processed_email_id: Optional[str] = Field(None, description="The ID of the last email successfully processed to prevent duplicates.")
