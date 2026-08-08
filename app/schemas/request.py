from pydantic import BaseModel,Field


class IngestRequest(BaseModel):

    pdf_path: str = Field(
        ...,
        description="Path of PDF"
    )


class AskRequest(BaseModel):
    session_id: str
    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="User question",
        examples=["How do I reset my password?"]
    )