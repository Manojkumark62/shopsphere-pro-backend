
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
from app.routers import product_attribute
from app.routers import product_pricing
from app.routers import inventory
from app.routers import warehouse
from app.routers import inventory_transfer
from app.routers import low_stock
from app.routers import cart
from app.routers import cart_pricing
from app.routers import wishlist
from app.routers import coupon

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
app.include_router(product_attribute.router)
app.include_router(product_pricing.router)
app.include_router(inventory.router)
app.include_router(warehouse.router)
app.include_router(inventory_transfer.router)
app.include_router(low_stock.router)
app.include_router(cart.router)
app.include_router(cart_pricing.router)
app.include_router(wishlist.router)
app.include_router(coupon.router)

@app.get("/")
def home():
    return {"message": "Welcome to ShopSphere Pro API"}
