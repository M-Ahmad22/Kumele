from fastapi import APIRouter, HTTPException

from app.services.ads.audience_matcher import get_audience_match
from app.services.ads.ctr_predictor import predict_ad_performance

router = APIRouter(prefix="/ads", tags=["Advertising"])


@router.get("/audience-match")
def api_audience_match(ad_id: int):
    res = get_audience_match(ad_id)
    if res is None:
        raise HTTPException(404, "Ad not found")
    return {"ad_id": ad_id, "segments": res}


@router.get("/performance-predict")
def api_predict(ad_id: int):
    res = predict_ad_performance(ad_id)
    if res is None:
        raise HTTPException(404, "Ad not found")
    return res
