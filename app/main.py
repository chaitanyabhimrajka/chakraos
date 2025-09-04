# app/main.py
from fastapi import FastAPI
from app.db import engine
from app.models import Base, Company
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.routers.inquiries import router as inquiries_router
from app.routers.quotations import router as quotations_router

app = FastAPI(title="ChakraOS API")

@app.on_event("startup")
async def startup():
    # Dev convenience: create tables if not present
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed a tenant if not present (ALAB = Amit Labs)
    async with AsyncSession(engine) as session:
        res = await session.execute(select(Company).where(Company.code == "ALAB"))
        if not res.scalar_one_or_none():
            session.add(Company(code="ALAB", name="Amit Labs", base_currency="INR"))
            await session.commit()

@app.get("/health")
def health():
    return {"ok": True}


app.include_router(inquiries_router)
app.include_router(quotations_router)