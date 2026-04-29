# Claude

Warm, editorial, intellectual product pages.

## Overview

Claude is Anthropic's AI assistant design language. It treats the page like a well-designed magazine spread — warm terracotta accents, generous serif typography, and whispers of shadow instead of hard borders. The parchment foundation with near-black typography creates a reading experience that feels like a book rather than a dashboard.

## Colors

- **Primary** (#141413): Anthropic Near Black — primary text, dark buttons
- **Secondary** (#c96442): Terracotta Brand — CTAs, brand accent
- **Tertiary** (#d97757): Coral Accent — text highlights, dark surface links
- **Focus** (#3898ec): Focus Blue — the only cool color, for focus rings
- **Background** (#f5f4ed): Parchment — warm white base
- **Surface** (#faf9f5): Ivory — cards, containers
- **White** (#ffffff): Pure White — buttons, high contrast
- **Sand** (#e8e6dc): Warm Sand — interactive surfaces, hover states
- **Success** (#22c55e)
- **Warning** (#f59e0b)
- **Error** (#b53333): Error Crimson — warm red
- **Border** (#f0eee6): Border Cream — standard borders
- **Border Warm** (#e8e6dc): prominent dividers

## Typography

- **Serif Font**: Georgia / Noto Serif SC
- **Sans Font**: Inter / Noto Sans SC
- **Mono Font**: SF Mono / Source Code Pro

- **Display**: Georgia 64px medium, 1.10 line height. Hero statements.
- **Section Heading**: Georgia 52px medium, 1.20 line height. Page titles.
- **Sub-heading Large**: Georgia 36px medium, 1.30 line height. Section headers.
- **Sub-heading**: Georgia 32px medium, 1.10 line height. Card titles.
- **Sub-heading Small**: Georgia 25px medium, 1.20 line height. Small headers.
- **Body Serif**: Georgia 17px regular, 1.60 line height. Editorial passages.
- **Body Large**: Inter 20px regular, 1.60 line height. Emphasized body.
- **Body**: Inter 16px regular, 1.60 line height. Default paragraph text.
- **Caption**: Inter 14px regular, 1.43 line height. Metadata, footnotes.
- **Label**: Inter 12px medium, 1.60 line height, 0.12em tracking. Buttons, tags.
- **Code**: SF Mono 15px regular, 1.60 line height. Code snippets.

## Spacing

- **Base unit:** 8px
- **Scale:** 3 / 4 / 6 / 8 / 10 / 12 / 16 / 20 / 24 / 30
- **Component padding (small):** 12px 16px
- **Component padding (medium):** 16px 20px
- **Component padding (large):** 20px 24px
- **Section spacing (mobile):** 48px
- **Section spacing (tablet):** 64px
- **Section spacing (desktop):** 96px

## Border Radius

- **Sharp** (4px): Buttons, inputs
- **Subtle** (6px): Cards, containers
- **Comfortable** (8px): Featured cards
- **Generous** (12px): Panels
- **Very Rounded** (16px): Large containers
- **Maximum** (32px): Hero containers

## Elevation

**Philosophy:** Whisper shadows and ring shadows — Claude's signature. Instead of hard borders, use barely-perceptible ring shadows for containment.

- **Flat**: No shadow, parchment background
- **Contained**: 1px solid border cream
- **Ring**: 0px 0px 0px 1px ring shadow using warm grays
- **Whisper**: rgba(0,0,0,0.05) 0px 4px 24px
- **Inset**: inset 0px 0px 0px 1px at 15% opacity — for pressed states

**Special:** Ring shadow pattern: `0 0 0 1px rgba(0,0,0,0.02)` — softer than a real border, creates a "halo" effect.

## Components

### Buttons

- **Primary**: #c96442 fill, #ffffff text, no border, 8px corners. Inter 500. Hover: #d97757. Active: ring inset.
- **Secondary Dark**: #141413 fill, #ffffff text, no border, 8px corners. Hover: #30302e.
- **Secondary Warm**: #e8e6dc fill, #4d4c48 text, no border, 8px corners. Hover: #d1cfc5.
- **Ghost**: transparent, #5e5d59 text, no border. Hover: background #e8e6dc.
- **Sizes**: Small 36px / Medium 40px / Large 48px height
- **Disabled**: 40% opacity, disabled cursor

### Cards

- **Default**: #faf9f5 fill, no border, 8px corners, whisper shadow. 20px padding. Hover: shadow intensifies to `0 4px 12px rgba(0,0,0,0.08)`.
- **Bordered**: #faf9f5 fill, 1px #f0eee6 border, 8px corners. Hover: border #e8e6dc.
- **Interactive**: Same as bordered, but with hover lift (-0.5px translate) and cursor pointer.

### Inputs

- **Text Input**: #ffffff fill, 1px #f0eee6 border, #141413 text, 8px corners. #87867f placeholder, 12px/16px padding, 44px tall. Focus: border #3898ec, ring 2px #3898ec at 20%. Error: border #b53333, ring #b53333 at 20%.
- **Label**: Inter 500, 12px, tracking 0.02em, uppercase, color #5e5d59, bottom margin 8px
- **Helper text**: Inter 400, 14px, color #87867f

### Tags & Badges

- **Status Badge**: background #22c55e/15%, text #22c55e, 9999px corners. Inter 500 12px. Variants: success/warning/error.
- **Category Tag**: background #e8e6dc, text #5e5d59, 6px corners. Inter 400 12px.

### Probability Bar (Financial)

- **Three-state**: height 8px, width 128px, 8px corners. Left (up) #b53333, middle (stable) #87867f, right (down) #22c55e. Widths determined by probability values.

### Timeline

- **Time Slot**: 16px gap between elements. Time label right-aligned, 64px width, #87867f text. Dot: 8px diameter, #e8e6dc fill, 2px ring #f0eee6. Hover: dot #c96442, ring #c96442 at 30%. Content: left border #f0eee6, 16px left padding.

## Do's and Don'ts

1. **Do** use warm parchment background — it reduces eye strain for long reading sessions.
2. **Don't** use pure white (#ffffff) as page background — it feels clinical and cold.
3. **Do** use ring shadows instead of hard borders — they're softer and more elegant.
4. **Don't** use pure black (#000000) for text — #141413 is warmer and easier to read.
5. **Do** use serif fonts for headlines — they give an editorial, intellectual feel.
6. **Don't** overuse the terracotta brand color — reserve it for primary CTAs only.
7. **Do** use whisper shadows (barely perceptible) — the three-layer pattern creates natural depth.
8. **Don't** use heavy shadows — Claude's aesthetic is light and airy.
9. **Do** use the focus blue (#3898ec) sparingly — it's the only cool color in the palette.
10. **Don't** mix too many font weights — stick to regular (400) and medium (500).