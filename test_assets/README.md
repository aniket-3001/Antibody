# Test assets

Realistic scam samples for manually exercising multimodal intake (`/report/extract`,
`/report/upload`) — screenshots, call-recording audio, and PDF/SMS text, each modeled
on a real scam pattern. Not used by the automated test suite (which uses small
synthetic fixtures instead, see `tests/unit/test_loaders.py`); these are for hands-on
testing of OCR/transcription/PDF-reading and the upload preview UI.

| File | Simulates |
|---|---|
| `Amazon-scam-test.png`, `Netflix-scam-test.png` | Phishing SMS/email screenshot (OCR) |
| `USA-customs-test.mp3.mpeg`, `Visa-scam-test.mp3.mpeg` | Scam-call audio recording (transcription) |
| `geek_squad_invoice.pdf`, `paypal_suspension.pdf` | Scam PDF attachment (PDF text extraction) |
| `bank_kyc_sms.txt`, `irs_warrant_sms.txt` | Plain-text SMS scam |
