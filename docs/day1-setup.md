02 September 2025  

- Set up the **development environment** for ChakraOS.  
- Build the **first API service** (health endpoint).  
- Deploy to **Google Cloud Run**.  
- Initialize **Git + GitHub repo** for version control.  
## 🔨 Steps Done  

### 1. Installed Dev Toolkit
- **Homebrew** → package manager for Mac (installed tools easily).  
- **Python 3.11** → language environment for ChakraOS backend.  
- **Virtual Environment (`.venv`)** → isolated project dependencies.  
- **FastAPI + Uvicorn** → framework + server to build & serve APIs.  

---

### 2. First API Created
- Wrote `app/main.py` with a **health check endpoint**:  
  ```python
  from fastapi import FastAPI
  
  app = FastAPI()
  
  @app.get("/health")
  def health():
      return {"ok": True}
	•	Tested locally → opened 127.0.0.1:8000/health → response {"ok": true} ✅

⸻

3. Cloud Setup
	•	Installed Google Cloud CLI (gcloud).
	•	Created GCP project: chakraos-dev.
	•	Enabled billing (free trial).
	•	Enabled APIs: Cloud Run, Artifact Registry, Cloud Build.
	•	Fixed port issue with a Procfile.

⸻

4. Deployment
	•	Ran gcloud run deploy chakraos-api --source . --allow-unauthenticated.
	•	Service successfully deployed → live public URL returned.
	•	Verified endpoint → saw {"ok": true} on Cloud Run ✅

⸻

5. Git + GitHub
	•	Installed Git.
	•	Installed Docker (future-proof, not yet used today).
	•	Initialized Git repo in chakraos/.
	•	Added .gitignore (excluded .venv/, caches, etc.).
	•	Made first commit ("Initial commit: FastAPI hello world").
	•	Installed GitHub CLI (gh), logged in.
	•	Created repo chakraos on GitHub.
	•	Connected local → remote.
	•	Pushed code successfully → repo live at:
👉 https://github.com/chaitanyabhimrajka/chakraos

⸻

📦 Result
	•	ChakraOS API skeleton is live on Google Cloud (global access).
	•	Repo initialized & pushed to GitHub (version-controlled, ready for collaboration).
	•	Local dev env fully set up (Python, FastAPI, Git, Docker, gcloud).

⸻

🏆 Achievement
	•	Went from zero setup → live API in one day.
	•	Now have a deployable, scalable, multi-tenant-ready foundation.
	•	ChakraOS isn’t a dream anymore → it’s a working POC hosted on GCP.

⸻

🔮 Next Steps (Tomorrow)
	1.	Add /inquiries module → capture + list customer inquiries.
	2.	Persist data in Cloud SQL (Postgres) instead of in-memory.
	3.	Document structure of Phase 1 (AP/AR, quotations, orders).
	4.	Start tuning ChakraOS around Amit Labs → our first client + case study.
```bash

```bash
exit
