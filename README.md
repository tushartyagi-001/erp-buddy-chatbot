# ERP Buddy Chatbot

College ERP ke liye LangChain chatbot — read-only, role/branch scoped.

## Setup

```bash
cd ErpChatBot_ERP_Buddy
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# .env me DB + GEMINI_API_KEY + JWT_SECRET set karo
uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

## ERP integration

1. `ChatBridgeController` ERP session se JWT token deta hai
2. Dashboard par robot icon → chat popup
3. Widget `http://127.0.0.1:8010/api/chat` call karta hai

## Tools (10 total)

**Student (Step 1)**
- `search_students_tool` — USP_SearchAdmissionStudents
- `select_student_tool` — disambiguation
- `get_student_profile_tool` — USP_STUDENTDETAILS
- `get_student_fee_summary_tool` — fee (permission check pehle)

**Dashboard (Step 2)**
- `get_dashboard_summary_tool` — USP_NewDashboardSummary
- `get_fee_due_alert_tool` — USP_GetDashboardFeeDueAlert

**Attendance**
- `get_student_attendance_tool` — USP_GetStudentAttendanceStatsForPopup

**Exam**
- `get_student_exam_results_tool` — student exam list
- `get_exam_result_detail_tool` — USP_GetNewExamResult

**Enquiry**
- `search_enquiries_tool` — usp_Datalist (mobile/email masked)

## Permission

- `Usp_ManageActionRights` — menu access
- Super admin / head branch bypass
- Fee / attendance / exam / enquiry — alag menu permission
- Bina access ke user-friendly message, data nahi

## Deploy (SmarterASP)

```powershell
.\deploy\deploy.ps1
.\deploy\deploy.ps1 -SkipPackages   # upload only, after first build
```

## Chat limit reset API

```http
POST /api/chat-limit/reset
Authorization: Bearer <JWT>
Content-Type: application/json

{"scope": "user"}
```

Optional dev header: `X-Chat-Limit-Key` (set `CHAT_LIMIT_ADMIN_KEY` in `.env`).
