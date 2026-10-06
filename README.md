# 🏄 SwellMind — Automated Cape Town Surf Assistant

**Developer:** Benjy  
**Project Category:** Duke of Edinburgh Bronze Skill (Computing / Software Development)  
**Target Area:** Cape Town Marine Forecasts (Muizenberg & Llandudno)  
**Tech Stack:** Python 3.10, Open-Meteo REST API, GitHub Actions (CI/CD), `ntfy` Webhooks, iOS Shortcuts  

---

## 📌 Project Overview
SwellMind is an automated, cloud-hosted Python assistant designed to solve a practical daily problem: deciding whether to wake up at 05:30 AM for a pre-school surf in Cape Town. 

The application fetches real-time marine weather forecasts, evaluates surf conditions using custom math thresholds for wave height, period, wind speed, and offshore wind angles, logs reports locally, and executes in the cloud on a schedule to trigger an automated iPhone alarm via push webhooks.

---

## ⚙️ System Architecture

```text
[ Open-Meteo Marine API ]
           │
           ▼ (JSON Forecast Data)
[ GitHub Actions Cloud Runner ]  <── Runs on Cron Schedule
           │
           ▼ (Python Decision Tree & Math Filters)
[ ntfy.sh Webhook Service ]
           │
           ▼ (Push Notification)
[ iOS Shortcuts Automation ] ──> [ Flips 5:30 AM iPhone Alarm ON ]
