from datetime import datetime, timezone
from sqlalchemy import Integer, DateTime, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Vector(Base):
    __tablename__ = "vectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dim: Mapped[int] = mapped_column(Integer, nullable=False)
    # 1 byte per dimension (int8), packed contiguously
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )