---
name: TradeIQ Design System
colors:
  surface: '#fbf9f8'
  surface-dim: '#dbd9d9'
  surface-bright: '#fbf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3f3'
  surface-container: '#efeded'
  surface-container-high: '#eae8e7'
  surface-container-highest: '#e4e2e2'
  on-surface: '#1b1c1c'
  on-surface-variant: '#404943'
  inverse-surface: '#303030'
  inverse-on-surface: '#f2f0f0'
  outline: '#717973'
  outline-variant: '#c0c9c1'
  surface-tint: '#356850'
  primary: '#002819'
  on-primary: '#ffffff'
  primary-container: '#06402b'
  on-primary-container: '#77ac90'
  inverse-primary: '#9cd2b5'
  secondary: '#5f5e5e'
  on-secondary: '#ffffff'
  secondary-container: '#e5e2e1'
  on-secondary-container: '#656464'
  tertiary: '#1f2322'
  on-tertiary: '#ffffff'
  tertiary-container: '#353838'
  on-tertiary-container: '#9ea1a0'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#b8efd0'
  primary-fixed-dim: '#9cd2b5'
  on-primary-fixed: '#002114'
  on-primary-fixed-variant: '#1b503a'
  secondary-fixed: '#e5e2e1'
  secondary-fixed-dim: '#c9c6c5'
  on-secondary-fixed: '#1c1b1b'
  on-secondary-fixed-variant: '#474646'
  tertiary-fixed: '#e1e3e2'
  tertiary-fixed-dim: '#c4c7c6'
  on-tertiary-fixed: '#191c1c'
  on-tertiary-fixed-variant: '#444747'
  background: '#fbf9f8'
  on-background: '#1b1c1c'
  surface-variant: '#e4e2e2'
typography:
  headline-xl:
    fontFamily: Manrope
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Manrope
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Manrope
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  body-md:
    fontFamily: Work Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Work Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.1em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  gutter-md: 24px
  margin-lg: 64px
  container-max: 1280px
---

## Brand & Style
The design system is engineered to project authority, precision, and institutional-grade trust. Targeted at ambitious traders and financial professionals, the visual language draws from **Corporate Modernism** with a **High-Contrast** edge. It avoids the cluttered aesthetic of traditional retail trading platforms in favor of a sophisticated, editorial-inspired layout that emphasizes clarity and high-stakes decision-making.

The emotional response should be one of "calm confidence"—moving away from the frantic energy of the markets toward a structured, educational environment. This is achieved through generous whitespace, sharp geometry, and a palette that mirrors the "bullish" momentum of the forest-green accents found in the primary identity.

## Colors
The palette is rooted in the "Forest Green" and "Deep Onyx" of the brand's logo, symbolizing growth and stability.

- **Primary (Forest Green):** Used for primary actions, success states, and as a strong brand identifier. It should feel rich and deep, not neon.
- **Secondary (Onyx):** Used for typography and structural elements to provide a grounded, premium feel.
- **Surface (Crisp White/Soft Grey):** Backgrounds utilize a stark white for high readability, with a very light grey for secondary containers to provide subtle separation.
- **Accent (Bull/Bear):** Use the primary green for positive market sentiment and a deep, muted charcoal for negative or neutral data points, maintaining high legibility over decorative flair.

## Typography
Typography is functional and structured. **Manrope** is used for headlines to provide a modern, balanced, and technical appearance. Its geometric roots align with chart patterns and data visualization.

**Work Sans** serves as the workhorse for body copy, offering exceptional legibility for educational content and financial disclosures. **Hanken Grotesk** is utilized for metadata, button labels, and small UI details, where its sharp terminals maintain clarity at small scales. 

All headlines should prioritize a tight tracking to feel more impactful and "locked-in."

## Layout & Spacing
The layout follows a **Fixed Grid** system for desktop to maintain the "Lead Magnet" or "White Paper" aesthetic, transitioning to a fluid model for mobile devices.

- **Desktop:** 12-column grid with a 1280px max-width. Guttering is set to 24px to provide breathable separation between content blocks.
- **Mobile:** 4-column grid with 16px margins. Content should reflow vertically, prioritizing a single-column stack for readability of text and charts.
- **Rhythm:** An 8px base unit governs all padding and margin increments. Use larger 64px-80px vertical gaps between major sections to emphasize the premium, spacious brand feel.

## Elevation & Depth
In this design system, depth is conveyed through **Low-Contrast Outlines** and **Tonal Layers** rather than heavy shadows. This maintains the clean, "professional" aesthetic required for finance.

- **Surface Tiers:** Use a light grey (`#F2F4F3`) for containers (cards, sidebars) against the pure white background to create hierarchy.
- **Borders:** Use subtle 1px borders in a muted neutral for input fields and cards.
- **Shadows:** If elevation is required (e.g., a primary CTA button or a modal), use a "Paper" shadow: an extremely soft, blurred drop shadow with 4% opacity and a 16px blur, tinted with the Secondary Onyx color.

## Shapes
To align with the sharp, analytical nature of trading, the shape language is **Soft (0.25rem)**. This provides just enough approachable warmth to keep the UI from feeling "brutalist," while maintaining a sense of architectural precision.

- **Buttons/Inputs:** 4px (0.25rem) corner radius.
- **Large Cards:** 8px (0.5rem) corner radius.
- **Data Points/Candlesticks:** 0px (sharp) to reflect the precision of market data.

## Components
- **Buttons:** Primary buttons use a solid Forest Green background with white text. High-emphasis CTAs should use bold Manrope typography. Secondary buttons use an Onyx outline with transparent background.
- **Input Fields:** Minimalist design with a 1px border and 4px radius. Focus states are indicated by the border color shifting to Forest Green.
- **Cards:** White or light grey backgrounds with 1px borders. Avoid shadows; rely on the border and spacing to define the container.
- **Chips/Badges:** Used for market status (e.g., "Open," "Closed," "Bullish"). These use highly desaturated versions of the primary green or a neutral grey to avoid distracting from the main content.
- **Charts:** Visualizations must strictly adhere to the brand palette—Green for gains, Onyx/Charcoal for losses—ensuring a unified, professional look consistent with the lead magnet's goals.