from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import httpx

from backend.database import get_db
from backend.auth import get_current_user
from backend.models import User
from backend import crud
from backend.config import settings
from backend.schemas import (
    ProductCreate, ProductUpdate, ProductResponse,
    AIDescriptionRequest, AIDescriptionResponse
)
from backend.security import limiter, sanitize, sanitize_sku, is_safe_input

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=List[ProductResponse])
@limiter.limit("200/minute")
async def get_products(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    products = crud.get_products(db, skip=skip, limit=limit)
    return products


@router.get("/{product_id}", response_model=ProductResponse)
@limiter.limit("200/minute")
async def get_product(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    return product


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_product(
    request: Request,
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_safe_input(product.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid characters detected in product name"
        )
    
    product.name = sanitize(product.name, max_length=255)
    product.sku = sanitize_sku(product.sku)
    if product.description:
        product.description = sanitize(product.description, max_length=2000)
    
    existing = crud.get_product_by_sku(db, product.sku)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{product.sku}' already exists"
        )
    
    return crud.create_product(db, product)


@router.put("/{product_id}", response_model=ProductResponse)
@limiter.limit("30/minute")
async def update_product(
    request: Request,
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if product.name:
        if not is_safe_input(product.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid characters detected in product name"
            )
        product.name = sanitize(product.name, max_length=255)
    if product.sku:
        product.sku = sanitize_sku(product.sku)
    if product.description:
        product.description = sanitize(product.description, max_length=2000)
    
    existing = crud.get_product_by_id(db, product_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    if product.sku and product.sku != existing.sku:
        duplicate = crud.get_product_by_sku(db, product.sku)
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with SKU '{product.sku}' already exists"
            )
    
    updated_product = crud.update_product(db, product_id, product)
    return updated_product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_product(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = crud.delete_product(db, product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    return None


@router.post("/generate-description", response_model=AIDescriptionResponse)
@limiter.limit("5/minute")
async def generate_product_description(
    request: Request,
    ai_request: AIDescriptionRequest,
    current_user: User = Depends(get_current_user)
):
    raw_name = ai_request.product_name
    if not raw_name or not is_safe_input(raw_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product name"
        )
    
    product_name = sanitize(raw_name, max_length=255)
    
    if settings.OPENAI_API_KEY:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a professional product copywriter. Write concise, engaging product descriptions in exactly 2 sentences."
                            },
                            {
                                "role": "user",
                                "content": f"Write a professional 2-sentence marketing description for: '{product_name}'"
                            }
                        ],
                        "max_tokens": 150,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    description = data["choices"][0]["message"]["content"].strip()
                    return AIDescriptionResponse(description=description)
        except Exception as e:
            print(f"OpenAI error: {e}")
    
    if settings.GEMINI_API_KEY:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={settings.GEMINI_API_KEY}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{
                            "parts": [{
                                "text": f"Write a professional 2-sentence marketing description for a product named '{product_name}'. Be concise and engaging."
                            }]
                        }],
                        "generationConfig": {
                            "maxOutputTokens": 150,
                            "temperature": 0.7
                        }
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    description = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return AIDescriptionResponse(description=description)
        except Exception as e:
            print(f"Gemini error: {e}")
    
    description = generate_template_description(product_name)
    return AIDescriptionResponse(description=description)


def generate_template_description(product_name: str) -> str:
    import random
    
    name_lower = product_name.lower()
    
    templates = {
        "laptop": [
            f"The {product_name} delivers exceptional performance for professionals and power users alike. Experience seamless multitasking and stunning visuals in a sleek, portable design.",
            f"Elevate your productivity with the {product_name}, featuring cutting-edge technology and premium build quality. Perfect for work, creativity, and entertainment on the go."
        ],
        "monitor": [
            f"The {product_name} brings your content to life with vibrant colors and crystal-clear resolution. Designed for professionals who demand visual excellence.",
            f"Experience immersive visuals with the {product_name}, offering exceptional clarity and eye-comfort technology. Ideal for extended work sessions and multimedia enjoyment."
        ],
        "keyboard": [
            f"The {product_name} combines ergonomic design with responsive performance for all-day typing comfort. Built with premium materials for durability and style.",
            f"Type with precision and comfort using the {product_name}. Features tactile feedback and customizable options to match your workflow perfectly."
        ],
        "mouse": [
            f"The {product_name} offers precise tracking and ergonomic design for enhanced productivity. Perfect for professionals seeking comfort and accuracy.",
            f"Navigate with ease using the {product_name}, featuring smooth tracking and comfortable grip. Designed for extended use without fatigue."
        ],
        "printer": [
            f"The {product_name} delivers professional-quality output with impressive speed and efficiency. Perfect for home offices and small businesses.",
            f"Produce stunning documents and graphics with the {product_name}. Reliable performance meets cost-effective operation."
        ],
        "webcam": [
            f"The {product_name} captures you in exceptional clarity for video calls and streaming. Features advanced low-light correction and crisp audio.",
            f"Look your best on every call with the {product_name}. Professional-grade video quality meets plug-and-play simplicity."
        ],
        "default": [
            f"The {product_name} combines quality craftsmanship with innovative design to deliver exceptional value. A reliable choice for discerning customers.",
            f"Discover the {product_name}, engineered for performance and built to last. Experience the perfect balance of quality and functionality.",
            f"Introducing the {product_name}: where premium quality meets practical design. Trusted by professionals and enthusiasts alike.",
            f"The {product_name} sets a new standard for excellence in its category. Designed with attention to detail and user experience in mind."
        ]
    }
    
    selected_templates = templates["default"]
    for keyword, category_templates in templates.items():
        if keyword in name_lower:
            selected_templates = category_templates
            break
    
    return random.choice(selected_templates)
