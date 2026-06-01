from pydantic import BaseModel, Field

class SendMessageIn(BaseModel):
    profesional_id: int | None = None
    cliente_id: int | None = None
    texto: str = Field(min_length=1, max_length=2000)

class JoinConversationIn(BaseModel):
    profesional_id: int
    cliente_id: int
    limit: int | None = 50