"use client";

import React, { useState } from 'react';

export default function TopAppBar() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeItem, setActiveItem] = useState('hero');

  const navLinks = [
    { id: 'hero', label: 'Home' },
    { id: 'curriculum', label: 'Curriculum' },
    { id: 'register', label: 'Join' },
    { id: 'faq', label: 'FAQ' },
  ];

  const handleNavClick = (id: string) => {
    setActiveItem(id);
    setIsMobileMenuOpen(false);
  };

  return (
    <header className="fixed top-0 w-full z-50 bg-background border-b border-outline-variant">
      <div className="flex justify-between items-center h-24 px-gutter-md max-w-container-max mx-auto">
        <div className="flex items-center gap-2">
          <img alt="TradeIQ Logo" className="h-20 w-auto object-contain rounded-md scale-110" src="/Icon-removebg-preview.png" />
        </div>
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <a
              key={link.id}
              className={`font-label-caps text-base tracking-widest transition-colors duration-200 border-b-2 py-1 ${activeItem === link.id
                  ? 'text-primary font-extrabold border-primary'
                  : 'text-secondary font-bold border-transparent hover:text-primary'
                }`}
              href={`#${link.id}`}
              onClick={() => handleNavClick(link.id)}
            >
              {link.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-4 text-primary">
            <span className="material-symbols-outlined cursor-pointer hover:opacity-70 transition-opacity">public</span>
            <span className="material-symbols-outlined cursor-pointer hover:opacity-70 transition-opacity">forum</span>
          </div>
          <div className="md:hidden flex items-center">
            <button
              className="material-symbols-outlined text-primary p-2 focus:outline-none"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              {isMobileMenuOpen ? 'close' : 'menu'}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile dropdown menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden absolute top-20 left-0 w-full bg-background border-b border-outline-variant shadow-lg flex flex-col py-6 px-gutter-md gap-6">
          {navLinks.map((link) => (
            <a
              key={link.id}
              className={`font-label-caps text-base tracking-widest transition-colors duration-200 ${activeItem === link.id
                  ? 'text-primary font-extrabold'
                  : 'text-secondary font-bold hover:text-primary'
                }`}
              href={`#${link.id}`}
              onClick={() => handleNavClick(link.id)}
            >
              {link.label}
            </a>
          ))}
        </div>
      )}
    </header>
  );
}
