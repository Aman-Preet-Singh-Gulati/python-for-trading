"use client";

import React, { useState } from 'react';

export default function Hero() {
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <section className="relative bg-primary-container py-16 md:py-24 px-gutter-md overflow-hidden" id="hero">
      <div className="max-w-container-max mx-auto relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          <div className="text-on-primary">
            <div className="inline-block px-4 py-1.5 mb-6 rounded-full bg-primary-fixed/20 text-primary-fixed font-label-caps text-label-caps border border-primary-fixed/30">
              INSTITUTIONAL-GRADE TRADING EDUCATION
            </div>
            <h1 className="font-headline-xl text-headline-xl mb-6 leading-[1.1]">
              Master the Markets with Professional Precision
            </h1>
            <p className="font-body-md text-on-primary-container text-lg mb-8 max-w-xl opacity-90">
              Learn the high-stakes strategies used by institutional desk traders. Join an elite ecosystem focused on risk management, technical mastery, and psychological edge.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 mb-10">
              <a className="bg-primary-fixed text-on-primary-fixed px-8 py-4 rounded-lg font-bold text-center hover:bg-primary-fixed-dim transition-all shadow-lg hover:-translate-y-0.5" href="#register">
                Get Instant Access
              </a>
              <a className="border border-on-primary-container text-on-primary px-8 py-4 rounded-lg font-bold text-center hover:bg-on-primary-container hover:text-primary transition-all" href="#curriculum">
                View Curriculum
              </a>
            </div>
            <div className="flex items-center gap-4 py-4 border-t border-on-primary-container/20">
              <div className="flex -space-x-3">
                <div className="w-10 h-10 rounded-full border-2 border-primary-container bg-surface-container-high overflow-hidden">
                  <img alt="Student" className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCfdEv10KEkf7kCSbRLV2B8IUvnr_1AiS75wmaHrFPKSGlaRA9qC4PRl8ASMyQZNX-hFh-vvRlz5ULenT5cn4Cudnp74Yl6ml2zIX_L1xFSwE2FwzJHoj-g1B1HrhwlVYrI1QPvcbjaibRVdXWsA3_YtsE1Nif_qaRfLb2z6zemLQBwDINK_udIhqrbfAgAjg4mAxmxihje-WgKih-uq9St2a3T-ZT3i0PQbBLCsbZsIhCFMM6Q73oa_tRnIWez7XSz83MCHINSbQ" />
                </div>
                <div className="w-10 h-10 rounded-full border-2 border-primary-container bg-surface-container-high overflow-hidden">
                  <img alt="Student" className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAIqba4A_HAIK8wWcjWYkrsfIAj3ouRN9qZ1Oi8ylIrr8ukTsHKaecLYXYKeFvdM0jdpKEvyAXU3OzefoGJUIqonR3ZbBvwSRwdJs6e4Z0PIQqeTHzArX2Ip62A_M0awfmRPfs56rlAv9bxZF_tyUuUZcldoX45SYZ5twT2pYxdjj8eG3o_PxtgXLonyGnPwGv3nJqAL6tF98RaSOz5nbYLXvyy-OEUDNzXiPWuFuUGkanwu_-DqZUv9qMzI-dcAdx2J4hcOOgW2w" />
                </div>
                <div className="w-10 h-10 rounded-full border-2 border-primary-container bg-surface-container-high overflow-hidden">
                  <img alt="Student" className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDuNOydKWXkt3peWZ3hlBxOirWEOuOlmSRB2RjllciMvkB8RJBI1ZMUFK9sutFXpNqws6OoDfR1jFlGKZ0vOTGjzLqd5E0md3sLSp_dUEUdj6tErF7vm-79n1aYm5DN6CFd4k1ZJ49Xr67R5qgIbUw2YVquKL0JcZUP1SiYdZJJHm7GJ-tkPB5MqMbpCwkuWRDujuwnlSKgQb7FMzZ_RbApuqlhUzPKHm5CSR8dO4siIuD_P_kTqNC1lknpwr2V9Og2FOoZhi6Ifw" />
                </div>
              </div>
              <div className="text-sm font-label-caps text-on-primary-container">
                <span className="text-primary-fixed font-bold">5,000+ TRADERS</span> ENROLLED WORLDWIDE
              </div>
            </div>
          </div>
          <div className="relative">
            <div className="relative group aspect-video bg-black rounded-xl overflow-hidden border-4 border-white/10 shadow-2xl ring-1 ring-primary-fixed/20">
              {isPlaying ? (
                <iframe 
                  className="w-full h-full"
                  src="https://www.youtube.com/embed/LXb3EKWsInQ?autoplay=1" 
                  title="TradeIQ Session Recording" 
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                  allowFullScreen
                ></iframe>
              ) : (
                <>
                  <div className="absolute inset-0 bg-cover bg-center opacity-70 group-hover:scale-105 transition-transform duration-700" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuAbC3RbESKrmWXzVnXO0_IgsXYmWTHDJjOBUSCvYqwRmZjsaxgcpCJjefOvx5opP79H0XzafsUg_XfWkhoiqX6VL6dmHIJpnVc3kl1fMDqAAb-YvgeT2lBEk2OIdPxDwYnSp3w16Y_22NiozaPAf6Wlre3YN-AeofGhTefv7aIW9E-zQBRXsD84UHlvwicAh_ndKzZD9uZQg41GRv7XNAPLSICWxHT4u_nD67rybcL9P7nubeVaEZ0MEeooqWhn0_JfIkE_Sx_59w')" }}></div>
                  <div className="absolute inset-0 bg-primary/20 flex items-center justify-center transition-all group-hover:bg-primary/30">
                    <button 
                      className="w-20 h-20 bg-primary-fixed text-on-primary-fixed rounded-full flex items-center justify-center shadow-2xl transform transition-transform group-hover:scale-110"
                      onClick={() => setIsPlaying(true)}
                    >
                      <span className="material-symbols-outlined text-5xl" style={{ fontVariationSettings: "'FILL' 1" }}>play_arrow</span>
                    </button>
                  </div>
                </>
              )}
            </div>
            <div className="absolute -top-10 -right-10 w-40 h-40 bg-primary-fixed/10 rounded-full blur-3xl -z-10"></div>
          </div>
        </div>
      </div>
      <div className="absolute inset-0 pointer-events-none opacity-[0.03] -z-0">
        <svg height="100%" width="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern height="40" id="grid" patternUnits="userSpaceOnUse" width="40">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="1"></path>
            </pattern>
          </defs>
          <rect fill="url(#grid)" height="100%" width="100%"></rect>
        </svg>
      </div>
    </section>
  );
}
