"use client";

import React, { useCallback, useEffect, useState } from 'react';
import useEmblaCarousel from 'embla-carousel-react';
import { curriculumModules } from '@/constants/curriculum';

export default function Curriculum() {
  const [emblaRef, emblaApi] = useEmblaCarousel({ loop: false, align: 'start' });
  const [prevBtnDisabled, setPrevBtnDisabled] = useState(true);
  const [nextBtnDisabled, setNextBtnDisabled] = useState(false);

  const scrollPrev = useCallback(() => emblaApi && emblaApi.scrollPrev(), [emblaApi]);
  const scrollNext = useCallback(() => emblaApi && emblaApi.scrollNext(), [emblaApi]);

  const onSelect = useCallback((emblaApi: any) => {
    setPrevBtnDisabled(!emblaApi.canScrollPrev());
    setNextBtnDisabled(!emblaApi.canScrollNext());
  }, []);

  useEffect(() => {
    if (!emblaApi) return;
    onSelect(emblaApi);
    emblaApi.on('reInit', onSelect).on('select', onSelect);
  }, [emblaApi, onSelect]);

  return (
    <section className="py-margin-lg px-gutter-md bg-surface-container-low overflow-hidden" id="curriculum">
      <div className="max-w-container-max mx-auto">
        <div className="text-center mb-12">
          <span className="font-label-caps text-label-caps text-primary mb-2 block">CURRICULUM OVERVIEW</span>
          <h2 className="font-headline-lg text-headline-lg text-primary mb-4">A Comprehensive Roadmap to Mastery</h2>
          <div className="w-20 h-1.5 bg-primary mx-auto rounded-full"></div>
          <p className="font-body-md text-secondary mt-6 max-w-2xl mx-auto">
            11 specialized modules designed to take you from market basics to building your own AI-powered trading systems.
          </p>
        </div>

        {/* Embla Carousel */}
        <div className="relative max-w-6xl mx-auto">
          <div className="overflow-hidden" ref={emblaRef}>
            <div className="flex touch-pan-y -ml-4">
              {curriculumModules.map((module, index) => (
                <div 
                  key={index} 
                  className="pl-4 flex-[0_0_100%] min-w-0 sm:flex-[0_0_50%] lg:flex-[0_0_33.333%]"
                >
                  <div className="h-full bg-surface-container-lowest p-8 border border-outline-variant/30 rounded-xl shadow-lg transition-all duration-300 hover:shadow-2xl hover:border-primary group flex flex-col">
                    <div className="flex items-center gap-4 mb-6">
                      <div className="w-12 h-12 bg-primary text-on-primary rounded-lg flex items-center justify-center font-bold text-xl shrink-0">
                        {module.moduleNumber}
                      </div>
                      <h3 className="font-bold text-lg text-primary leading-tight">
                        {module.title}
                      </h3>
                    </div>
                    
                    <ul className="space-y-3 flex-grow">
                      {module.topics.map((topic, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="material-symbols-outlined text-primary text-[20px] shrink-0 mt-0.5">
                            check_circle
                          </span>
                          <span className="font-body-sm text-secondary leading-relaxed">
                            {topic}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-center items-center gap-4 mt-10">
            <button
              onClick={scrollPrev}
              disabled={prevBtnDisabled}
              className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                prevBtnDisabled 
                  ? 'bg-surface-container border border-outline-variant text-outline cursor-not-allowed' 
                  : 'bg-primary text-on-primary hover:bg-primary/90 hover:scale-105 shadow-md'
              }`}
              aria-label="Previous module"
            >
              <span className="material-symbols-outlined">arrow_back</span>
            </button>
            <button
              onClick={scrollNext}
              disabled={nextBtnDisabled}
              className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                nextBtnDisabled 
                  ? 'bg-surface-container border border-outline-variant text-outline cursor-not-allowed' 
                  : 'bg-primary text-on-primary hover:bg-primary/90 hover:scale-105 shadow-md'
              }`}
              aria-label="Next module"
            >
              <span className="material-symbols-outlined">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
