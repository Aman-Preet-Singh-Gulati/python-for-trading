"use client";

import React, { useState } from 'react';

export default function Footer() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMessage("");

    try {
      const res = await fetch('/api/newsletter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, website: "" }), // website is honeypot
      });

      const contentType = res.headers.get("content-type");
      let data: any = {};
      if (contentType && contentType.includes("application/json")) {
        data = await res.json();
      }

      if (!res.ok) {
        throw new Error(data.error || `Server Error (${res.status}). Please try again.`);
      }

      setIsSuccess(true);
      setEmail("");
    } catch (err: any) {
      setErrorMessage(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <footer className="border-t border-outline-variant py-margin-lg bg-primary-container">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter-md px-gutter-md max-w-container-max mx-auto text-center md:text-left">
        <div>
          <h4 className="font-headline-lg text-headline-lg font-bold text-on-primary mb-4">TradeIQ</h4>
          <p className="font-body-sm text-on-primary-container max-w-xs mx-auto md:mx-0">
            Empowering the next generation of financial professionals with precision and institutional strategies.
          </p>
          <div className="flex justify-center md:justify-start gap-4 mt-6">
            <span className="material-symbols-outlined text-on-primary cursor-pointer hover:opacity-70">face_nod</span>
            <span className="material-symbols-outlined text-on-primary cursor-pointer hover:opacity-70">language</span>
            <span className="material-symbols-outlined text-on-primary cursor-pointer hover:opacity-70">share</span>
          </div>
        </div>
        <div className="flex flex-col gap-2">
          <span className="font-label-caps text-label-caps text-on-primary mb-4">QUICK LINKS</span>
          <a className="font-body-sm text-on-primary-container hover:text-on-primary transition-colors" href="#">Terms of Service</a>
          <a className="font-body-sm text-on-primary-container hover:text-on-primary transition-colors" href="#">Privacy Policy</a>
          <a className="font-body-sm text-on-primary-container hover:text-on-primary transition-colors underline" href="#">Risk Disclosure</a>
        </div>
        <div>
          <span className="font-label-caps text-label-caps text-on-primary mb-4">STAY UPDATED</span>
          <p className="font-body-sm text-on-primary-container mb-4">Join our newsletter for weekly market insights.</p>
          
          <form onSubmit={handleSubscribe} className="flex flex-col">
            <div className="flex">
              <input 
                required 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-surface-container-lowest border border-outline-variant border-r-0 rounded-l p-2 outline-none focus:border-primary-fixed text-on-surface" 
                placeholder="Email" 
              />
              <button 
                type="submit" 
                disabled={isSubmitting}
                className="bg-primary-fixed text-on-primary-fixed px-4 rounded-r font-label-caps text-[10px] hover:bg-primary-fixed-dim transition-colors disabled:opacity-70"
              >
                {isSubmitting ? "WAIT" : "JOIN"}
              </button>
            </div>
            
            {isSuccess && (
              <p className="text-[#4caf50] font-body-sm mt-2">Successfully subscribed!</p>
            )}
            
            {errorMessage && (
              <p className="text-error font-body-sm mt-2">{errorMessage}</p>
            )}
          </form>

        </div>
      </div>
      <div className="mt-margin-lg pt-base border-t border-on-primary-container/20 text-center px-gutter-md">
        <p className="font-body-sm text-body-sm text-on-primary-container">© 2024 TradeIQ Financial Education. All rights reserved.</p>
      </div>
    </footer>
  );
}
