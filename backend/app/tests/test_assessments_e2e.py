import io
import zipfile

def test_assessment_flow_and_reporting(client):
    # 1. Create assessment via manual architecture description
    payload = {
        "project_name": "Healthcare RAG Agent",
        "description": "Clinical advisory agent with local Llama model and ChromaDB",
        "architecture_text": "System connects to ChromaDB vector store and calls Llama-3 model. Tools execute python queries.",
        "target_frameworks": ["OWASP-GENAI", "NIST-AI-RMF", "EU-AI-ACT"]
    }
    create_res = client.post("/api/v1/assessments", json=payload)
    assert create_res.status_code == 200
    data = create_res.json()
    assert "id" in data
    assessment_id = data["id"]
    assert data["status"] == "COMPLETED"
    assert "overall_risk_score" in data
    assert "compliance_score" in data

    # 2. Upload file assessment
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        code_content = '''
import os
def query_bot(user_q):
    prompt = f"Answer this: {user_q}"
    out = "system result"
    eval(out)
'''
        zf.writestr("bot.py", code_content)
    
    upload_res = client.post(
        "/api/v1/assessments/upload",
        data={
            "project_name": "Vulnerable Bot Upload",
            "description": "Upload test archive",
            "target_frameworks": '["OWASP-GENAI", "NIST-AI-RMF"]'
        },
        files={"file": ("vulnerable_bot.zip", zip_buffer.getvalue(), "application/zip")}
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    vuln_assessment_id = upload_data["id"]
    assert upload_data["status"] == "COMPLETED"
    assert upload_data["findings_count"] >= 2
    assert upload_data["risk_level"] == "CRITICAL"

    # 3. Retrieve assessment details
    get_res = client.get(f"/api/v1/assessments/{vuln_assessment_id}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert len(detail["findings"]) >= 2
    assert len(detail["control_mappings"]) > 0

    # 4. Retrieve structured JSON report
    report_res = client.get(f"/api/v1/assessments/{vuln_assessment_id}/report")
    assert report_res.status_code == 200
    rep = report_res.json()
    assert "report_metadata" in rep
    assert "findings" in rep
    assert "compliance_matrix" in rep
    assert "remediation_roadmap" in rep
    assert "disclaimer" in rep

    # 5. Retrieve PDF report
    pdf_res = client.get(f"/api/v1/assessments/{vuln_assessment_id}/report.pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000

    # 6. Retrieve findings with filters
    findings_res = client.get(f"/api/v1/findings?assessment_id={vuln_assessment_id}&severity=CRITICAL")
    assert findings_res.status_code == 200
    crit_findings = findings_res.json()
    assert len(crit_findings) >= 1
    assert crit_findings[0]["severity"] == "CRITICAL"
