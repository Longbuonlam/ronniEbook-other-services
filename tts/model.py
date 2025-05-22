from pydantic import BaseModel
from typing import Optional

class UserRecord(BaseModel):
    path: str
    recordUrl: str
    originalName: str
    size: Optional[int] = None

class AudioRequest(BaseModel):
    prompt: str
    language: str
    normalize_vi_text: bool
    user_record: UserRecord
