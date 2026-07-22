"""initial migration (MySQL)

Revision ID: 0001
Revises:
Create Date: 2026-07-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("openid", sa.String(128), nullable=False, comment="微信openid"),
        sa.Column("nickname", sa.String(64), nullable=True, comment="昵称"),
        sa.Column("avatar_url", sa.String(512), nullable=True, comment="头像URL"),
        sa.Column("phone", sa.String(20), nullable=True, comment="手机号"),
        sa.Column("is_admin", sa.Boolean(), default=False, comment="是否管理员"),
        sa.Column("is_active", sa.Boolean(), default=True, comment="是否启用"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("openid"),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )

    # categories
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(32), nullable=False, comment="分类名称"),
        sa.Column("sort_order", sa.Integer(), default=0, comment="排序序号"),
        sa.Column("is_active", sa.Boolean(), default=True, comment="是否启用"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )

    # materials
    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(32), nullable=False, comment="材料名称"),
        sa.Column("category", sa.String(32), nullable=True, comment="材料分类"),
        sa.Column("description", sa.Text(), nullable=True, comment="材料说明"),
        sa.Column("is_allergen", sa.Boolean(), default=False, comment="是否为常见过敏原"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )

    # dishes
    op.create_table(
        "dishes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(64), nullable=False, comment="菜品名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="菜品描述"),
        sa.Column("price", sa.Numeric(10, 2), nullable=True, comment="定价"),
        sa.Column("image_url", sa.String(512), nullable=True, comment="图片URL"),
        sa.Column("category_id", sa.Integer(), nullable=True, comment="分类ID"),
        sa.Column("status", sa.String(20), server_default="active", comment="状态: active=已上架, inactive=已下架, pending_price=待定价"),
        sa.Column("is_recommended", sa.Boolean(), default=False, comment="是否推荐"),
        sa.Column("sales_count", sa.Integer(), default=0, comment="销量"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )

    # dish_materials (many-to-many)
    op.create_table(
        "dish_materials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("dish_id", sa.Integer(), nullable=False, comment="菜品ID"),
        sa.Column("material_id", sa.Integer(), nullable=False, comment="材料ID"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["dish_id"], ["dishes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )

    # orders
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(32), nullable=False, comment="订单编号"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="用户ID"),
        sa.Column("status", sa.String(20), server_default="pending", comment="状态: pending=待处理, confirmed=已确认, preparing=制作中, completed=已完成, cancelled=已取消"),
        sa.Column("total_price", sa.Numeric(10, 2), server_default="0", comment="总价"),
        sa.Column("note", sa.Text(), nullable=True, comment="订单备注"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_no"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )

    # order_items
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("dish_id", sa.Integer(), nullable=False, comment="菜品ID"),
        sa.Column("dish_name", sa.String(64), nullable=False, comment="下单时的菜品名称"),
        sa.Column("quantity", sa.Integer(), server_default="1", comment="数量"),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False, comment="单价"),
        sa.Column("excluded_material_ids", sa.Text(), nullable=True, comment="排除的材料ID列表(JSON数组)"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dish_id"], ["dishes.id"]),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )

    # pending_dishes
    op.create_table(
        "pending_dishes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="提交用户ID"),
        sa.Column("name", sa.String(64), nullable=False, comment="菜品名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="菜品描述"),
        sa.Column("image_url", sa.String(512), nullable=True, comment="参考图片URL"),
        sa.Column("suggested_price", sa.Numeric(10, 2), nullable=True, comment="建议价格"),
        sa.Column("status", sa.String(20), server_default="pending_price", comment="状态: pending_price=待定价, approved=已审核通过, rejected=已驳回"),
        sa.Column("admin_price", sa.Numeric(10, 2), nullable=True, comment="管理员定价"),
        sa.Column("admin_note", sa.Text(), nullable=True, comment="管理员备注"),
        sa.Column("admin_id", sa.Integer(), nullable=True, comment="审核管理员ID"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"]),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )


def downgrade() -> None:
    op.drop_table("pending_dishes")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("dish_materials")
    op.drop_table("dishes")
    op.drop_table("materials")
    op.drop_table("categories")
    op.drop_table("users")
