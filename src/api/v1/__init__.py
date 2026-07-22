from fastapi import APIRouter

from src.api.v1 import users, menu, orders, admin

router = APIRouter()

router.include_router(users.router, prefix="/users", tags=["用户"])
router.include_router(menu.router, prefix="/menu", tags=["菜单"])
router.include_router(orders.router, prefix="/orders", tags=["订单"])
router.include_router(admin.router, prefix="/admin", tags=["管理后台"])
