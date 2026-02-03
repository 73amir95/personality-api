from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import joblib
import pandas as pd
import os
from fastapi.templating import Jinja2Templates
from fastapi import Request, Form
from starlette import status
from starlette.responses import HTMLResponse, RedirectResponse
from routers.auth import get_current_user

model_path = "extrovert_model.pkl"
templates = Jinja2Templates(directory="templates")
router = APIRouter(
        prefix="/predict",
        tags=["predict"]
)

user_dependency = Annotated[dict, Depends(get_current_user)]

class PersonalityInput(BaseModel):
    Time_spent_Alone: float = Field(..., gt=-1, lt=25, description="Hours spent alone (Daily)")
    Stage_fear: str = Field(..., description="Do you have stage fear? (Yes/No)")
    Social_event_attendance: float = Field(..., gt=-1, lt=11, description="Frequency of attending social events (on scale 0 - 10)")
    Going_outside: float = Field(..., gt=-1, lt=8, description="Frequency of going outside (weekly on scale of 0-7)")
    Drained_after_socializing: str = Field(..., description="Do you feel drained after socializing? (Yes/No)")
    Friends_circle_size: float = Field(..., gt=-1, description="Number of friends in circle")
    Post_frequency: float = Field(..., gt=-1, lt=11, description="Frequency of posting on social media (on scale 0 - 10)")

if os.path.exists(model_path):
    model = joblib.load(model_path)
    print("Model loaded successfully.")
else:
    model = None
    print("Warning: Model file not found. Please ensure 'extrovert_model.pkl' is in the same folder.")


@router.get("/", response_class=HTMLResponse)
def home(user: user_dependency, request: Request):
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@router.post("/predict-form", response_class=HTMLResponse)
def predict_form(
        user: user_dependency,
        request: Request,
        Time_spent_Alone: float = Form(...),
        Stage_fear: str = Form(...),
        Social_event_attendance: float = Form(...),
        Going_outside: float = Form(...),
        Drained_after_socializing: str = Form(...),
        Friends_circle_size: float = Form(...),
        Post_frequency: float = Form(...)
):
    if not user:
        raise HTTPException(status_code=401, detail='Authentication failed.')

    if not model:
        return HTMLResponse("Model not loaded", status_code=500)

    stage_fear_val = 1 if Stage_fear.lower() == "yes" else 0
    drained_val = 1 if Drained_after_socializing.lower() == "yes" else 0

    features = [[
        Time_spent_Alone,
        stage_fear_val,
        Social_event_attendance,
        Going_outside,
        drained_val,
        Friends_circle_size,
        Post_frequency
    ]]

    columns = [
        'Time_spent_Alone', 'Stage_fear', 'Social_event_attendance',
        'Going_outside', 'Drained_after_socializing',
        'Friends_circle_size', 'Post_frequency'
    ]

    df = pd.DataFrame(features, columns=columns)

    prediction = model.predict(df)[0]
    result = "Extrovert" if prediction == 1 else "Introvert"

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "result": result
        }
    )

@router.get("/", response_class=HTMLResponse)
def home(user: user_dependency, request: Request):
    if not user:
        raise HTTPException(status_code=401, detail='Authentication failed.')

    return templates.TemplateResponse("index.html", {"request": request})