# Job Application Detector

An AI-powered job application tracking system that automatically detects job-related emails, extracts important application details, and stores them in a centralized dashboard.

## Features

* Gmail inbox integration using Gmail API
* AI-powered email analysis using Google Gemini
* Automatic company and job-role extraction
* Job/Application ID extraction
* Job location extraction
* Application date extraction
* Application status tracking
* Duplicate application detection
* Application status progression tracking
* SQLite database for persistent storage
* FastAPI backend
* Application dashboard

## How It Works

```text
Gmail Inbox
     ↓
Gmail API
     ↓
Email Filtering
     ↓
Gemini AI Analysis
     ↓
Job Information Extraction
     ↓
Duplicate / Status Check
     ↓
SQLite Database
     ↓
Application Dashboard
```

## Tech Stack

* Python
* FastAPI
* Google Gemini API
* Gmail API
* SQLite
* HTML
* CSS
* JavaScript
* Uvicorn

## Extracted Information

For job-related emails, the system can identify:

* Company
* Job Role
* Job ID
* Application Status
* Location
* Application Date

## Application Status

The system supports the following application stages:

* Applied
* Under Review
* Assessment
* Interview
* Selected
* Rejected

## Running the Project

### 1. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 2. Configure Environment Variables

Create a `backend/.env` file and add:

```env
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Start the Backend

```bash
python -m uvicorn backend.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## API Endpoints

| Method | Endpoint             | Purpose                         |
| ------ | -------------------- | ------------------------------- |
| GET    | `/`                  | Check API status                |
| POST   | `/detect`            | Analyze a job application email |
| POST   | `/sync-gmail`        | Sync recent Gmail emails        |
| GET    | `/applications`      | View saved applications         |
| PUT    | `/applications/{id}` | Update an application           |
| DELETE | `/applications/{id}` | Delete an application           |

## Gmail Integration

The project uses the Gmail API to retrieve recent emails from the user's inbox.

Gmail authentication uses OAuth 2.0. The system processes recent emails, filters potential job-related messages, and analyzes relevant emails using Gemini.

## Duplicate Detection

Before saving an application, the system checks whether a matching application already exists.

This prevents the same job application from being stored multiple times.

## Status Tracking

When a new email indicates a later stage of an existing application, the system can update the stored application status instead of creating a duplicate record.

## Future Scope

* Real-time Gmail monitoring
* Email notifications for status changes
* Advanced application analytics
* Resume-to-job matching
* Interview preparation recommendations
* Support for additional email providers
* Mobile application version

## Project Goal

The goal of Job Application Detector is to reduce the manual effort involved in tracking job applications by automatically converting application-related emails into structured and searchable application records.

## Author

Mallika Rajapure
