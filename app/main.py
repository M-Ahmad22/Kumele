from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app import config
from app.db.database import get_local_db  
from app.data.loader import fetch_all_users
from app.api import moderation as moderation_router  
from app.api import rewards as rewards_router 
from app.api import match, recommendations, host_ratings
from app.api.predict_routes import router as PredictRouter
from app.api.feedback_routes import router as feedback_router
from app.api.engagement_routes import router as engagement_router
from app.api.ads_routes import router as ads_router
from app.api.nlp_routes import router as nlp_router
from app.api.pricing_routes import router as pricing_router
from app.api.discount_routes import router as discount_router
from app.api.chatbot_router import router as chatbot_router

app = FastAPI(title="Kumele ML Service APIs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
app.include_router(moderation_router.router)
app.include_router(rewards_router.router) 
app.include_router(recommendations.router)
app.include_router(match.router)
app.include_router(host_ratings.router)
app.include_router(PredictRouter, tags=["Prediction"])
app.include_router(feedback_router)
app.include_router(engagement_router)
app.include_router(ads_router)
app.include_router(nlp_router)
app.include_router(pricing_router)
app.include_router(discount_router)
app.include_router(chatbot_router)



@app.get("/Users", tags=["Users"])
def get_users(db=Depends(get_local_db)):
    users = fetch_all_users(db)
    return [
        {
            "user_id": u.user_id,
            "name": u.full_name,
            "city": u.city,
            "email": u.email,
            "age": u.age,
            "gender": u.gender
        }
        for u in users
    ]
@app.get("/")
def root():
    return {
        "service": "kumele-ml",
    }

