import React from "react";
import { Globe, ShieldCheck, MailWarning } from "lucide-react";
import { Card, CardContent } from "./ui/card.jsx";
import { Button } from "./ui/button.jsx";

export default function ExtensionPreviewView() {
  return (
    <div className="flex flex-col gap-6">
      <div className="text-center">
        <h2 className="text-2xl font-extrabold text-[var(--color-ink)] flex items-center justify-center gap-2">
          <Globe className="text-[#4285F4]" size={28} />
          Browser Extension (Coming Soon)
        </h2>
        <p className="mt-2 text-[15px] text-[var(--color-body)]">
          Antibody will soon live in your browser, protecting you in real-time.
        </p>
      </div>

      <Card className="border border-[var(--color-line)] shadow-lg overflow-hidden bg-white">
        {/* Mock Browser Header */}
        <div className="bg-[#f1f3f4] p-2 flex items-center gap-2 border-b border-[#dadce0]">
          <div className="flex gap-1.5 ml-2">
            <div className="w-3 h-3 rounded-full bg-[#ff5f56]"></div>
            <div className="w-3 h-3 rounded-full bg-[#ffbd2e]"></div>
            <div className="w-3 h-3 rounded-full bg-[#27c93f]"></div>
          </div>
          <div className="flex-1 bg-white mx-4 rounded-full h-6 border border-[#dadce0] flex items-center px-3 text-[11px] text-[#5f6368]">
            mail.google.com
          </div>
          <div className="flex items-center justify-center w-6 h-6 rounded-full bg-[var(--color-brand-soft)] text-[var(--color-brand)] mr-2 relative">
            <ShieldCheck size={14} />
            <span className="absolute -top-1 -right-1 bg-[var(--color-danger)] text-white text-[9px] font-bold px-1 rounded-full">1</span>
          </div>
        </div>

        {/* Mock Email Body */}
        <CardContent className="p-0">
          <div className="flex h-64">
            {/* Sidebar */}
            <div className="w-1/4 bg-[#f8f9fa] border-r border-[#dadce0] p-3 hidden sm:block">
              <div className="h-4 bg-[#e8eaed] rounded w-3/4 mb-4"></div>
              <div className="h-3 bg-[#e8eaed] rounded w-1/2 mb-3"></div>
              <div className="h-3 bg-[#e8eaed] rounded w-2/3 mb-3"></div>
            </div>
            
            {/* Main Email */}
            <div className="flex-1 p-6 flex flex-col gap-4 relative">
              <div>
                <h3 className="text-lg font-bold text-[#202124]">Action Required: Account Suspension Notice</h3>
                <div className="text-sm text-[#5f6368] mt-1">From: support@paypal-security-update.com</div>
              </div>
              <div className="text-sm text-[#202124] leading-relaxed">
                Dear Customer,<br/><br/>
                We detected unusual activity on your account. Your account will be permanently suspended in 24 hours if you do not verify your identity.<br/><br/>
                <div className="relative inline-block mt-2">
                  <span className="bg-[#1a73e8] text-white px-4 py-2 rounded font-medium inline-block relative border-2 border-[var(--color-danger)]">
                    Verify Account Now
                  </span>
                  
                  {/* Extension Tooltip overlay */}
                  <div className="absolute top-12 left-1/2 -translate-x-1/2 w-64 bg-[var(--color-surface)] border-2 border-[var(--color-danger)] rounded-lg shadow-xl p-3 z-10">
                    <div className="flex items-center gap-2 text-[var(--color-danger)] font-bold text-xs uppercase mb-2">
                      <MailWarning size={14} /> Phishing Link Detected
                    </div>
                    <div className="text-xs text-[var(--color-body)] leading-relaxed">
                      This button links to a known credential harvesting site. <b>Do not click.</b>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <div className="text-center">
        <Button variant="secondary">Join the Waitlist</Button>
      </div>
    </div>
  );
}
