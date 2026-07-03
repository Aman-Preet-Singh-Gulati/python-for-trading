"use client";

import React, { useState } from 'react';
import { RegistrationFormData, FormField } from '@/types/form';
import { registrationFormSections, getInitialFormData } from '@/constants/registrationForm';

export default function Register() {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<RegistrationFormData>(getInitialFormData());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const totalSteps = registrationFormSections.length;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleNext = () => {
    setErrorMessage(""); // Clear any previous errors
    if (currentStep < totalSteps) setCurrentStep(prev => prev + 1);
  };

  const handleBack = () => {
    if (currentStep > 1) setCurrentStep(prev => prev - 1);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // If we are not on the final step, the form is valid (HTML5 checked it), so just go to next
    if (currentStep < totalSteps) {
      handleNext();
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");
    
    try {
      // We append the honeypot "website" field here as an empty string. 
      // If a bot somehow fills it, the backend will silently discard the request.
      const payload = { ...formData, website: "" };

      const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      // Safe JSON parsing to prevent crashes on 502/504 HTML error pages from proxies
      const contentType = res.headers.get("content-type");
      let data: any = {};
      
      if (contentType && contentType.includes("application/json")) {
        data = await res.json();
      }

      if (!res.ok) {
        if (data.details && Array.isArray(data.details)) {
          // Format Zod field errors into a readable string without technical field names
          const formattedErrors = data.details.map((d: any) => d.message).join(" • ");
          throw new Error(formattedErrors);
        }
        // If details is a string, use it directly. Otherwise use a fallback error.
        const errorMessage = typeof data.details === 'string' 
          ? data.details 
          : (data.error || `Server Error (${res.status}). Please try again.`);
        throw new Error(errorMessage);
      }

      setIsSuccess(true);
    } catch (err: any) {
      console.error(err);
      setErrorMessage(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Helper for rendering radio options
  const renderRadioGroup = (field: FormField) => {
    if (!field.options) return null;
    return (
      <div className="space-y-3 mt-3">
        {field.options.map(option => (
          <label key={option} className="flex items-center gap-3 cursor-pointer group">
            <input
              type="radio"
              name={field.id}
              value={option}
              checked={formData[field.id] === option}
              onChange={handleChange}
              required={field.required}
              className="w-5 h-5 text-primary bg-surface border-outline-variant focus:ring-primary focus:ring-offset-surface-container-lowest transition-all"
            />
            <span className="font-body-md text-secondary group-hover:text-primary transition-colors">{option}</span>
          </label>
        ))}
      </div>
    );
  };

  // Main Field Renderer
  const renderField = (field: FormField) => {
    // Check if the field has a condition and if it is met
    if (field.condition) {
      if (formData[field.condition.fieldId] !== field.condition.equals) {
        return null;
      }
    }

    const commonLabelClass = field.type === 'radio' 
      ? "block font-bold text-primary mb-2" 
      : "block font-label-caps text-label-caps text-primary mb-2";

    const isSmallInput = ['text', 'email', 'tel'].includes(field.type);

    return (
      <div key={field.id} className="mb-8 animate-fade-in">
        <label className={commonLabelClass}>
          {field.label} {field.required && <span className="text-error">*</span>}
        </label>

        {field.type === 'radio' && renderRadioGroup(field)}

        {isSmallInput && (
          <input 
            required={field.required} 
            className="w-full bg-surface border border-outline-variant rounded p-4 focus:ring-1 focus:ring-primary focus:border-primary outline-none" 
            name={field.id} 
            value={formData[field.id] || ""} 
            onChange={handleChange} 
            placeholder={field.placeholder} 
            type={field.type} 
          />
        )}

        {field.type === 'textarea' && (
          <textarea 
            required={field.required} 
            className="w-full bg-surface border border-outline-variant rounded p-4 focus:ring-1 focus:ring-primary focus:border-primary outline-none min-h-[120px]" 
            name={field.id} 
            value={formData[field.id] || ""} 
            onChange={handleChange} 
            placeholder={field.placeholder}
          />
        )}
      </div>
    );
  };

  const currentSection = registrationFormSections.find(s => s.id === currentStep);

  return (
    <section className="py-margin-lg px-gutter-md" id="register">
      <div className="max-w-container-max mx-auto">
        <div className="bg-primary-container rounded-xl overflow-hidden shadow-2xl flex flex-col lg:flex-row min-h-[600px]">
          
          {/* Left Side Info Panel */}
          <div className="lg:w-2/5 p-10 md:p-16 text-on-primary flex flex-col justify-between">
            <div>
              <h2 className="font-headline-xl text-headline-xl mb-6">Secure Your Spot</h2>
              <p className="font-body-md text-on-primary-container mb-8">
                Spaces for our next session are strictly limited. Complete this short application to ensure this bootcamp is the right fit for you.
              </p>
              <ul className="space-y-4">
                <li className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-primary-fixed">check_circle</span>
                  <span className="font-body-sm">Lifetime access to course materials</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-primary-fixed">check_circle</span>
                  <span className="font-body-sm">Exclusive Discord community access</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-primary-fixed">check_circle</span>
                  <span className="font-body-sm">Weekly live market recap calls</span>
                </li>
              </ul>
            </div>
            
            {/* Progress Indicator */}
            {!isSuccess && (
              <div className="mt-12">
                <p className="font-label-caps text-label-caps text-on-primary-container mb-2">
                  STEP {currentStep} OF {totalSteps}
                </p>
                <div className="w-full bg-on-primary-container/20 h-2 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary-fixed transition-all duration-500 ease-out"
                    style={{ width: `${(currentStep / totalSteps) * 100}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>

          {/* Right Side Form Panel */}
          <div className="lg:w-3/5 bg-surface-container-lowest p-10 md:p-16 relative">
            {isSuccess ? (
              <div className="h-full flex flex-col items-center justify-center text-center animate-fade-in">
                <div className="w-20 h-20 bg-primary-fixed rounded-full flex items-center justify-center mb-6">
                  <span className="material-symbols-outlined text-[40px] text-primary">task_alt</span>
                </div>
                <h3 className="font-headline-lg text-primary mb-4">Application Received!</h3>
                <p className="font-body-md text-secondary max-w-md">
                  Thank you for applying. Our team will review your application and get back to you shortly via email or WhatsApp.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="flex flex-col h-full">
                <div className="flex-grow animate-fade-in">
                  
                  {/* Dynamic Step Rendering */}
                  {currentSection && (
                    <>
                      <h3 className="font-headline-md text-primary mb-6">
                        {currentSection.id}. {currentSection.title}
                      </h3>
                      {currentSection.fields.map(field => renderField(field))}
                    </>
                  )}

                </div>

                {/* Error Message Display */}
                {errorMessage && (
                  <div className="mt-6 p-4 bg-error-container text-on-error-container rounded border border-error-container font-body-sm animate-fade-in">
                    <strong>Error:</strong> {errorMessage}
                  </div>
                )}

                {/* Form Navigation Controls */}
                <div className="mt-10 flex flex-col-reverse sm:flex-row items-center justify-between gap-4 pt-6 border-t border-outline-variant/30">
                  {currentStep > 1 ? (
                    <button type="button" onClick={handleBack} className="text-secondary font-bold hover:text-primary transition-colors flex items-center justify-center gap-2 w-full sm:w-auto py-3">
                      <span className="material-symbols-outlined text-[20px]">arrow_back</span>
                      Back
                    </button>
                  ) : (
                    <div className="hidden sm:block"></div> // Spacer
                  )}

                  {currentStep < totalSteps ? (
                    <button type="submit" className="bg-primary text-on-primary font-bold px-8 py-3 rounded transition-all hover:bg-primary/90 flex items-center justify-center gap-2 w-full sm:w-auto">
                      Next
                      <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
                    </button>
                  ) : (
                    <button type="submit" disabled={isSubmitting} className="bg-primary text-on-primary font-bold px-10 py-3 rounded transition-all hover:bg-primary/90 flex items-center justify-center gap-2 disabled:opacity-70 w-full sm:w-auto text-center">
                      {isSubmitting ? 'Submitting...' : 'Submit Application'}
                    </button>
                  )}
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
