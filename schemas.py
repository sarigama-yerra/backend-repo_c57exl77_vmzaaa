"""
Database Schemas for Pranesta Jewellery

Each Pydantic model represents a MongoDB collection. The collection name
is the lowercase of the class name (e.g., Product -> "product").
"""
from pydantic import BaseModel, Field
from typing import Optional, List

class Product(BaseModel):
    """
    Products sold by Pranesta Jewellery
    Collection: "product"
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in INR")
    category: str = Field(..., description="Category: silver | oxidised")
    image: Optional[str] = Field(None, description="Image URL")
    in_stock: bool = Field(True, description="In stock flag")

class Inquiry(BaseModel):
    """
    Customer inquiries / query notes
    Collection: "inquiry"
    """
    name: str = Field(..., description="Customer full name")
    email: str = Field(..., description="Customer email")
    phone: Optional[str] = Field(None, description="Phone number")
    message: str = Field(..., description="Inquiry message or notes")

class OrderItem(BaseModel):
    product_id: str = Field(..., description="Referenced product _id as string")
    title: str = Field(..., description="Snapshot of product title")
    price: float = Field(..., ge=0, description="Snapshot of price")
    qty: int = Field(..., ge=1, description="Quantity")
    image: Optional[str] = Field(None, description="Snapshot of image")

class Order(BaseModel):
    """
    Customer orders
    Collection: "order"
    """
    items: List[OrderItem]
    total: float = Field(..., ge=0)
    customer_name: str
    customer_email: str
    customer_address: Optional[str] = None
    status: str = Field("pending", description="pending | paid | failed")
    payment_reference: Optional[str] = None
