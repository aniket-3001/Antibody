"""Synthetic seed — 6 scam families with realistic reworded variants, known-bad
indicators (the CONFIRMED fast path), curated guidance, plus legit controls the
asymmetric gate must correctly NOT flag (spec §7, §14).

Shared tactics are deliberately overlapped across families so the graph beat
(spec §16 beat 3) has real traversals:
  • fake_delivery_fee  → usps_redelivery, toll_unpaid, tax_refund
  • urgency_pressure   → nearly all
  • callback_number    → tech_support, bank_otp
  • gift_card_payment  → tech_support, tax_refund
"""
from __future__ import annotations

# Each family: signature tactics/lures, summary, known-bad indicators, guidance,
# and a list of report variants (several reworded, some without any URL/number).
FAMILIES: dict = {
    "usps_redelivery_fee": {
        "summary": "Fake USPS/postal 'redelivery fee' texts. A real carrier never "
                   "charges a redelivery fee by SMS link — that is the tell.",
        "tactics": ["fake_delivery_fee", "urgency_pressure", "credential_harvest", "spoofed_sender"],
        "lures": ["package_delivery"],
        "channels": ["sms"],
        "indicators": [("usps-redelivery.com", "url_domain"),
                       ("usps-trackfee.info", "url_domain"),
                       ("+18775550142", "phone")],
        "guidance": {
            "do_now": [
                "Do not click the link or pay any 'redelivery fee'.",
                "USPS does not charge redelivery fees by text — delete it.",
                "Track packages only at usps.com typed by hand.",
            ],
            "report_to": [
                "US: forward the text to 7726 (SPAM); report at reportfraud.ftc.gov",
                "Report fake USPS texts to spam@uspis.gov",
            ],
            "recovery": [
                "If you entered card details, call your bank and freeze the card.",
                "Watch for further charges and dispute any you didn't make.",
            ],
        },
        "reports": [
            "USPS: Your package is on hold. A $2.99 redelivery fee is required. Pay now at http://usps-redelivery.com to reschedule delivery.",
            "USPS notice: we could not deliver your parcel due to an unpaid fee of $2.99. Confirm at usps-redelivery.com within 24 hours.",
            "United States Postal Service: your shipment is pending. Settle the $1.99 redelivery charge here: usps-trackfee.info",
            "Your parcel is waiting. A small redelivery fee is required to reschedule delivery. Reply or visit the link to release your package.",
            "Hi, this is the post office — a customs fee of £2 is required before we can redeliver your parcel today. Please pay to avoid return.",
            "Postal alert: delivery failed. Unpaid shipping fee detected. Update your address and pay the small fee to receive your item.",
        ],
        "hero_count": 41,  # display target — we replicate reporters up to here
    },
    "toll_unpaid_fee": {
        "summary": "Fake 'unpaid toll' texts (E-ZPass, FasTrak). Same fake-fee tactic "
                   "as delivery scams — pay a tiny fee via a link before a deadline.",
        "tactics": ["fake_delivery_fee", "urgency_pressure", "credential_harvest"],
        "lures": ["toll_road"],
        "channels": ["sms"],
        "indicators": [("ezpass-tollpay.com", "url_domain"),
                       ("ez-pass-notice.net", "url_domain")],
        "guidance": {
            "do_now": [
                "Do not pay — tolling agencies don't collect via random SMS links.",
                "Check your account directly on the official tolling website.",
            ],
            "report_to": ["US: report at reportfraud.ftc.gov; forward to 7726"],
            "recovery": ["If you paid, contact your bank; dispute the charge."],
        },
        "reports": [
            "E-ZPass: You have an unpaid toll of $6.99. Pay before the deadline to avoid a $50 fine: http://ezpass-tollpay.com",
            "Final notice: your toll account has an outstanding balance. Settle the small fee now at ez-pass-notice.net or face penalties.",
            "You have an unpaid highway toll. A late fee will be added if not paid within 24 hours. Pay the toll fee to avoid further charges.",
            "FasTrak alert: unpaid toll detected on your vehicle. Immediate payment of the fee is required to prevent DMV action.",
        ],
        "emerging": True,  # first-seen recent → lights up the emerging feed
    },
    "bank_otp_theft": {
        "summary": "Bank-impersonation fraud alerts that pressure you to read back a "
                   "one-time code or 'verify' via a link — the code is the theft.",
        "tactics": ["impersonation", "urgency_pressure", "credential_harvest", "callback_number"],
        "lures": ["bank_security"],
        "channels": ["sms", "voice_call"],
        "indicators": [("secure-bank-verify.com", "url_domain"),
                       ("+18005550188", "phone")],
        "guidance": {
            "do_now": [
                "Never share a one-time code — your bank will never ask for it.",
                "Hang up and call the number on the back of your card yourself.",
                "Do not click 'verify' links in the message.",
            ],
            "report_to": ["US: reportfraud.ftc.gov", "UK: forward to 7726; actionfraud.police.uk"],
            "recovery": [
                "If you shared a code, call your bank now and lock the account.",
                "Change online banking password and enable app-based 2FA.",
            ],
        },
        "reports": [
            "ALERT: A payment of $499 to Amazon was attempted on your account. If this wasn't you, verify now at secure-bank-verify.com",
            "Your bank: suspicious login detected. Reply with the 6-digit code we just sent to confirm it's you, or your account will be suspended.",
            "This is your bank's fraud department. We detected unauthorized activity. Please confirm your identity by reading the verification code aloud.",
            "Security notice: your card has been temporarily blocked. Call +1 800 555 0188 immediately to restore access.",
            "We noticed an unusual transaction. To keep your account safe, confirm your details and the one-time passcode within 10 minutes.",
        ],
    },
    "tax_refund_scam": {
        "summary": "Fake tax-authority refund/rebate bait (IRS/HMRC). Promises a small "
                   "refund to harvest bank details or a processing 'fee'.",
        "tactics": ["refund_bait", "fake_delivery_fee", "urgency_pressure", "impersonation"],
        "lures": ["tax_refund"],
        "channels": ["sms", "email"],
        "indicators": [("irs-refund-claim.com", "url_domain"),
                       ("hmrc-rebate.co", "url_domain")],
        "guidance": {
            "do_now": [
                "Tax agencies don't issue refunds by text/email links — ignore it.",
                "Never pay a 'processing fee' to receive a refund.",
            ],
            "report_to": [
                "US: report to phishing@irs.gov",
                "UK: report to phishing@hmrc.gov.uk",
            ],
            "recovery": ["If you shared bank details, alert your bank and monitor statements."],
        },
        "reports": [
            "IRS: You are eligible for a tax refund of $842.15. Claim it before it expires at http://irs-refund-claim.com",
            "HMRC: our records show you are due a tax rebate. A small processing fee applies. Claim at hmrc-rebate.co",
            "You have an outstanding tax refund waiting. Confirm your bank details to receive your payment of £312 today.",
            "Final reminder: your government rebate is ready. Verify your identity and pay the small release fee to claim your refund.",
        ],
    },
    "tech_support_callback": {
        "summary": "Fake antivirus/subscription 'renewal' or virus alerts that push you "
                   "to call a number, then demand gift cards or remote access.",
        "tactics": ["impersonation", "callback_number", "gift_card_payment", "urgency_pressure"],
        "lures": ["tech_support"],
        "channels": ["email", "voice_call"],
        "indicators": [("geeksquad-billing.com", "url_domain"),
                       ("+18885550170", "phone")],
        "guidance": {
            "do_now": [
                "Don't call the number — it's not real support.",
                "Never pay with gift cards; no real company asks for that.",
                "Never give remote access to your computer.",
            ],
            "report_to": ["US: reportfraud.ftc.gov"],
            "recovery": [
                "If you gave remote access, disconnect and run a security scan.",
                "If you paid by gift card, report to the card issuer immediately.",
            ],
        },
        "reports": [
            "Geek Squad: Your annual subscription of $399.99 has been renewed. To cancel, call +1 888 555 0170 within 24 hours.",
            "Norton renewal confirmation: $349 charged. If you did not authorize this, contact support at geeksquad-billing.com to dispute.",
            "Your computer is infected with a virus. Call Microsoft support immediately to prevent data loss. Do not restart your PC.",
            "We detected suspicious activity on your device. To fix it, our technician needs remote access — please pay the service fee via gift card.",
        ],
    },
    "crypto_romance_investment": {
        "summary": "Long-con 'pig-butchering' romance + crypto investment scams that "
                   "groom trust then push a fake trading platform or wallet.",
        "tactics": ["romance_grooming", "payment_demand", "urgency_pressure"],
        "lures": ["romance", "crypto_investment"],
        "channels": ["whatsapp", "sms"],
        "indicators": [("0x9f8a3b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f80", "crypto_wallet"),
                       ("coinprofit-vip.com", "url_domain")],
        "guidance": {
            "do_now": [
                "Stop sending money — legitimate partners never ask for crypto.",
                "Be skeptical of any 'guaranteed returns' trading platform.",
            ],
            "report_to": ["US: reportfraud.ftc.gov; ic3.gov for crypto fraud"],
            "recovery": [
                "Save all messages and transaction IDs as evidence.",
                "Report the wallet address to the exchange and to ic3.gov.",
            ],
        },
        "reports": [
            "My dear, I found a trading platform with guaranteed returns. Send to my wallet 0x9f8a3b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f80 and we invest in our future together.",
            "Trust me, I made 40% this week on coinprofit-vip.com. Deposit today so we can grow our savings before the bonus window closes.",
            "I care about you so much. Let's build our future — just start with a small deposit into the investment account I set up for us.",
        ],
    },
}

# Legit control messages — the gate must NOT flag these (spec §7/§14).
LEGIT_CONTROLS: list[str] = [
    "Your Amazon order #112-4455 has shipped and will arrive Tuesday. Track it in the Amazon app.",
    "USPS: Your package was delivered to your front door at 2:14 PM. Thanks for using USPS.",
    "Your verification code is 448291. Do not share this code with anyone. — Google",
    "Chase: A deposit of $1,240.00 posted to your checking account. View details in the Chase app.",
    "Reminder: your dentist appointment is tomorrow at 10:00 AM. Reply C to confirm.",
]
