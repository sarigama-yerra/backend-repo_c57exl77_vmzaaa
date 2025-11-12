import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Literal, Any
from database import db, create_document, get_documents
from schemas import Product, Inquiry, Order, OrderItem
from bson import ObjectId

app = FastAPI(title="Pranesta Jewellery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utils

def to_str_id(doc: dict) -> dict:
    d = dict(doc)
    if d.get("_id"):
        d["_id"] = str(d["_id"]) if isinstance(d["_id"], ObjectId) else d["_id"]
    return d


@app.get("/")
def read_root():
    return {"brand": "Pranesta Jewellery", "message": "Backend running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# ----------------- Products -----------------

class ProductCreate(Product):
    pass

@app.get("/api/categories")
def get_categories():
    return ["silver", "oxidised"]

@app.post("/api/products")
def create_product(prod: ProductCreate):
    try:
        _id = create_document("product", prod)
        return {"_id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products")
def list_products(category: Optional[Literal["silver", "oxidised"]] = None) -> List[dict]:
    try:
        filt = {"category": category} if category else {}
        docs = get_documents("product", filt)
        return [to_str_id(x) for x in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------- Inquiries -----------------

@app.post("/api/inquiries")
def create_inquiry(inquiry: Inquiry):
    try:
        _id = create_document("inquiry", inquiry)
        return {"_id": _id, "status": "received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------- Orders & Payments -----------------

class CreateOrderRequest(BaseModel):
    items: List[OrderItem]
    customer_name: str
    customer_email: str
    customer_address: Optional[str] = None

@app.post("/api/orders")
def create_order(body: CreateOrderRequest):
    try:
        total = sum(i.price * i.qty for i in body.items)
        order = Order(
            items=body.items,
            total=total,
            customer_name=body.customer_name,
            customer_email=body.customer_email,
            customer_address=body.customer_address,
        )
        _id = create_document("order", order)
        return {"order_id": _id, "total": total, "status": "pending"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PaymentIntentRequest(BaseModel):
    order_id: str

@app.post("/api/payments/create-intent")
def create_payment_intent(body: PaymentIntentRequest):
    # Mock payment intent that returns a fake URL and reference
    try:
        ref = f"PRN-{body.order_id[-6:]}"
        payment_url = f"https://example-payments.test/checkout/{ref}"
        # Store reference on order
        try:
            db["order"].update_one({"_id": ObjectId(body.order_id)}, {"$set": {"payment_reference": ref}})
        except Exception:
            pass
        return {"reference": ref, "payment_url": payment_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PaymentConfirmRequest(BaseModel):
    order_id: str
    success: bool = True
    reference: Optional[str] = None

@app.post("/api/payments/confirm")
def confirm_payment(body: PaymentConfirmRequest):
    try:
        status = "paid" if body.success else "failed"
        update = {"status": status}
        if body.reference:
            update["payment_reference"] = body.reference
        res = db["order"].update_one({"_id": ObjectId(body.order_id)}, {"$set": update})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Order not found")
        return {"order_id": body.order_id, "status": status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
