from pydantic import BaseModel


class AddIn(BaseModel):
    session_id: str
    product_id: str
    quantity: int = 1


class CartSetIn(BaseModel):
    session_id: str
    product_id: str
    quantity: int          # 0 removes the item


class SessionIn(BaseModel):
    session_id: str


class ChatIn(BaseModel):
    message: str
    session_id: str | None = None


class CheckoutIn(BaseModel):
    session_id: str
    customer: dict[str, str] = {}


class CaptureIn(BaseModel):
    session_id: str
    order_id: str
