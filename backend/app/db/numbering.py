"""Per-company sequential code generation.

Auto-generates unique codes like ``CUS-001`` scoped to a company. Manual codes
are always respected: generation skips any number that is already taken, so a
manually-entered code can never collide with an auto-generated one.

The counter lives in ``numbering_sequences`` (one row per company per kind) and
is locked with ``SELECT ... FOR UPDATE`` so concurrent requests cannot mint the
same number. Every business table keeps its ``UniqueConstraint(company_id, code)``
as the database-level backstop.
"""

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db.base_class import Base


class NumberingSequence(Base):
    __tablename__ = "numbering_sequences"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "kind", name="uq_numbering_sequences_company_kind"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    last_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


def generate_code(
    db: Session,
    company_id: int,
    kind: str,
    prefix: str,
    model,
    field: str,
    pad: int = 3,
) -> str:
    """Return the next unique ``{prefix}-{n:0{pad}d}`` code for a company.

    ``model``/``field`` identify the table+column used to detect collisions with
    manually-entered codes (e.g. ``Partner`` / ``"code"``). The returned code is
    guaranteed not to exist yet for that company.
    """
    seq = db.scalar(
        select(NumberingSequence)
        .where(
            NumberingSequence.company_id == company_id,
            NumberingSequence.kind == kind,
        )
        .with_for_update()
    )
    if seq is None:
        seq = NumberingSequence(company_id=company_id, kind=kind, last_value=0)
        db.add(seq)
    while True:
        seq.last_value += 1
        code = f"{prefix}-{seq.last_value:0{pad}d}"
        exists = db.scalar(
            select(getattr(model, "id"))
            .where(
                getattr(model, "company_id") == company_id,
                getattr(model, field) == code,
            )
            .limit(1)
        )
        if exists is None:
            db.flush()
            return code
