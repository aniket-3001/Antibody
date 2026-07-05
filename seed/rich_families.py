FAMILIES = [
    {
        "name": "bank_kyc_phishing",
        "summary": "A collection of bank_kyc_phishing scams targeting victims via sms, email, whatsapp.",
        "tactics": [
            "urgency",
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
            {
                "value": "fake-bank_kyc_phishing.example.com",
                "kind": "domain"
            }
        ],
        "templates": [
            "We detected unusual activity. To prevent restriction, complete identity verification within 24 hours: https://secure-check.example",
            "Your bank account will be suspended today. Verify KYC as soon as possible at https://parcel-update.example and confirm your OTP.",
            "We detected unusual activity. To prevent restriction, complete identity verification within 2 hours: https://parcel-update.example",
            "We detected unusual activity. To prevent restriction, complete identity verification within 12 hours: https://parcel-update.example",
            "Your bank account will be suspended today. Verify KYC as soon as possible at https://verify-account.example and confirm your OTP."
        ]
    },
    {
        "name": "loan_scam",
        "summary": "A collection of loan_scam scams targeting victims via whatsapp, sms, email.",
        "tactics": [
            "advance_fee",
            "urgency",
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
            {
                "value": "fake-loan_scam.example.com",
                "kind": "domain"
            }
        ],
        "templates": [
            "CIBIL check ke bina loan approved. Disbursal se pehle \u20b999 insurance fee pay karein.",
            "CIBIL check ke bina loan approved. Disbursal se pehle \u20b9999 insurance fee pay karein.",
            "CIBIL check ke bina loan approved. Disbursal se pehle \u20b9999 insurance fee pay karein.",
            "Your \u20b91,00,000 instant loan is approved with no credit check. Pay \u20b999 file charge to release funds.",
            "Funds are ready. A refundable processing deposit of \u20b9299 is required within 24 hours."
        ]
    },
    {
        "name": "tech_support",
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
            {
                "value": "fake-tech_support.example.com",
                "kind": "domain"
            }
        ],
        "templates": [
            "Your device is infected and banking data is at risk. Call +91 11111 11111 promptly and install remote support software.",
            "Your device is infected and banking data is at risk. Call +91 22222 22222 immediately and install remote support software.",
            "Your device is infected and banking data is at risk. Call +91 00000 00000 immediately and install remote support software.",
            "Your device is infected and banking data is at risk. Call +91 11111 11111 promptly and install remote support software.",
            "Your device is infected and banking data is at risk. Call +91 22222 22222 as soon as possible and install remote support software."
        ]
    },
    {
        "name": "impersonation",
        "summary": "A collection of impersonation scams targeting victims via sms, email, whatsapp.",
        "tactics": [
            "authority",
            "trust_abuse",
            "urgency"
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
            {
                "value": "fake-impersonation.example.com",
                "kind": "domain"
            }
        ],
        "templates": [
            "Main meeting mein hoon. Confidential payment \u20b910,000 abhi transfer karo. Kisi aur ko mat batana.",
            "My phone is damaged; this is my new number. I urgently need \u20b925,000. Please transfer now.",
            "Main meeting mein hoon. Confidential payment \u20b950,000 abhi transfer karo. Kisi aur ko mat batana.",
            "I am in a meeting. Buy gift cards worth \u20b925,000 and send the codes promptly. I will reimburse you.",
            "Main meeting mein hoon. Confidential payment \u20b925,000 abhi transfer karo. Kisi aur ko mat batana."
        ]
    },
    {
        "name": "lottery_prize",
        "summary": "A collection of lottery_prize scams targeting victims via sms, whatsapp, email.",
        "tactics": [
            "advance_fee",
            "too_good_to_be_true",
            "urgency"
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
            {
                "value": "fake-lottery_prize.example.com",
                "kind": "domain"
            }
        ],
        "templates": [
            "Your email has been selected for a cash award. Send ID details and transfer clearance fee of \u20b9499.",
            "Aapka mobile number lucky draw mein select hua. Prize \u20b910,000. Claim fee \u20b999 as soon as possible pay karein.",
            "Aapka mobile number lucky draw mein select hua. Prize \u20b910,000. Claim fee \u20b9499 as soon as possible pay karein.",
            "Hello, You won \u20b91,00,000 in an international draw. Pay \u20b9999 processing tax to release winnings.",
            "Your email has been selected for a cash award. Send ID details and transfer clearance fee of \u20b9999."
        ]
    },
    {
        "name": "parcel_customs",
        "summary": "A collection of parcel_customs scams targeting victims via email, whatsapp, sms.",
        "tactics": [
            "fake_delivery_fee",
            "link_obfuscation",
            "urgency"
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
            {
                "value": "fake-parcel_customs.example.com",
                "kind": "domain"
            }
        ],
        "templates": [
            "Package address incomplete. \u20b9999 redelivery fee pay karein: https://verify-account.example. Otherwise parcel return hoga.",
            "Your parcel is detained. Pay \u20b9999 customs charge within 24 hours at https://parcel-update.example to avoid legal action.",
            "Package address incomplete. \u20b9299 redelivery fee pay karein: https://secure-check.example. Otherwise parcel return hoga.",
            "Package address incomplete. \u20b92,500 redelivery fee pay karein: https://verify-account.example. Otherwise parcel return hoga.",
            "Your parcel is detained. Pay \u20b9299 customs charge within 12 hours at https://verify-account.example to avoid legal action."
        ]
    },
    {
        "name": "investment_crypto",
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
            {
                "value": "fake-investment_crypto.example.com",
                "kind": "domain"
            }
        ],
        "templates": [
            "SEBI guaranteed secret plan! \u20b9299 invest karo aur fixed 100% monthly return pao. Loss impossible.",
            "Send funds to activate guaranteed double returns within 24 hours. Limited slots only.",
            "Send funds to activate guaranteed double returns within 24 hours. Limited slots only.",
            "SEBI guaranteed secret plan! \u20b9299 invest karo aur fixed 100% monthly return pao. Loss impossible.",
            "Send funds to activate guaranteed double returns within 24 hours. Limited slots only."
        ]
    },
    {
        "name": "job_scam",
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
            {
                "value": "fake-job_scam.example.com",
                "kind": "domain"
            }
        ],
        "templates": [
            "Aap select ho gaye ho. Joining letter ke liye security deposit \u20b999 pay karo. Interview required nahi hai.",
            "You are selected without interview for a work-from-home role earning \u20b910,000/day. Pay \u20b9999 registration fee to start today.",
            "You are selected without interview for a work-from-home role earning \u20b925,000/day. Pay \u20b9499 registration fee to start today.",
            "You are selected without interview for a work-from-home role earning \u20b91,00,000/day. Pay \u20b999 registration fee to start today.",
            "Aap select ho gaye ho. Joining letter ke liye security deposit \u20b999 pay karo. Interview required nahi hai."
        ]
    },
    {
        "name": "upi_payment",
        "summary": "A collection of upi_payment scams targeting victims via whatsapp, sms, email.",
        "tactics": [
            "payment_request",
            "qr_code_fraud",
            "urgency"
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
            {
                "value": "fake-upi_payment.example.com",
                "kind": "domain"
            }
        ],
        "templates": [
            "Hello, Aapko \u20b91,00,000 cashback mila hai. Collect karne ke liye link open karke UPI PIN confirm karein: https://verify-account.example",
            "\u20b95,000 refund pending. Open https://parcel-update.example and enter UPI PIN to receive the amount.",
            "\u20b950,000 refund pending. Open https://secure-check.example and enter UPI PIN to receive the amount.",
            "A payment dispute requires immediate validation. Approve the collect request and share confirmation code 248097.",
            "\u20b950,000 refund pending. Open https://parcel-update.example and enter UPI PIN to receive the amount."
        ]
    },
    {
        "name": "account_takeover",
        "summary": "A collection of account_takeover scams targeting victims via whatsapp, email, sms.",
        "tactics": [
            "credential_harvesting",
            "otp_theft",
            "urgency"
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
            {
                "value": "fake-account_takeover.example.com",
                "kind": "domain"
            }
        ],
        "templates": [
            "A confidential document was shared with you. Sign in to view it: https://secure-check.example",
            "A confidential document was shared with you. Sign in to view it: https://verify-account.example",
            "A confidential document was shared with you. Sign in to view it: https://secure-check.example",
            "Aapka account 4 hours mein deactivate hoga. Login verify karein: https://secure-check.example",
            "A confidential document was shared with you. Sign in to view it: https://secure-check.example"
        ]
    }
]