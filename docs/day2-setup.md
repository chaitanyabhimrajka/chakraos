# ChakraOS – Day 2 Setup Log 🚀

**Date:** 3rd September 2025  
**Milestone:** First live deployment of ChakraOS API (inquiries + parser) on **Google Cloud Run** with Postgres backend (Cloud SQL).  

---

## ✅ Achievements  

1. **Local API → Cloud Run**  
   - FastAPI + Uvicorn app containerized via Dockerfile.  
   - Deployment succeeded to Cloud Run (`chakraos-api`).  
   - Public URL: [https://chakraos-api-656857229129.asia-south1.run.app](https://chakraos-api-656857229129.asia-south1.run.app)  

2. **Database Integration**  
   - Created Cloud SQL (Postgres) instance `chakraos-sql`.  
   - DB: `chakraos_db`  
   - User: `chakraos_app`  
   - Secret `DB_PASS` configured in Secret Manager and mounted into Cloud Run.  
   - Cloud SQL Proxy configured for local testing and migrations.  

3. **Inquiries Module Live**  
   - Endpoints:  
     - `GET /health` → returns API health.  
     - `POST /inquiries/ingest` → accepts inquiries in JSON, parses, saves to DB.  
     - `GET /inquiries` → retrieves all stored inquiries.  

4. **Parser Service**  
   - Added lightweight regex parser (`services/parser/factory.py`) for proof-of-concept extraction.  
   - Example extracted JSON:  
     ```json
     {
       "qty": "500",
       "unit": "L",
       "product_snippet": "acetone technical grade delivered Jaipur",
       "detected": true
     }
     ```  
   - Extraction persisted in DB alongside raw inquiry.  

5. **End-to-End Test (Deployed API)**  
   - `POST /inquiries/ingest` with payload:  
     ```json
     {
       "company_code": "ALAB",
       "source": "email",
       "raw_body": "Hi team, please quote 500 L benzene delivered Jaipur by Friday. Need MSDS and best price.",
       "from_email": "buyer@amitlabs.com"
     }
     ```  
   - Response → inquiry created with `status=parsed`.  
   - `GET /inquiries` returns stored inquiries (though extraction currently basic).  

---

## 🔧 Debugs & Fixes  

- Fixed **`uvicorn` not found** by installing in venv.  
- Installed `pydantic[email]` to resolve `email-validator` dependency.  
- Resolved **Cloud Run build failure** by:  
  - Correcting `requirements.txt` formatting.  
  - Ensuring Dockerfile used correct `CMD`.  
- Fixed **Cloud SQL auth error** by binding service account to `cloudsql.client`.  
- Debugged Cloud Run logs → identified Postgres connection issues until secrets + service account were configured.  
- Fixed JSON error (422 Unprocessable Entity) by correcting request payload.  

---

## 📌 Current Limitations  

- Parser only extracts **qty + unit + product snippet** via regex → misses full product / city / deadline.  
- `extraction_json` sometimes returns `null` if parser fails.  
- No authentication layer yet (public endpoints).  
- Cloud Run cold starts add latency (~2–3 sec on first request).  

---

## 🎯 Next Steps (Day 3 Plan)  

1. **Quotations Module (Phase 1)**  
   - Create `/quotations` endpoint.  
   - Model: `quotation_id`, `inquiry_id`, `status` (`draft/sent/approved`), `price`, `currency`, `delivery_date`.  
   - Link inquiries → quotations.  

2. **Better Parser / Vertex AI**  
   - Replace regex parser with Vertex AI Text Model.  
   - Structured extraction:  
     - Product name  
     - Quantity + Unit  
     - Delivery city  
     - Delivery deadline  

3. **Docs & CI/CD**  
   - Write `day3-setup.md` after tomorrow’s progress.  
   - Add GitHub Actions for auto-deploy → Cloud Run.  

---

**✨ Summary:**  
In just 2 days, ChakraOS went from *zero setup → a production-ready API* live on Cloud Run, connected to a managed Postgres database, serving Amit Labs as the **first ERP-like proof of concept.**  
