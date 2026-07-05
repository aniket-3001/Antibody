from __future__ import annotations

FAMILIES: dict = {
    "bank_kyc_phishing": {
        "summary": "A collection of bank_kyc_phishing scams targeting victims via sms, email, whatsapp.",
        "tactics": [
            "urgency_pressure",
            "impersonation",
            "link_obfuscation"
        ],
        "lures": [
            "account_suspension",
            "kyc_expiry"
        ],
        "channels": [
            "sms",
            "email",
            "whatsapp"
        ],
        "guidance": {
            "do_now": [
                "Do not click any links or share OTPs.",
                "Block and report the sender."
            ],
            "report_to": [
                "Report to local cyber crime authorities.",
                "Report to the impersonated platform."
            ],
            "recovery": [
                "If money was lost, contact your bank immediately.",
                "Change passwords and enable 2FA."
            ]
        },
        "indicators": [
            [
                "fake-bank_kyc_phishing.example.com",
                "url_domain"
            ]
        ],
        "reports": [
            "Your bank account will be suspended today. Verify KYC as soon as possible at https://verify-account.example and confirm your OTP.",
            "We detected unusual activity. To prevent restriction, complete identity verification within 24 hours: https://secure-check.example",
            "Dear customer, aapka KYC expire ho gaya hai. Account block hone se bachane ke liye https://secure-check.example par verify karein.",
            "We detected unusual activity. To prevent restriction, complete identity verification within 12 hours: https://secure-check.example",
            "Dear customer, aapka KYC expire ho gaya hai. Account block hone se bachane ke liye https://secure-check.example par verify karein.",
            "Your bank account will be suspended today. Verify KYC as soon as possible at https://parcel-update.example and confirm your OTP.",
            "Dear customer, aapka KYC expire ho gaya hai. Account block hone se bachane ke liye https://parcel-update.example par verify karein.",
            "Your bank account will be suspended today. Verify KYC as soon as possible at https://parcel-update.example and confirm your OTP.",
            "We detected unusual activity. To prevent restriction, complete identity verification within 2 hours: https://parcel-update.example",
            "Dear customer, aapka KYC expire ho gaya hai. Account block hone se bachane ke liye https://secure-check.example par verify karein."
        ],
        "emerging": True
    },
    "loan_scam": {
        "summary": "A collection of loan_scam scams targeting victims via whatsapp, sms, email.",
        "tactics": [
            "advance_fee",
            "urgency_pressure",
            "fake_approval"
        ],
        "lures": [
            "pre_approved_loan",
            "low_interest_rate"
        ],
        "channels": [
            "whatsapp",
            "sms",
            "email"
        ],
        "guidance": {
            "do_now": [
                "Do not click any links or share OTPs.",
                "Block and report the sender."
            ],
            "report_to": [
                "Report to local cyber crime authorities.",
                "Report to the impersonated platform."
            ],
            "recovery": [
                "If money was lost, contact your bank immediately.",
                "Change passwords and enable 2FA."
            ]
        },
        "indicators": [
            [
                "fake-loan_scam.example.com",
                "url_domain"
            ]
        ],
        "reports": [
            "Funds are ready. A refundable processing deposit of \u20b9299 is required within 12 hours.",
            "Funds are ready. A refundable processing deposit of \u20b9499 is required within 4 hours.",
            "CIBIL check ke bina loan approved. Disbursal se pehle \u20b9999 insurance fee pay karein.",
            "Funds are ready. A refundable processing deposit of \u20b9299 is required within 12 hours.",
            "CIBIL check ke bina loan approved. Disbursal se pehle \u20b9999 insurance fee pay karein.",
            "CIBIL check ke bina loan approved. Disbursal se pehle \u20b9999 insurance fee pay karein.",
            "Your \u20b950,000 instant loan is approved with no credit check. Pay \u20b999 file charge to release funds.",
            "Your \u20b92,500 instant loan is approved with no credit check. Pay \u20b92,500 file charge to release funds.",
            "Funds are ready. A refundable processing deposit of \u20b999 is required within 24 hours.",
            "CIBIL check ke bina loan approved. Disbursal se pehle \u20b9499 insurance fee pay karein."
        ],
        "emerging": True
    },
    "tech_support": {
        "summary": "A collection of tech_support scams targeting victims via sms, email, whatsapp.",
        "tactics": [
            "remote_access",
            "fear",
            "brand_impersonation"
        ],
        "lures": [
            "virus_alert",
            "subscription_renewal"
        ],
        "channels": [
            "sms",
            "email",
            "whatsapp"
        ],
        "guidance": {
            "do_now": [
                "Do not click any links or share OTPs.",
                "Block and report the sender."
            ],
            "report_to": [
                "Report to local cyber crime authorities.",
                "Report to the impersonated platform."
            ],
            "recovery": [
                "If money was lost, contact your bank immediately.",
                "Change passwords and enable 2FA."
            ]
        },
        "indicators": [
            [
                "fake-tech_support.example.com",
                "url_domain"
            ]
        ],
        "reports": [
            "Your system license expired. Immediate remote access is required to prevent permanent data loss.",
            "Your system license expired. Immediate remote access is required to prevent permanent data loss.",
            "Your system license expired. Immediate remote access is required to prevent permanent data loss.",
            "Computer hack ho gaya hai. Technician ko remote access do aur \u20b9999 security renewal pay karo.",
            "Computer hack ho gaya hai. Technician ko remote access do aur \u20b9999 security renewal pay karo.",
            "Your device is infected and banking data is at risk. Call +91 11111 11111 promptly and install remote support software.",
            "Your system license expired. Immediate remote access is required to prevent permanent data loss.",
            "Your device is infected and banking data is at risk. Call +91 00000 00000 immediately and install remote support software.",
            "Computer hack ho gaya hai. Technician ko remote access do aur \u20b999 security renewal pay karo.",
            "Your system license expired. Immediate remote access is required to prevent permanent data loss."
        ],
        "emerging": True
    },
    "impersonation": {
        "summary": "A collection of impersonation scams targeting victims via sms, email, whatsapp.",
        "tactics": [
            "authority",
            "trust_abuse",
            "urgency_pressure"
        ],
        "lures": [
            "family_emergency",
            "arrest_warrant"
        ],
        "channels": [
            "sms",
            "email",
            "whatsapp"
        ],
        "guidance": {
            "do_now": [
                "Do not click any links or share OTPs.",
                "Block and report the sender."
            ],
            "report_to": [
                "Report to local cyber crime authorities.",
                "Report to the impersonated platform."
            ],
            "recovery": [
                "If money was lost, contact your bank immediately.",
                "Change passwords and enable 2FA."
            ]
        },
        "indicators": [
            [
                "fake-impersonation.example.com",
                "url_domain"
            ]
        ],
        "reports": [
            "I am in a meeting. Buy gift cards worth \u20b910,000 and send the codes as soon as possible. I will reimburse you.",
            "I am in a meeting. Buy gift cards worth \u20b925,000 and send the codes promptly. I will reimburse you.",
            "I am in a meeting. Buy gift cards worth \u20b91,00,000 and send the codes immediately. I will reimburse you.",
            "My phone is damaged; this is my new number. I urgently need \u20b910,000. Please transfer now.",
            "I am in a meeting. Buy gift cards worth \u20b950,000 and send the codes promptly. I will reimburse you.",
            "Main meeting mein hoon. Confidential payment \u20b950,000 abhi transfer karo. Kisi aur ko mat batana.",
            "My phone is damaged; this is my new number. I urgently need \u20b910,000. Please transfer now.",
            "Main meeting mein hoon. Confidential payment \u20b92,500 abhi transfer karo. Kisi aur ko mat batana.",
            "I am in a meeting. Buy gift cards worth \u20b925,000 and send the codes immediately. I will reimburse you.",
            "My phone is damaged; this is my new number. I urgently need \u20b95,000. Please transfer now."
        ],
        "emerging": False
    },
    "lottery_prize": {
        "summary": "A collection of lottery_prize scams targeting victims via sms, whatsapp, email.",
        "tactics": [
            "advance_fee",
            "too_good_to_be_true",
            "urgency_pressure"
        ],
        "lures": [
            "jackpot_winner",
            "free_gift"
        ],
        "channels": [
            "sms",
            "whatsapp",
            "email"
        ],
        "guidance": {
            "do_now": [
                "Do not click any links or share OTPs.",
                "Block and report the sender."
            ],
            "report_to": [
                "Report to local cyber crime authorities.",
                "Report to the impersonated platform."
            ],
            "recovery": [
                "If money was lost, contact your bank immediately.",
                "Change passwords and enable 2FA."
            ]
        },
        "indicators": [
            [
                "fake-lottery_prize.example.com",
                "url_domain"
            ]
        ],
        "reports": [
            "Aapka mobile number lucky draw mein select hua. Prize \u20b92,500. Claim fee \u20b999 as soon as possible pay karein.",
            "Aapka mobile number lucky draw mein select hua. Prize \u20b950,000. Claim fee \u20b9999 promptly pay karein.",
            "Your email has been selected for a cash award. Send ID details and transfer clearance fee of \u20b9999.",
            "Congratulations! You won \u20b95,000 in an international draw. Pay \u20b92,500 processing tax to release winnings.",
            "Congratulations! You won \u20b91,00,000 in an international draw. Pay \u20b9299 processing tax to release winnings.",
            "Your email has been selected for a cash award. Send ID details and transfer clearance fee of \u20b92,500.",
            "Congratulations! You won \u20b92,500 in an international draw. Pay \u20b9499 processing tax to release winnings.",
            "Aapka mobile number lucky draw mein select hua. Prize \u20b95,000. Claim fee \u20b9299 promptly pay karein.",
            "Your email has been selected for a cash award. Send ID details and transfer clearance fee of \u20b9999.",
            "Your email has been selected for a cash award. Send ID details and transfer clearance fee of \u20b9999."
        ],
        "emerging": False
    },
    "parcel_customs": {
        "summary": "A collection of parcel_customs scams targeting victims via email, whatsapp, sms.",
        "tactics": [
            "fake_delivery_fee",
            "link_obfuscation",
            "urgency_pressure"
        ],
        "lures": [
            "failed_delivery",
            "customs_fee"
        ],
        "channels": [
            "email",
            "whatsapp",
            "sms"
        ],
        "guidance": {
            "do_now": [
                "Do not click any links or share OTPs.",
                "Block and report the sender."
            ],
            "report_to": [
                "Report to local cyber crime authorities.",
                "Report to the impersonated platform."
            ],
            "recovery": [
                "If money was lost, contact your bank immediately.",
                "Change passwords and enable 2FA."
            ]
        },
        "indicators": [
            [
                "fake-parcel_customs.example.com",
                "url_domain"
            ]
        ],
        "reports": [
            "Package address incomplete. \u20b9499 redelivery fee pay karein: https://secure-check.example. Otherwise parcel return hoga.",
            "Package address incomplete. \u20b9299 redelivery fee pay karein: https://secure-check.example. Otherwise parcel return hoga.",
            "Package address incomplete. \u20b999 redelivery fee pay karein: https://secure-check.example. Otherwise parcel return hoga.",
            "Package address incomplete. \u20b9499 redelivery fee pay karein: https://verify-account.example. Otherwise parcel return hoga.",
            "Package address incomplete. \u20b9299 redelivery fee pay karein: https://secure-check.example. Otherwise parcel return hoga.",
            "Illegal items found in a parcel linked to your ID. Pay verification charge immediately to close the case.",
            "Package address incomplete. \u20b9299 redelivery fee pay karein: https://parcel-update.example. Otherwise parcel return hoga.",
            "Your parcel is detained. Pay \u20b9999 customs charge within 24 hours at https://parcel-update.example to avoid legal action.",
            "Illegal items found in a parcel linked to your ID. Pay verification charge as soon as possible to close the case.",
            "Your parcel is detained. Pay \u20b9999 customs charge within 2 hours at https://verify-account.example to avoid legal action."
        ],
        "emerging": False
    },
    "investment_crypto": {
        "summary": "A collection of investment_crypto scams targeting victims via email, sms, whatsapp.",
        "tactics": [
            "high_return_promise",
            "romance_grooming",
            "fake_platform"
        ],
        "lures": [
            "guaranteed_returns",
            "insider_tip"
        ],
        "channels": [
            "email",
            "sms",
            "whatsapp"
        ],
        "guidance": {
            "do_now": [
                "Do not click any links or share OTPs.",
                "Block and report the sender."
            ],
            "report_to": [
                "Report to local cyber crime authorities.",
                "Report to the impersonated platform."
            ],
            "recovery": [
                "If money was lost, contact your bank immediately.",
                "Change passwords and enable 2FA."
            ]
        },
        "indicators": [
            [
                "fake-investment_crypto.example.com",
                "url_domain"
            ]
        ],
        "reports": [
            "Send funds to activate guaranteed double returns within 24 hours. Limited slots only.",
            "SEBI guaranteed secret plan! \u20b92,500 invest karo aur fixed 30% monthly return pao. Loss impossible.",
            "Send funds to activate guaranteed double returns within 24 hours. Limited slots only.",
            "SEBI guaranteed secret plan! \u20b9499 invest karo aur fixed 30% monthly return pao. designed for stable returns.",
            "Send funds to activate guaranteed double returns within 24 hours. Limited slots only.",
            "Send funds to activate guaranteed double returns within 24 hours. Limited slots only.",
            "Send funds to activate guaranteed double returns within 24 hours. Limited slots only.",
            "Send funds to activate guaranteed double returns within 24 hours. Limited slots only.",
            "SEBI guaranteed secret plan! \u20b9299 invest karo aur fixed 50% monthly return pao. Loss impossible.",
            "SEBI guaranteed secret plan! \u20b9499 invest karo aur fixed 30% monthly return pao. Loss impossible."
        ],
        "emerging": False
    },
    "job_scam": {
        "summary": "A collection of job_scam scams targeting victims via sms, email, whatsapp.",
        "tactics": [
            "advance_fee",
            "fake_recruiter",
            "easy_money"
        ],
        "lures": [
            "work_from_home",
            "high_salary"
        ],
        "channels": [
            "sms",
            "email",
            "whatsapp"
        ],
        "guidance": {
            "do_now": [
                "Do not click any links or share OTPs.",
                "Block and report the sender."
            ],
            "report_to": [
                "Report to local cyber crime authorities.",
                "Report to the impersonated platform."
            ],
            "recovery": [
                "If money was lost, contact your bank immediately.",
                "Change passwords and enable 2FA."
            ]
        },
        "indicators": [
            [
                "fake-job_scam.example.com",
                "url_domain"
            ]
        ],
        "reports": [
            "You are selected without interview for a work-from-home role earning \u20b92,500/day. Pay \u20b9299 registration fee to start today.",
            "Aap select ho gaye ho. Joining letter ke liye security deposit \u20b92,500 pay karo. Interview required nahi hai.",
            "You are selected without interview for a work-from-home role earning \u20b95,000/day. Pay \u20b9299 registration fee to start today.",
            "You are selected without interview for a work-from-home role earning \u20b91,00,000/day. Pay \u20b999 registration fee to start today.",
            "Aap select ho gaye ho. Joining letter ke liye security deposit \u20b9499 pay karo. Interview required nahi hai.",
            "Part-time rating job available. Daily income \u20b910,000. Deposit \u20b92,500 to unlock tasks. Contact recruiter now.",
            "You are selected without interview for a work-from-home role earning \u20b950,000/day. Pay \u20b999 registration fee to start soon.",
            "Aap select ho gaye ho. Joining letter ke liye security deposit \u20b9999 pay karo. Interview required nahi hai.",
            "Aap select ho gaye ho. Joining letter ke liye security deposit \u20b9499 pay karo. Interview required nahi hai.",
            "You are selected without interview for a work-from-home role earning \u20b910,000/day. Pay \u20b9999 registration fee to start today."
        ],
        "emerging": False
    },
    "upi_payment": {
        "summary": "A collection of upi_payment scams targeting victims via whatsapp, sms, email.",
        "tactics": [
            "payment_demand",
            "qr_code_fraud",
            "urgency_pressure"
        ],
        "lures": [
            "money_received",
            "cashback_offer"
        ],
        "channels": [
            "whatsapp",
            "sms",
            "email"
        ],
        "guidance": {
            "do_now": [
                "Do not click any links or share OTPs.",
                "Block and report the sender."
            ],
            "report_to": [
                "Report to local cyber crime authorities.",
                "Report to the impersonated platform."
            ],
            "recovery": [
                "If money was lost, contact your bank immediately.",
                "Change passwords and enable 2FA."
            ]
        },
        "indicators": [
            [
                "fake-upi_payment.example.com",
                "url_domain"
            ]
        ],
        "reports": [
            "Congratulations! Aapko \u20b910,000 cashback mila hai. Collect karne ke liye link open karke UPI PIN confirm karein: https://secure-check.example",
            "Hello, Aapko \u20b910,000 cashback mila hai. Collect karne ke liye link open karke UPI PIN confirm karein: https://parcel-update.example",
            "Congratulations! Aapko \u20b92,500 cashback mila hai. Collect karne ke liye link open karke UPI PIN confirm karein: https://secure-check.example",
            "A payment dispute requires immediate validation. Approve the collect request and share confirmation code 589638.",
            "Congratulations! Aapko \u20b91,00,000 cashback mila hai. Collect karne ke liye link open karke UPI PIN confirm karein: https://parcel-update.example",
            "Congratulations! Aapko \u20b950,000 cashback mila hai. Collect karne ke liye link open karke UPI PIN confirm karein: https://parcel-update.example",
            "\u20b950,000 refund pending. Open https://parcel-update.example and enter UPI PIN to receive the amount.",
            "A payment dispute requires immediate validation. Approve the collect request and share confirmation code 490941.",
            "\u20b925,000 refund pending. Open https://parcel-update.example and enter UPI PIN to receive the amount.",
            "A payment dispute requires immediate validation. Approve the collect request and share confirmation code 820420."
        ],
        "emerging": False
    },
    "account_takeover": {
        "summary": "A collection of account_takeover scams targeting victims via whatsapp, email, sms.",
        "tactics": [
            "credential_harvest",
            "otp_theft",
            "urgency_pressure"
        ],
        "lures": [
            "unauthorized_login",
            "verify_identity"
        ],
        "channels": [
            "whatsapp",
            "email",
            "sms"
        ],
        "guidance": {
            "do_now": [
                "Do not click any links or share OTPs.",
                "Block and report the sender."
            ],
            "report_to": [
                "Report to local cyber crime authorities.",
                "Report to the impersonated platform."
            ],
            "recovery": [
                "If money was lost, contact your bank immediately.",
                "Change passwords and enable 2FA."
            ]
        },
        "indicators": [
            [
                "fake-account_takeover.example.com",
                "url_domain"
            ]
        ],
        "reports": [
            "Your mailbox password expires today. Keep access by signing in at https://parcel-update.example.",
            "A confidential document was shared with you. Sign in to view it: https://secure-check.example",
            "A confidential document was shared with you. Sign in to view it: https://secure-check.example",
            "Your mailbox password expires today. Keep access by signing in at https://parcel-update.example.",
            "A confidential document was shared with you. Sign in to view it: https://secure-check.example",
            "Aapka account 24 hours mein deactivate hoga. Login verify karein: https://verify-account.example",
            "Your mailbox password expires today. Keep access by signing in at https://parcel-update.example.",
            "Your mailbox password expires today. Keep access by signing in at https://secure-check.example.",
            "A confidential document was shared with you. Sign in to view it: https://parcel-update.example",
            "A confidential document was shared with you. Sign in to view it: https://parcel-update.example"
        ],
        "emerging": False
    }
}

LEGIT_CONTROLS: list[str] = [
    "Your Amazon order #112-4455 has shipped and will arrive Tuesday. Track it in the Amazon app.",
    "USPS: Your package was delivered to your front door at 2:14 PM. Thanks for using USPS.",
    "Your verification code is 448291. Do not share this code with anyone. — Google",
    "Chase: A deposit of $1,240.00 posted to your checking account. View details in the Chase app.",
    "Reminder: your dentist appointment is tomorrow at 10:00 AM. Reply C to confirm.",
]
