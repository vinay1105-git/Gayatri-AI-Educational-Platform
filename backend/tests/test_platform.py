def _login(client, email: str, password: str) -> dict:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "healthy"
    assert body["database_connected"] is True


def test_authentication_and_rbac_enforcement(client):
    # Unauthenticated request rejected
    unauth = client.get("/api/v1/students/me/dashboard")
    assert unauth.status_code == 401

    # Invalid credentials rejected
    bad = client.post("/api/v1/auth/login", json={"email": "ananya.sharma@gayatri-ai.edu", "password": "wrong-password"})
    assert bad.status_code == 401

    # Student login succeeds
    student_auth = _login(client, "ananya.sharma@gayatri-ai.edu", "Student@2026")
    assert student_auth["user"]["role"] == "student"
    student_headers = {"Authorization": f"Bearer {student_auth['access_token']}"}

    # Student blocked from admin endpoints
    forbidden = client.get("/api/v1/analytics/cohort", headers=student_headers)
    assert forbidden.status_code == 403
    forbidden_students = client.get("/api/v1/admin/students", headers=student_headers)
    assert forbidden_students.status_code == 403

    # Admin login succeeds and accesses admin analytics
    admin_auth = _login(client, "admin@gayatri-ai.edu", "Admin@Gayatri2026")
    assert admin_auth["user"]["role"] == "admin"
    admin_headers = {"Authorization": f"Bearer {admin_auth['access_token']}"}
    cohort_res = client.get("/api/v1/analytics/cohort", headers=admin_headers)
    assert cohort_res.status_code == 200
    assert cohort_res.json()["kpis"]["total_students"] >= 100


def test_student_dashboard_recommendations_and_checkin(client):
    auth = _login(client, "ananya.sharma@gayatri-ai.edu", "Student@2026")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    dash = client.get("/api/v1/students/me/dashboard", headers=headers)
    assert dash.status_code == 200
    payload = dash.json()
    assert payload["profile"]["student_code"].startswith("GAI-")
    assert 0 <= payload["ml_intelligence"]["risk_score"] <= 100
    assert len(payload["ml_intelligence"]["drivers"]) >= 3
    assert len(payload["trajectory"]) >= 10
    assert len(payload["recommendations"]) >= 3

    # Log study telemetry check-in
    checkin = client.post(
        "/api/v1/students/me/telemetry",
        headers=headers,
        json={"study_hours": 2.5, "sessions_count": 2, "assignments_completed": 1},
    )
    assert checkin.status_code == 200
    assert "updated_prediction" in checkin.json()


def test_course_resource_completion_updates_mastery(client):
    auth = _login(client, "ananya.sharma@gayatri-ai.edu", "Student@2026")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    courses_res = client.get("/api/v1/courses", headers=headers)
    assert courses_res.status_code == 200
    courses = courses_res.json()["courses"]
    assert len(courses) == 6

    detail_res = client.get(f"/api/v1/courses/{courses[0]['id']}", headers=headers)
    assert detail_res.status_code == 200
    resources = detail_res.json()["resources"]
    assert len(resources) >= 4

    interact_res = client.post(
        f"/api/v1/courses/resources/{resources[0]['id']}/interact",
        headers=headers,
        json={"status": "completed", "rating": 5},
    )
    assert interact_res.status_code == 200
    assert interact_res.json()["status"] == "completed"


def test_assessment_submission_and_psychometrics(client):
    student_auth = _login(client, "ananya.sharma@gayatri-ai.edu", "Student@2026")
    s_headers = {"Authorization": f"Bearer {student_auth['access_token']}"}

    list_res = client.get("/api/v1/assessments", headers=s_headers)
    assert list_res.status_code == 200
    assessments = list_res.json()["assessments"]
    assert len(assessments) >= 6

    target = assessments[-1]
    detail_res = client.get(f"/api/v1/assessments/{target['id']}", headers=s_headers)
    assert detail_res.status_code == 200
    questions = detail_res.json()["questions"]
    # Ensure answers are hidden from students
    assert "correct_index" not in questions[0]

    answers = {str(q["id"]): 0 for q in questions}
    submit_res = client.post(
        f"/api/v1/assessments/{target['id']}/submit",
        headers=s_headers,
        json={"answers": answers, "time_spent_seconds": 240},
    )
    assert submit_res.status_code == 200
    sub_body = submit_res.json()
    assert 0 <= sub_body["score_pct"] <= 100
    assert len(sub_body["items"]) == len(questions)

    # Admin psychometrics check
    admin_auth = _login(client, "admin@gayatri-ai.edu", "Admin@Gayatri2026")
    a_headers = {"Authorization": f"Bearer {admin_auth['access_token']}"}
    psy_res = client.get(f"/api/v1/assessments/{target['id']}/psychometrics", headers=a_headers)
    assert psy_res.status_code == 200
    psy = psy_res.json()
    assert psy["submissions_count"] >= 10
    assert len(psy["items"]) == len(questions)


def test_academic_assistant_rag_and_telemetry_grounding(client):
    student_auth = _login(client, "ananya.sharma@gayatri-ai.edu", "Student@2026")
    s_headers = {"Authorization": f"Bearer {student_auth['access_token']}"}

    concept_q = client.post(
        "/api/v1/assistant/query",
        headers=s_headers,
        json={"query": "Explain backpropagation and gradient flow in deep neural networks", "session_id": "test-s1"},
    )
    assert concept_q.status_code == 200
    c_msg = concept_q.json()["message"]
    assert "Backpropagation" in c_msg["content"]
    assert len(c_msg["citations"]) >= 1

    plan_q = client.post(
        "/api/v1/assistant/query",
        headers=s_headers,
        json={"query": "Build me a personalized study plan for this week", "session_id": "test-s1"},
    )
    assert plan_q.status_code == 200
    assert "Study Plan" in plan_q.json()["message"]["content"]

    hist = client.get("/api/v1/assistant/history?session_id=test-s1", headers=s_headers)
    assert hist.status_code == 200
    assert len(hist.json()["messages"]) == 4


def test_ml_metrics_retrain_and_interventions(client):
    admin_auth = _login(client, "admin@gayatri-ai.edu", "Admin@Gayatri2026")
    a_headers = {"Authorization": f"Bearer {admin_auth['access_token']}"}

    metrics_res = client.get("/api/v1/ml/metrics", headers=a_headers)
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["cohort_size"] >= 100
    assert 0.5 <= metrics["risk_model"]["classifier_metrics"]["roc_auc"] <= 1.0
    assert -1.0 <= metrics["clustering_model"]["silhouette_score"] <= 1.0

    # Create intervention
    students_res = client.get("/api/v1/admin/students?risk_level=high&limit=5", headers=a_headers)
    assert students_res.status_code == 200
    high_students = students_res.json()["students"]
    assert len(high_students) >= 1

    iv_create = client.post(
        "/api/v1/admin/interventions",
        headers=a_headers,
        json={
            "student_id": high_students[0]["id"],
            "intervention_type": "Academic Coaching",
            "priority": "high",
            "notes": "Automated integration test coaching outreach.",
        },
    )
    assert iv_create.status_code == 201
    iv_id = iv_create.json()["id"]

    iv_patch = client.patch(
        f"/api/v1/admin/interventions/{iv_id}",
        headers=a_headers,
        json={"status": "resolved"},
    )
    assert iv_patch.status_code == 200
    assert iv_patch.json()["status"] == "resolved"


def test_pdf_and_csv_report_exports(client):
    student_auth = _login(client, "ananya.sharma@gayatri-ai.edu", "Student@2026")
    s_headers = {"Authorization": f"Bearer {student_auth['access_token']}"}
    sid = student_auth["user"]["student_profile_id"]

    pdf_res = client.get(f"/api/v1/reports/student/{sid}/pdf", headers=s_headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content[:4] == b"%PDF"

    csv_res = client.get(f"/api/v1/reports/student/{sid}/csv", headers=s_headers)
    assert csv_res.status_code == 200
    assert "concept_name" in csv_res.text

    admin_auth = _login(client, "admin@gayatri-ai.edu", "Admin@Gayatri2026")
    a_headers = {"Authorization": f"Bearer {admin_auth['access_token']}"}

    cohort_pdf = client.get("/api/v1/reports/cohort/pdf", headers=a_headers)
    assert cohort_pdf.status_code == 200
    assert cohort_pdf.content[:4] == b"%PDF"

    cohort_csv = client.get("/api/v1/reports/cohort/csv", headers=a_headers)
    assert cohort_csv.status_code == 200
    assert "student_code" in cohort_csv.text


def test_student_registration_flow(client):
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Kiran Deshpande",
            "email": "kiran.deshpande@gayatri-ai.edu",
            "password": "StrongPass@2026",
            "cohort": "Fall 2026 - AI Engineering",
            "program_track": "Applied Artificial Intelligence",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    dash = client.get("/api/v1/students/me/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert dash.status_code == 200
    assert dash.json()["profile"]["full_name"] == "Kiran Deshpande"
