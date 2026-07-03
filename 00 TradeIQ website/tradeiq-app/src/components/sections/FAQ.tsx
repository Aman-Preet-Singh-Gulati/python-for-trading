"use client";

import React, { useState } from 'react';
import { faqs } from '../../constants/faqs';

export default function FAQ() {
  const [activeIndex, setActiveIndex] = useState<number | null>(0);

  const toggleAccordion = (index: number) => {
    setActiveIndex(activeIndex === index ? null : index);
  };

  return (
    <section className="py-margin-lg px-gutter-md bg-surface-container-lowest" id="faq">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="font-headline-lg text-headline-lg text-primary mb-4">Frequently Asked Questions</h2>
          <p className="font-body-md text-secondary">Everything you need to know before starting your journey.</p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
          {faqs.map((faq, index) => (
            <div key={index} className={`border border-outline-variant rounded-lg overflow-hidden transition-all hover:border-primary ${activeIndex === index ? 'border-primary' : ''}`}>
              <button 
                className="w-full p-6 text-left flex justify-between items-center bg-surface-container-low" 
                onClick={() => toggleAccordion(index)}
              >
                <span className="font-body-md font-bold text-primary">{faq.question}</span>
                <span className={`material-symbols-outlined transition-transform duration-300 ${activeIndex === index ? 'rotate-180' : ''}`}>
                  expand_more
                </span>
              </button>
              <div 
                className="bg-surface-container-lowest transition-all duration-300 ease-in-out overflow-hidden"
                style={{ maxHeight: activeIndex === index ? '500px' : '0' }}
              >
                <div className="p-6 pt-0 font-body-sm text-secondary">
                  {faq.answer}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
