
from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.registration import router as registration_router
from app.routers.customer_profile import router as customer_profile_router
from app.routers.customer_address import router as customer_address_router
from app.routers.product_category import router as product_category_router
from app.routers.brand import router as brand_router
from app.routers.product import router as product_router
from app.routers.product_variant import router as product_variant_router
from app.routers import product_media

app = FastAPI(title="ShopSphere Pro API", description="E-Commerce Platform Backend", version="1.0.0")
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(registration_router)
app.include_router(customer_profile_router)
app.include_router(customer_address_router)
app.include_router(product_category_router)
app.include_router(brand_router)
app.include_router(product_router)
app.include_router(product_variant_router)
app.include_router(product_media.router)

@app.get("/")
def home():
    return {"message": "Welcome to ShopSphere Pro API"}
