from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models import PolicyDocument
from app.services.policy import save_policy, set_active

router = APIRouter(prefix="/policy", tags=["policy"])


class PolicyOut(BaseModel):
    id: int
    label: str
    filename: str
    content_type: str | None
    char_count: int | None
    is_active: bool
    uploaded_at: datetime
    preview: str | None = None

    class Config:
        from_attributes = True


def _to_out(doc: PolicyDocument, include_preview: bool = True) -> PolicyOut:
    preview = doc.raw_text[:600].strip() + "…" if include_preview and doc.raw_text else None
    return PolicyOut(
        id=doc.id,
        label=doc.label,
        filename=doc.filename,
        content_type=doc.content_type,
        char_count=doc.char_count,
        is_active=doc.is_active,
        uploaded_at=doc.uploaded_at,
        preview=preview,
    )


@router.post("/upload", response_model=PolicyOut)
async def upload_policy(
    file: UploadFile = File(...),
    label: str = Form(...),
    db: Session = Depends(get_db),
):
    allowed = (".pdf", ".docx", ".doc", ".txt", ".md")
    if not any(file.filename.lower().endswith(ext) for ext in allowed):
        raise HTTPException(400, f"Unsupported file type. Allowed: {', '.join(allowed)}")
    content = await file.read()
    try:
        doc = save_policy(db, content, file.filename, label)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return _to_out(doc)


@router.get("", response_model=List[PolicyOut])
def list_policies(db: Session = Depends(get_db)):
    docs = db.query(PolicyDocument).order_by(PolicyDocument.uploaded_at.desc()).all()
    return [_to_out(d) for d in docs]


@router.get("/active", response_model=PolicyOut | None)
def get_active_policy(db: Session = Depends(get_db)):
    doc = (
        db.query(PolicyDocument)
        .filter(PolicyDocument.is_active == True)  # noqa: E712
        .order_by(PolicyDocument.uploaded_at.desc())
        .first()
    )
    return _to_out(doc) if doc else None


@router.patch("/{policy_id}/activate", response_model=PolicyOut)
def activate(policy_id: int, db: Session = Depends(get_db)):
    try:
        doc = set_active(db, policy_id, True)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return _to_out(doc)


@router.patch("/{policy_id}/deactivate", response_model=PolicyOut)
def deactivate(policy_id: int, db: Session = Depends(get_db)):
    try:
        doc = set_active(db, policy_id, False)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return _to_out(doc)


@router.delete("/{policy_id}")
def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    doc = db.get(PolicyDocument, policy_id)
    if not doc:
        raise HTTPException(404, "Policy not found")
    db.delete(doc)
    db.commit()
    return {"deleted": policy_id}
