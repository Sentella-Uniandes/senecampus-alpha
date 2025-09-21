from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
    
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(120), nullable=False, index=True)  # local-part only, lowercase
    first_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    vector_id: Mapped[int | None] = mapped_column(ForeignKey("vectors.id", ondelete="SET NULL"))
    vector = relationship("Vector", lazy="joined")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

