# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [ ] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [ ] Backup cũng phải ở trong lãnh thổ VN
- [ ] Log việc transfer data ra ngoài nếu có

## B. Explicit Consent
- [ ] Thu thập consent trước khi dùng data cho AI training
- [ ] Có mechanism để user rút consent (Right to Erasure)
- [ ] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [ ] Có incident response plan
- [ ] Alert tự động khi phát hiện breach
- [ ] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [ ] Đã bổ nhiệm Data Protection Officer
- [ ] DPO có thể liên hệ tại: ___

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | AES-256 at rest, TLS 1.3 in transit | ✅ Done | Infra Team |
| Audit logging | CloudTrail + API access logs | ⬜ Todo | Platform Team |
| Breach detection | Anomaly monitoring (Prometheus) | ⬜ Todo | Security Team |

## F. Technical Solutions cho các items còn Todo

### Audit Logging
**Solution:** Implement structured audit log middleware trong FastAPI:
- Mỗi API request ghi log: `{timestamp, user, role, resource, action, result, ip}`
- Lưu vào file log rotated hàng ngày + ship lên centralized log (ELK/Loki)
- Retention: 90 ngày theo NĐ13
- Implementation: FastAPI middleware + Python `logging` + `python-json-logger`

```python
@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    response = await call_next(request)
    logger.info({
        "timestamp": datetime.utcnow().isoformat(),
        "path": request.url.path,
        "method": request.method,
        "status": response.status_code,
        "user": request.headers.get("Authorization", "anonymous"),
    })
    return response
```

### Breach Detection
**Solution:** Prometheus + Grafana + AlertManager:
- Metric: `api_unauthorized_requests_total` — đếm số 401/403 responses
- Alert rule: nếu >50 lần 403 trong 5 phút → trigger PagerDuty/email
- Metric: `api_data_export_bytes_total` — phát hiện data exfiltration
- Anomaly detection: Grafana Loki + LogQL để phát hiện pattern bất thường
- SIEM integration: ship logs vào Wazuh (open-source SIEM)

```yaml
# prometheus alert rule
- alert: HighUnauthorizedRate
  expr: rate(api_unauthorized_requests_total[5m]) > 10
  for: 2m
  annotations:
    summary: "Possible breach attempt detected"
```
