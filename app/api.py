import logging
from typing import Literal
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.explanation import top_reasons
from src import predict as P

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Kestrel Returns Risk")


class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    order_id: str
    order_placed_at: str
    customer_id: str
    sku: str
    sales_channel: Literal["app", "web", "marketplace", "partner_outlet"]
    payment_mode: Literal["prepaid_upi", "prepaid_card", "cod", "emi"]
    discount_pct: float = Field(ge=0, le=100)
    qty: int = Field(ge=1, le=50)
    order_value_inr: float = Field(gt=0)
    promised_delivery_days: int = Field(ge=0, le=60)
    delivery_pincode: int = Field(ge=0, le=999999)
    is_gift: Literal["Y", "N"]
    customer_prior_orders: int = Field(ge=0)
    customer_prior_returns: int = Field(ge=0)

    @model_validator(mode="after")
    def returns_not_above_orders(self):
        if self.customer_prior_returns > self.customer_prior_orders:
            raise ValueError("customer_prior_returns cannot exceed customer_prior_orders")
        try:
            pd.to_datetime(self.order_placed_at)
        except Exception:
            raise ValueError("order_placed_at must look like 2026-07-01 09:30")
        return self


def error(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": message})


@app.exception_handler(RequestValidationError)
async def bad_input(request: Request, exc: RequestValidationError):
    parts = [f"{'.'.join(str(x) for x in e['loc'][1:])}: {e['msg']}" for e in exc.errors()]
    return error(422, "Invalid order. " + "; ".join(parts))


@app.get("/health")
def health():
    try:
        m = P.load_model()
        P.load_lookup()
    except P.ModelUnavailable as exc:
        return error(503, str(exc))
    return {"status": "ok", "model": m["kind"], "threshold": m["threshold"]}


@app.post("/predict")
def predict(order: Order):
    record = order.model_dump()
    try:
        P.check_references(record)
        frame = pd.DataFrame([record])
        prob, feats = P.score_frame(frame)
        p = float(prob[0])
        return {"order_id": order.order_id, "return_probability": round(p, 4), "risk_level": P.risk_level(p),
                "decision": P.decision(p), "reasons": top_reasons(feats)}
    except P.UnknownReference as exc:
        return error(404, str(exc))
    except P.ModelUnavailable as exc:
        return error(503, str(exc))
    except Exception:
        logging.exception("prediction failed")
        return error(500, "Prediction failed. Please check the order values and try again.")
