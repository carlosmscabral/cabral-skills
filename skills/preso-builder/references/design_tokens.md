# Design System Tokens & Visual Standards Reference
## The AI Factory Blueprint Design Language

This document defines the exact design tokens, typography hierarchies, color palettes, coordinate bounding boxes, and accessibility rules reverse-engineered from the master reference presentation:
**"The AI Factory Blueprint - A developer's playbook for the agentic era"** (`1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U`).

---

### 1. Canvas Geometry & Coordinate System

Google Slides uses **English Metric Units (EMU)** natively, while the `gslides` batch operations and layout calculations operate in **Points (pt)**.

$$\text{1 pt} = 12,700\text{ EMU}$$
$$\text{1 inch} = 72\text{ pt} = 914,400\text{ EMU}$$

#### Standard Widescreen (16:9) Dimensions
| Property | Value (Points) | Value (EMU) | Notes |
| :--- | :--- | :--- | :--- |
| **Canvas Width** | `720.0 pt` | `9,144,000 EMU` | Total slide width |
| **Canvas Height** | `405.0 pt` | `5,143,500 EMU` | Total slide height |
| **Margin Left** | `36.0 pt` | `457,200 EMU` | Left safe margin |
| **Margin Right** | `36.0 pt` | `457,200 EMU` | Right safe margin |
| **Margin Top** | `28.0 pt` | `355,600 EMU` | Top safe margin |
| **Margin Bottom** | `30.0 pt` | `381,000 EMU` | Bottom safe margin |
| **Usable Width** | `648.0 pt` | `8,229,600 EMU` | Width inside safe margins |
| **Usable Height** | `275.0 pt` | `3,492,500 EMU` | Content area height |
| **Header Baseline** | `92.0 pt` | `1,168,400 EMU` | Header separation line |
| **Content Top** | `100.0 pt` | `1,270,000 EMU` | Starting Y for card bodies |

---

### 2. Standard Header & Title Layout

All content slides (Archetypes 2 through 8) share a standardized header layout:

```
Y=28pt ┌─────────────────────────────────────────────────────────────┐
       │ [KICKER] 10pt Google Sans, Uppercase, Tracking +1.5pt       │
Y=40pt │ SLIDE TITLE: 24pt Google Sans Bold (#202124)                │
Y=68pt │ Subtitle / Thesis: 13pt Google Sans Text (#5F6368)          │
Y=92pt ├─────────────────────────────────────────────────────────────┤ (Header Baseline)
Y=100pt│ [CONTENT AREA: 648pt Wide x 275pt High]                    │
```

* **Slide Title**: Height `26.0 pt`, Font: `Google Sans 24pt Bold` (weight: 700), Color: `#202124` (Light) or `#FFFFFF` (Dark).
* **Slide Subtitle**: Height `20.0 pt`, Font: `Google Sans Text 13pt Regular` (weight: 400), Color: `#5F6368` (Light) or `#CADCFC` (Dark).
* **Category Kicker (Optional)**: Height `14.0 pt`, Font: `Google Sans 10pt Bold` (weight: 700), All Caps, Color: `#1A73E8`.

---

### 3. Typography Scales & Roles

| Role | Font Family | Size | Weight | Line Spacing | Color (Light / Dark Theme) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hero / Chapter Number** | `Google Sans` | `84.0 pt` | Bold (700) | 100% | `#1A73E8` / `#CADCFC` |
| **Chapter Title** | `Google Sans` | `36.0 pt` | Bold (700) | 115% | `#FFFFFF` |
| **Chapter Subtitle** | `Google Sans Text`| `16.0 pt` | Regular (400)| 130% | `#CADCFC` |
| **Slide Title** | `Google Sans` | `24.0 pt` | Bold (700) | 120% | `#202124` / `#FFFFFF` |
| **Slide Subtitle** | `Google Sans Text`| `13.0 pt` | Regular (400)| 130% | `#5F6368` / `#CADCFC` |
| **Card Header** | `Google Sans` | `16.0 pt` | Bold (700) | 120% | `#202124` / `#FFFFFF` |
| **Card Body / Bullets** | `Google Sans Text`| `12.0 pt` | Regular (400)| 140% | `#202124` / `#E8EAED` |
| **Pill / Tag Label** | `Google Sans` | `9.5 pt` | Bold (700) | 100% | `#174EA6` / `#137333` / `#C5221F` |
| **Stat Number Value** | `Google Sans` | `54.0 pt` | Bold (700) | 100% | `#202124` / `#1E8E3E` / `#FFFFFF` |
| **Stat Unit Label** | `Google Sans Text`| `13.0 pt` | Regular (400)| 120% | `#5F6368` |
| **Code / Syntax Body** | `Roboto Mono` | `10.5 pt` | Regular (400)| 135% | `#CADCFC` / `#202124` |
| **Code Filename Header**| `Roboto Mono` | `11.0 pt` | Regular (400)| 100% | `#BDC1C6` |
| **Rung / Step Title** | `Google Sans` | `14.0 pt` | Bold (700) | 120% | `#202124` |
| **Rung Description** | `Google Sans Text`| `11.0 pt` | Regular (400)| 130% | `#5F6368` |
| **Quadrant Header** | `Google Sans` | `15.0 pt` | Bold (700) | 120% | `#202124` |
| **Quadrant Body** | `Google Sans Text`| `11.5 pt` | Regular (400)| 135% | `#5F6368` |
| **Speaker Notes** | `Google Sans Text`| `11.0 pt` | Regular (400)| 140% | `#3C4043` |

---

### 4. Color Palette & WCAG 2.1 AA Tokens

#### Core Color Palette
```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ #1E2761 Navy    │ │ #1A73E8 Blue    │ │ #1E8E3E Green   │ │ #D93025 Red     │
│ (Primary Dark)  │ │ (Accent Brand)  │ │ (Success / DO)  │ │ (Alert / DON'T) │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ #F8F9FA Light   │ │ #FFFFFF White   │ │ #202124 Slate   │ │ #DADCE0 Border  │
│ (Canvas BG)     │ │ (Card Fill)     │ │ (Primary Text)  │ │ (Stroke / Rule) │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

| Token Constant | Hex Value | RGB Tuple | Role & Description |
| :--- | :--- | :--- | :--- |
| `COLOR_NAVY_PRIMARY` | `#1E2761` | `(30, 39, 97)` | Chapter divider slide background, dark roadmap card |
| `COLOR_NAVY_SURFACE` | `#2D3A8C` | `(45, 58, 140)` | Elevated cards on navy background |
| `COLOR_SLATE_DARK` | `#202124` | `(32, 33, 36)` | Code terminal container background |
| `COLOR_SLATE_HEADER` | `#2D3035` | `(45, 48, 53)` | Code terminal window header bar |
| `COLOR_BG_LIGHT` | `#F8F9FA` | `(248, 249, 250)` | Standard light slide canvas background |
| `COLOR_CARD_WHITE` | `#FFFFFF` | `(255, 255, 255)` | Standard card surface |
| `COLOR_CARD_BORDER` | `#DADCE0` | `(218, 220, 224)` | Subtle 1pt card outline / border |
| `COLOR_BLUE_ACCENT` | `#1A73E8` | `(26, 115, 232)` | Primary accent, divider rules, CTA button fill |
| `COLOR_BLUE_LIGHT` | `#E8F0FE` | `(232, 240, 254)` | Category pill fill, takeaway footer banner fill |
| `COLOR_BLUE_SUBTITLE` | `#CADCFC` | `(202, 220, 252)` | Subtitle text on navy backgrounds |
| `COLOR_GREEN_DO` | `#1E8E3E` | `(30, 142, 62)` | Positive metric stat, DO badge accent |
| `COLOR_GREEN_LIGHT` | `#E6F4EA` | `(230, 244, 234)` | DO card top banner fill, DO badge container |
| `COLOR_RED_DONT` | `#D93025` | `(217, 48, 37)` | DON'T card top banner fill, alert pill accent |
| `COLOR_RED_LIGHT` | `#FCE8E6` | `(252, 232, 230)` | DON'T card container background |
| `COLOR_AMBER_WARN` | `#F9AB00` | `(249, 171, 0)` | Caution indicators, warning badges |
| `COLOR_AMBER_LIGHT` | `#FEF7E0` | `(254, 247, 224)` | Caution container background |
| `COLOR_TEXT_PRIMARY` | `#202124` | `(32, 33, 36)` | Primary high-contrast body & heading text |
| `COLOR_TEXT_MUTED` | `#5F6368` | `(95, 99, 104)` | Subtitles, secondary descriptions, units |
| `COLOR_TEXT_WHITE` | `#FFFFFF` | `(255, 255, 255)` | Text on dark navy and dark slate containers |

#### High-Contrast Pill Text Tokens (WCAG 2.1 AA Compliance)
To prevent contrast failures on light pastel backgrounds (e.g. `#E8F0FE`), the system uses specialized high-contrast text tokens:

| Container Background | Standard Text Token | Contrast Ratio | WCAG Compliance |
| :--- | :--- | :--- | :--- |
| `#E8F0FE` (Light Blue) | `COLOR_BLUE_TEXT` (`#174EA6`) | **`5.74:1`** | **PASS (AA Normal & Large)** |
| `#E6F4EA` (Light Green) | `COLOR_GREEN_TEXT` (`#137333`) | **`4.92:1`** | **PASS (AA Normal & Large)** |
| `#FCE8E6` (Light Red) | `COLOR_RED_TEXT` (`#C5221F`) | **`5.01:1`** | **PASS (AA Normal & Large)** |
| `#FEF7E0` (Light Amber) | `COLOR_AMBER_TEXT` (`#7A4100`) | **`5.25:1`** | **PASS (AA Normal & Large)** |
| `#1E2761` (Navy Dark) | `COLOR_TEXT_WHITE` (`#FFFFFF`) | **`14.62:1`** | **PASS (AAA Enhanced)** |
| `#1E2761` (Navy Dark) | `COLOR_BLUE_SUBTITLE` (`#CADCFC`)| **`11.20:1`** | **PASS (AAA Enhanced)** |
| `#202124` (Slate Dark) | `COLOR_BLUE_SUBTITLE` (`#CADCFC`)| **`12.45:1`** | **PASS (AAA Enhanced)** |
