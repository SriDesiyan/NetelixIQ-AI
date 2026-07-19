"""
NetElixIQ AI — Data Ingestion API
Handles CSV upload, validation, and storage for all marketing channels.
"""
import io
import os
import json
import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db, CampaignRecord
from backend.services.ingestion.parsers import parse_channel_csv, parse_multiple_channels
from backend.services.ingestion.validator import DataValidator

logger = logging.getLogger(__name__)
router = APIRouter()
validator = DataValidator()


class IngestionResponse(BaseModel):
    session_id: str
    channel: str
    rows_ingested: int
    validation: dict
    preview: list
    timestamp: str


class MultiChannelIngestionResponse(BaseModel):
    session_id: str
    total_rows: int
    channels: List[str]
    validation: dict
    timestamp: str


@router.post("/ingest/upload", response_model=IngestionResponse)
async def upload_channel_csv(
    file: UploadFile = File(...),
    channel: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Upload and ingest a single channel CSV file.

    - **file**: CSV file (Google Ads, Meta Ads, Microsoft Ads, Shopify, or GA4 export)
    - **channel**: Channel name: google | meta | microsoft | shopify | ga4
    """
    if not file.filename.endswith((".csv", ".CSV")):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_upload_size_mb}MB limit."
        )

    try:
        df = parse_channel_csv(content=content, channel=channel, filename=file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Validate
    result = validator.validate(df, channel=channel)

    # Store to database
    session_id = str(uuid.uuid4())
    records = []
    for _, row in df.iterrows():
        records.append(CampaignRecord(
            upload_session_id=session_id,
            date=str(row.get("date", "")),
            channel=str(row.get("channel", channel)),
            campaign=str(row.get("campaign", "")) if row.get("campaign") else None,
            impressions=float(row.get("impressions", 0) or 0),
            clicks=float(row.get("clicks", 0) or 0),
            spend=float(row.get("spend", 0) or 0),
            conversions=float(row.get("conversions", 0) or 0),
            revenue=float(row.get("revenue", 0) or 0),
            roas=float(row.get("roas", 0) or 0),
            ctr=float(row.get("ctr", 0) or 0),
            cvr=float(row.get("cvr", 0) or 0),
            cpc=float(row.get("cpc", 0) or 0),
        ))

    db.bulk_save_objects(records)
    db.commit()

    # Preview: first 5 rows
    preview = df.head(5).fillna(0).to_dict(orient="records")

    logger.info(f"Ingested {len(records)} rows | channel={channel} | session={session_id}")

    return IngestionResponse(
        session_id=session_id,
        channel=channel,
        rows_ingested=len(records),
        validation=result.to_dict(),
        preview=preview,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


@router.post("/ingest/upload-multi")
async def upload_multiple_channels(
    files: List[UploadFile] = File(...),
    channels: str = Form(...),  # comma-separated: "google,meta,microsoft"
    db: Session = Depends(get_db),
):
    """
    Upload multiple channel CSV files in a single request.

    - **files**: List of CSV files
    - **channels**: Comma-separated channel names matching file order
    """
    channel_list = [c.strip() for c in channels.split(",")]
    if len(files) != len(channel_list):
        raise HTTPException(
            status_code=400,
            detail=f"Number of files ({len(files)}) must match number of channels ({len(channel_list)})."
        )

    file_specs = []
    for f, ch in zip(files, channel_list):
        content = await f.read()
        file_specs.append({"content": content, "channel": ch, "filename": f.filename})

    try:
        df = parse_multiple_channels(file_specs)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    result = validator.validate_multi_channel(df)

    session_id = str(uuid.uuid4())
    records = []
    for _, row in df.iterrows():
        records.append(CampaignRecord(
            upload_session_id=session_id,
            date=str(row.get("date", "")),
            channel=str(row.get("channel", "")),
            campaign=str(row.get("campaign", "")) if row.get("campaign") else None,
            impressions=float(row.get("impressions", 0) or 0),
            clicks=float(row.get("clicks", 0) or 0),
            spend=float(row.get("spend", 0) or 0),
            conversions=float(row.get("conversions", 0) or 0),
            revenue=float(row.get("revenue", 0) or 0),
            roas=float(row.get("roas", 0) or 0),
            ctr=float(row.get("ctr", 0) or 0),
            cvr=float(row.get("cvr", 0) or 0),
            cpc=float(row.get("cpc", 0) or 0),
        ))

    db.bulk_save_objects(records)
    db.commit()

    return {
        "session_id": session_id,
        "total_rows": len(records),
        "channels": list(df["channel"].unique()),
        "validation": result.to_dict(),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@router.post("/ingest/demo")
def load_demo_data(db: Session = Depends(get_db)):
    """
    Load the built-in demo dataset.
    Generates synthetic 120-day multi-channel data and stores it for immediate use.
    """
    import subprocess, sys

    # Generate demo data if needed
    demo_dir = settings.demo_data_dir
    if not os.path.exists(os.path.join(demo_dir, "google_ads_sample.csv")):
        try:
            subprocess.run(
                [sys.executable, "scripts/generate_demo_data.py"],
                check=True, timeout=60
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Demo data generation failed: {e}")

    # Parse and ingest all sample files
    channel_map = {
        "google_ads_sample.csv": "google",
        "meta_ads_sample.csv": "meta",
        "microsoft_ads_sample.csv": "microsoft",
        "shopify_sample.csv": "shopify",
        "ga4_sample.csv": "ga4",
    }

    file_specs = []
    for filename, channel in channel_map.items():
        filepath = os.path.join(demo_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                file_specs.append({"content": f.read(), "channel": channel, "filename": filename})

    if not file_specs:
        raise HTTPException(status_code=500, detail="No demo files found.")

    df = parse_multiple_channels(file_specs)
    session_id = str(uuid.uuid4())

    records = []
    for _, row in df.iterrows():
        records.append(CampaignRecord(
            upload_session_id=session_id,
            date=str(row.get("date", "")),
            channel=str(row.get("channel", "")),
            campaign=str(row.get("campaign", "")) if row.get("campaign") else None,
            impressions=float(row.get("impressions", 0) or 0),
            clicks=float(row.get("clicks", 0) or 0),
            spend=float(row.get("spend", 0) or 0),
            conversions=float(row.get("conversions", 0) or 0),
            revenue=float(row.get("revenue", 0) or 0),
            roas=float(row.get("roas", 0) or 0),
        ))

    db.bulk_save_objects(records)
    db.commit()

    logger.info(f"Demo data loaded: {len(records)} rows | session={session_id}")

    return {
        "session_id": session_id,
        "total_rows": len(records),
        "channels": list(df["channel"].unique()),
        "message": "Demo data loaded successfully. Use this session_id for forecasting.",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@router.get("/ingest/sessions/{session_id}/summary")
def get_session_summary(session_id: str, db: Session = Depends(get_db)):
    """Get a summary of ingested data for a session."""
    records = db.query(CampaignRecord).filter(
        CampaignRecord.upload_session_id == session_id
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail=f"No data found for session {session_id}")

    import pandas as pd
    df = pd.DataFrame([{
        "date": r.date,
        "channel": r.channel,
        "spend": r.spend,
        "revenue": r.revenue,
        "roas": r.roas,
    } for r in records])

    total_spend = float(df["spend"].sum())
    total_revenue = float(df["revenue"].sum())

    return {
        "session_id": session_id,
        "total_rows": len(records),
        "channels": list(df["channel"].unique()),
        "date_from": df["date"].min(),
        "date_to": df["date"].max(),
        "total_spend": round(total_spend, 2),
        "total_revenue": round(total_revenue, 2),
        "blended_roas": round(total_revenue / total_spend, 2) if total_spend > 0 else 0,
        "channel_breakdown": {
            ch: {
                "spend": round(float(df[df["channel"] == ch]["spend"].sum()), 2),
                "revenue": round(float(df[df["channel"] == ch]["revenue"].sum()), 2),
                "roas": round(
                    float(df[df["channel"] == ch]["revenue"].sum()) /
                    max(float(df[df["channel"] == ch]["spend"].sum()), 0.01), 2
                ),
            }
            for ch in df["channel"].unique()
        },
    }
