---
name: PlateMatch Editorial Dining Guide
colors:
  surface: '#fbf8fc'
  surface-dim: '#dcd9dd'
  surface-bright: '#fbf8fc'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f2f7'
  surface-container: '#f0edf1'
  surface-container-high: '#eae7eb'
  surface-container-highest: '#e4e1e6'
  on-surface: '#1b1b1e'
  on-surface-variant: '#424842'
  inverse-surface: '#303033'
  inverse-on-surface: '#f3f0f4'
  outline: '#727972'
  outline-variant: '#c2c8c0'
  surface-tint: '#45664e'
  primary: '#32533c'
  on-primary: '#ffffff'
  primary-container: '#4a6b53'
  on-primary-container: '#c5eacc'
  inverse-primary: '#abcfb2'
  secondary: '#a13e28'
  on-secondary: '#ffffff'
  secondary-container: '#fd8367'
  on-secondary-container: '#721c09'
  tertiary: '#644700'
  on-tertiary: '#ffffff'
  tertiary-container: '#815e09'
  on-tertiary-container: '#ffdda0'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c7ecce'
  primary-fixed-dim: '#abcfb2'
  on-primary-fixed: '#01210f'
  on-primary-fixed-variant: '#2e4e37'
  secondary-fixed: '#ffdad2'
  secondary-fixed-dim: '#ffb4a3'
  on-secondary-fixed: '#3d0600'
  on-secondary-fixed-variant: '#822714'
  tertiary-fixed: '#ffdea4'
  tertiary-fixed-dim: '#eec067'
  on-tertiary-fixed: '#261900'
  on-tertiary-fixed-variant: '#5d4200'
  background: '#fbf8fc'
  on-background: '#1b1b1e'
  surface-variant: '#e4e1e6'
typography:
  display-hero:
    fontFamily: Playfair Display
    fontSize: 48px
    fontWeight: '600'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-hero-mobile:
    fontFamily: Playfair Display
    fontSize: 34px
    fontWeight: '600'
    lineHeight: 42px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Playfair Display
    fontSize: 36px
    fontWeight: '500'
    lineHeight: 44px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Playfair Display
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Playfair Display
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Playfair Display
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  title-editorial:
    fontFamily: Playfair Display
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 17px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 23px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 19px
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-caps:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.08em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-sm: 1rem
  margin: 2.5rem
  margin-mobile: 1.25rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

The design system embodies a modern culinary journal: discerning, tactile, and rooted in neighborhood culture. Rather than projecting algorithmic coldness or generic food delivery urgency, it cultivates an unhurried, artisanal atmosphere suitable for discovering bespoke Bangalore dining experiences—from quiet Indiranagar micro-roasteries to heritage South Indian tiffin institutions.

The visual style blends refined editorial layout principles with contemporary web utility. It leverages expansive light-toned whitespace, meticulous typographical pacing, whisper-light hairline borders, and warm botanical undertones. The interface feels like a beautifully typeset food compendium brought to life through subtle interactive surfaces. AI interactions are framed not as robotic prompts, but as knowledgeable, personal concierge recommendations.

## Colors

The palette is anchored in natural culinary materiality—stone, linen, botanical leaf, and roasted terracotta. 

- **Primary (`#4A6B53` Botanical Olive):** Serves as the primary voice for core actions, filter pills, map vectors, and key accents. It delivers a calming, grounded presence without clinical corporate stiffness.
- **Secondary (`#E06D53` Soft Coral):** Dedicated to high-signal anchors: flavor badges, match percentages, curated awards, and rating metrics. It generates appetite appeal and warmth.
- **Tertiary (`#C49A45` Warm Ochre):** Used sparingly for specialty curation tags, Michelin/guide mentions, and price tier indications (`₹₹₹`).
- **Neutrals & Surfaces:**
  - Base Canvas: Pale stone (`#FAFAF7`) establishes an organic paper feel across viewports.
  - Surface Raised: Pure crisp white (`#FFFFFF`) isolates cards, inputs, dialogs, and navigation sheets.
  - Borders: Thin muted stone (`#E6E4DF`) and subdued divide hairline (`#EFECE6`).
  - Text: Deep warm charcoal (`#18181B`) for primary titles, softened charcoal (`#3F3F46`) for readable body copy, and muted slate-stone (`#71717A`) for captions and metadata.

Strictly avoid pure pitch blacks, bright neon hues, and synthetic indigo gradients. Contrast ratios across text and actionable elements strictly satisfy WCAG AA (minimum 4.5:1 on background layers).

## Typography

The typographical pairing strikes an intentional balance between literary sophistication and contemporary digital clarity.

- **Editorial Headings (`Playfair Display`):** Reserved for identity headers, story titles, venue names, and contextual AI match narratives. Weights remain medium (`500`) to semi-bold (`600`) to preserve delicate stroke modulation and avoid visual weight heaviness.
- **Product Interfaces & Body (`Plus Jakarta Sans`):** Powers metadata lines, restaurant operational details, filtering, search fields, reviews, and button labels. It possesses generous apertures and clean geometry, maintaining extreme readability at compact 12px–15px sizes.
- **Eyebrow & Category Treatment:** Locality labels (e.g., "KORAMANGALA 4TH BLOCK", "INDIRANAGAR 100FT RD") utilize `label-caps` in uppercase styling with positive letter tracking (+0.08em) for crisp architectural hierarchy.

## Layout & Spacing

The layout is structured around an adaptive 12-column grid system (desktop), a 6-column grid (tablet), and a 4-column flow (mobile).

- **Desktop (≥1200px):** Maximum content container width of 1320px centered on screen. Fluid 12 columns with 24px (`1.5rem`) gutters and generous 40px (`2.5rem`) side gutters, giving screens breathing space reminiscent of open culinary periodicals.
- **Tablet (768px – 1199px):** 6-column layout with 20px gutters and 24px page margins.
- **Mobile (≤767px):** 4 columns with 16px (`1rem`) gutters and 20px (`1.25rem`) side margins. Sticky contextual bottom bars replace desktop lateral filters.

Spacing follows an 8px base rhythm with 4px sub-increments for fine-grain element locks (such as icon-to-label offsets). Content modules utilize rhythmic vertical spacing: 40px separating cohesive feature sections, and 16px–24px organizing nested items inside cards.

## Elevation & Depth

Visual hierarchy does not rely on heavy drop shadows or dramatic blurs. Depth is achieved primarily through warm surface contrasting and delicate hairline perimeter borders.

- **Base Ground:** Background sits on `#FAFAF7`.
- **Card & Sheet Elevation (Rest):** Pure `#FFFFFF` surfaces bounded by a 1px border of `#E6E4DF`. Shadows are ultra-diffuse and ambient: `0 2px 8px rgba(24, 24, 27, 0.03), 0 1px 2px rgba(24, 24, 27, 0.02)`.
- **Interactive Hover:** Elements translate upward by -2px while the shadow subtly broadens: `0 8px 20px rgba(24, 24, 27, 0.06), 0 2px 4px rgba(24, 24, 27, 0.03)`. The border shifts smoothly from `#E6E4DF` to `#D6D3CC`.
- **Modals, Drawers & AI Concierge Trays:** Positioned over a warm translucent backdrop (`rgba(24, 24, 27, 0.35)` with an 8px background blur). Box shadow deepens to `0 16px 36px rgba(24, 24, 27, 0.08), 0 4px 12px rgba(24, 24, 27, 0.04)`.

## Shapes

The design uses balanced, organic corner curves calibrated to the 12px–16px range, reinforcing the welcoming nature of the hospitality space without falling into juvenile hyper-pill aesthetics:

- **Cards & Dialogue Panels:** 16px (`rounded-xl` equivalent in this scale) creates smooth framing for imagery and venue profiles.
- **Interactive Controls (Inputs, Dropdowns, Buttons):** 12px (`rounded-lg`) for a comfortable, approachable touch footprint.
- **Badges, Filter Chips & Rating Tags:** Rounded pill forms (`9999px`) provide contrast against structured card geometries and signify clickable micro-elements.
- **Images:** Corner radii strictly mirror their parent cards (16px), or use 12px with a 4px inset container border for an archival photographic treatment.

## Components

### Buttons
- **Primary:** Solid `#4A6B53` background with pure `#FFFFFF` typography. 12px border radius, 44px standard height (48px for mobile tap targets). Hover state: `#3D5944`.
- **Secondary / Ghost:** `#FFFFFF` background, 1px `#E6E4DF` border, `#18181B` typography. Hover: `#FAFAF7` background with a `#4A6B53` text transition.
- **Accent (Recommendation / Action CTA):** `#E06D53` background, `#FFFFFF` text. Used exclusively for "Book Table", "PlateMatch Concierge", or critical conversion triggers.

### Chips & Filter Tags
- **Filter Pill (Unselected):** `#FFFFFF` fill, 1px `#E6E4DF` border, `#3F3F46` label. Height: 34px.
- **Filter Pill (Active):** `#4A6B53` background, `#FFFFFF` text, borderless.
- **Metadata Badge (Vibe / Neighborhood / Diet):** `#FAFAF7` background, `#4A6B53` text, delicate `#EFECE6` border, 24px height, typography set to `label-md`.

### Cards (Dining Venues & Recommendations)
- Structured on `#FFFFFF` with a 1px `#E6E4DF` outer stroke and 16px radius.
- Aspect ratio of photography: 16:10 with soft progressive image darkening toward bottom edges for title legibility when overlaid, or cleanly decoupled above an editorial typographic body.
- Content flow within cards:
  1. Eyebrow: Neighborhood ("Lavelle Road") + Distance / Walkability.
  2. Title: Venue name (`headline-sm` in `Playfair Display`).
  3. AI Match Ribbon: "98% Match for filter: Quiet Dinner & Sourdough" highlighted in a soft coral tint (`rgba(224, 109, 83, 0.08)`) with `#E06D53` text.
  4. Footer: Cuisine tags, price tier (`₹₹₹`), and open hours indicator.

### Input Fields & Search Bars
- Background: `#FFFFFF`.
- Border: 1.5px solid `#E6E4DF`.
- Focus State: Border switches directly to `#4A6B53` with an ambient glow of `0 0 0 3px rgba(74, 107, 83, 0.12)`. No harsh browser focus outlines.
- Natural Language Search Bar: Sits prominently with a 16px border radius, 52px height, soft search icon, and conversational placeholder ("Ask PlateMatch: e.g. Co-working cafe with outdoor seating in Indiranagar").

### Checkboxes & Radio Controls
- Base: 20px box/circle with 1.5px stroke `#D6D3CC`.
- Selected: Background fills with `#4A6B53` displaying a crisp white micro-check. Smooth spring-eased transition (150ms).

### Curated Lists & Dish Carousels
- Horizontal snap carousels for neighborhood guides ("Best Filter Coffee in Malleshwaram", "Late Night Craft Beer in Koramangala").
- List rows feature clean bottom hairlines (`#EFECE6`) with generous 16px vertical padding, avoiding cluttered dividers.