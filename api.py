from fastapi import FastAPI
from pydantic import BaseModel
from services.chat_service import process_user_query

app = FastAPI(title="Payroll Chatbot API")


# Request schema
class ChatRequest(BaseModel):
    query: str
    employee_id: int = 1


# Response schema
class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    try:
        result = process_user_query(
            user_query=req.query,
            employee_id=req.employee_id
        )

        # If your function returns dict
        if isinstance(result, dict):
            answer = result.get("answer") or result.get("response") or str(result)

        else:
            answer = str(result)

        return ChatResponse(response=answer)

    except Exception as e:
        return ChatResponse(
            response=f"ERROR: {str(e)}"
        )