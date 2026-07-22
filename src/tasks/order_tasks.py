from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from src.core.database import async_session_factory
from src.core.logger import get_logger
from src.models.order import Order

logger = get_logger(__name__)


class OrderTasks:
    """订单相关的异步任务."""

    @staticmethod
    async def auto_cancel_expired_orders(hours: int = 24) -> int:
        """
        自动取消超过指定时间仍未处理的订单。
        可被调度系统定时调用。
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cancelled_count = 0

        async with async_session_factory() as db:
            result = await db.execute(
                select(Order).where(
                    Order.status == "pending",
                    Order.created_at < cutoff,
                )
            )
            expired_orders = result.scalars().all()

            for order in expired_orders:
                order.status = "cancelled"
                cancelled_count += 1

            if cancelled_count > 0:
                await db.commit()
                logger.info(
                    "Auto-cancelled expired orders",
                    extra={"count": cancelled_count, "cutoff_hours": hours},
                )

        return cancelled_count
