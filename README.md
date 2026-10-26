<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:172554,35:1D4ED8,70:3B82F6,100:93C5FD&height=240&section=header&text=APPLICATION%20PULSE&fontSize=44&fontColor=FFFFFF&fontAlignY=36&desc=Your%20job%20search%2C%20organized%20in%20one%20place&descAlignY=59&descSize=15" width="100%" alt="Application Pulse — Job Application Detector" />

<h3>Turn application emails into a trackable job-search timeline.</h3>

<p>
  <img src="https://img.shields.io/badge/Python-Backend-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Gmail%20API-Email%20Sync-EA4335?style=for-the-badge&logo=gmail&logoColor=white" alt="Gmail API" />
  <img src="https://img.shields.io/badge/Google%20Gemini-Email%20Analysis-4285F4?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Google Gemini" />
  <img src="https://img.shields.io/badge/SQLite-Local%20Storage-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
</p>

</div>

---

## 💼 What is Job Application Detector?

**Job Application Detector** is a job-search tracking project that helps turn recruitment emails into structured application records. Instead of manually searching your inbox to remember every role and update, the app can fetch recent Gmail messages, analyse potential job-related emails with Google Gemini, and save useful details in a SQLite database.

The project includes a **FastAPI backend** and a lightweight **HTML, CSS, and JavaScript dashboard**.

## ✨ Key features

| Feature | What it does |
|---|---|
| 📬 Gmail sync | Retrieves recent emails through the Gmail API after OAuth authorization |
| 🧠 Email analysis | Uses Gemini to extract structured information from potential application emails |
| 🏢 Company & role extraction | Captures company name and job title when present in the email |
| 🆔 Application details | Extracts a job ID, location, and application date when available |
| 🔁 Duplicate checks | Checks for an existing matching application before adding a new record |
| 📈 Status tracking | Keeps application stages organised as emails indicate progress |
| 🗃️ Persistent records | Stores application data in SQLite |
| ✏️ Record management | Lists, edits, and deletes saved application entries |

## 🪜 Application journey

<div align="center">

`Gmail` → `Gmail API` → `Filter & Analyse` → `Extract Details` → `Check Duplicates / Status` → `SQLite` → `Dashboard`

</div>

1. Authorize access to Gmail using Google's OAuth flow.
2. Fetch a limited batch of recent messages.
3. Analyse candidate job-related messages using Gemini.
4. Extract application fields and compare them with saved records.
5. Save new applications or update an existing record where a match is found.
6. Review and manage the results from the dashboard.

## 🧾 Information tracked

- Company
- Job role
- Job/application ID, when present
- Location, when present
- Application date, when available
- Current application stage

The project recognises stages such as **Applied**, **Under Review**, **Assessment**, **Interview**, **Selected**, and **Rejected**. Actual extraction depends on the information present in the email.

## 🧰 Tech stack

| Layer | Technology |
|---|---|
| Backend API | Python, FastAPI, Uvicorn |
| Email integration | Gmail API, Google OAuth 2.0 |
| Email analysis | Google Gemini API |
| Storage | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Dashboard charts | Chart.js |

## 📁 Repository structure

```text
job-application-detector/
├── backend/
│   ├── app/
│   │   └── services/
│   │       ├── gemini_service.py
│   │       └── gmail_service.py
│   ├── database.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
├── .gitignore
└── README.md
```

## ⚙️ Run locally (Windows / PowerShell)

### Prerequisites

- Python installed
- A Google Gemini API key
- A Google Cloud project with the Gmail API enabled
- OAuth client credentials for a desktop application

### 1. Clone the repository

```powershell
git clone https://github.com/mallikarajapure-collab/job-application-detector.git
cd job-application-detector
```

### 2. Create a virtual environment and install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

If PowerShell blocks activation, use the virtual environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

### 3. Configure the Gemini API key

Create a file named `backend/.env` and add your own key:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Keep your real API key private. Never commit `.env`, OAuth credentials, or generated token files to GitHub.

### 4. Configure Gmail OAuth

1. Open the Google Cloud Console and select or create a project.
2. Enable the **Gmail API** for that project.
3. Configure the OAuth consent screen for your testing setup.
4. Create an OAuth client ID for a **Desktop app** and download its JSON file.
5. Save the downloaded file as `credentials.json` in the **repository root** (next to this README).
6. If your app is in OAuth testing mode, add your Google account as a test user when required.

The first Gmail sync opens Google's authorization flow. After approval, the application creates `token.json` locally for subsequent sessions. These files are sensitive: do not upload or share them.

### 5. Start the backend

From the **repository root**, run:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000`. Keep this terminal running.

### 6. Open the dashboard

Open `frontend/index.html` in your browser. The dashboard JavaScript calls the local API, so the backend must be running.

> If the dashboard does not connect, confirm the API is running and check the API base URL configured in `frontend/script.js`.

## 🔌 API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Check API status |
| `POST` | `/detect` | Analyse a supplied email subject and body |
| `POST` | `/sync-gmail` | Fetch and process recent Gmail messages |
| `GET` | `/applications` | List saved application records |
| `PUT` | `/applications/{application_id}` | Edit a saved application |
| `DELETE` | `/applications/{application_id}` | Delete an application record |

Interactive API documentation is available at `http://127.0.0.1:8000/docs` while the backend is running.

## 🔐 Privacy & safe use

- Gmail access uses the `gmail.readonly` OAuth scope configured in the project.
- Email analysis sends relevant email content to the Gemini API; review Google's applicable privacy and data-handling terms before using personal inbox data.
- Keep `backend/.env`, `credentials.json`, and `token.json` private.
- Use a test inbox or non-sensitive sample emails while learning.
- This is a personal educational project. It is not a replacement for checking important recruiter emails directly.

## ⚠️ Current scope & limitations

- Extraction quality depends on email wording and the model's response; fields may be missing or incorrect.
- Duplicate matching is based on the fields and rules implemented in the backend, so it may not catch every variation of the same role.
- Gmail sync processes a limited set of recent messages rather than acting as a continuous inbox monitor.
- The dashboard and API are designed for local use; production deployment would require additional authentication, access controls, error monitoring, and security review.

## 🌱 Future improvements

- Scheduled email synchronisation and notifications
- Application timeline and outcome analytics
- Resume-to-role matching
- Follow-up reminders
- Additional email-provider integrations
- Responsive mobile experience

---

<div align="center">

**Built to make the job search easier to track, one email at a time.**

<sub>Job Application Detector · Organise applications. Spot progress. Stay on top of your search.</sub>

</div>
