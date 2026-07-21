# Handoff: Scribe — Néo-brutalist meeting assistant

## Overview
Scribe is a meeting-assistant SaaS: it records a meeting (Google Meet / Zoom / Teams or a local dictaphone), transcribes each speaker, and generates a written recap (summary, decisions, action items) at the end. This handoff covers the **neo-brutalist / anti-design** direction: monochrome black-on-white, one loud red accent, heavy display type, hard 4–6px borders, offset drop-shadows, no rounded corners, no gradients.

The package contains one prototype, `Scribe Brut.dc.html`, covering the full flow: **Landing → Login/Signup → Token verification → Consent → App (Dictaphone / En direct / Comptes-rendus)**.

## About the Design Files
The file in this bundle is a **design reference created in HTML** — a prototype showing intended look and behavior, **not production code to copy directly**. The task is to **recreate this design in the target codebase's existing environment** (React, Vue, SwiftUI, native, etc.) using its established patterns, component library, and conventions. If no environment exists yet, choose the most appropriate framework for the project and implement it there. Do not ship the HTML as-is.

> Note on the source format: the prototype is authored as a self-contained component with an inline template + a JS logic class. Treat the template as JSX-like markup and the logic class as component state/handlers when porting.

## Fidelity
**High-fidelity (hifi).** Final colors, typography, spacing, borders, shadows and interactions are all intentional. Recreate the UI pixel-close using the codebase's own primitives — but preserve the exact tokens below (palette, type, border weights, shadow offsets) since they define the aesthetic.

## Design Tokens

### Colors
- Ink / primary: `#0a0a0a`
- Paper / background: `#ffffff`
- Accent (single loud accent, also used for REC / live / errors): `#FF2E00`
- On-accent text: `#ffffff` (a red background ALWAYS pairs with white text — never black)
- Muted text (mono captions): `#666666`
- Speaker dot palette: `#FF2E00`, `#0a0a0a`, `#1a56ff`, `#8a8a00`
- Selection: background `#FF2E00`, text `#0a0a0a`

### Typography
- Wordmark logo **SCRIBE**: **Playfair Display** (900). Display / headings: **Archivo Black** (single weight, uppercase, tight tracking `-1px` to `-3px`).
- Body / labels / captions / UI: **Space Mono** (400 / 700), frequently `text-transform: uppercase` with `letter-spacing: 1–2px`.
- Mid-weight body accents: **Archivo** 800 (e.g. recap list titles).
- Google Fonts import: `Archivo+Black`, `Archivo:wght@400..900`, `Space+Mono:wght@400;700`.

### Borders, shadows, shape
- Border weights: `3px` (small chips/badges), `4px` (default), `6px` (big REC button).
- Border color: always `#0a0a0a`.
- Offset drop-shadows (hard, no blur): `8px 8px 0`, `10px 10px 0`, `12px 12px 0` — color `#0a0a0a` or `#FF2E00`.
- **Border radius: 0 everywhere. No gradients. No blur.**
- Spacing scale is loose/large: section padding 40–80px, card padding 18–28px, gaps 0 (borders separate cells) or 4–12px.

### Animation / keyframes
- `slam` (.25–.35s, `cubic-bezier(.2,.8,.2,1)`): mount transition — element enters from `translate(-8px,-8px)` opacity 0, overshoots to `translate(2px,2px)`, settles. Replaces all fades. Re-fires on screen change, tab change, and recap selection (via a changing React `key`).
- `blink` (1.1s `steps(1)` infinite): REC indicators.
- `bar` (ease-in-out infinite, staggered 0.6–1.4s): waveform bars `scaleY(0.25)`→`1`.
- `pulse` (1.4s ease-in-out infinite): REC button while recording, `scale(1)`→`scale(0.86)`.
- `marq` (18s linear infinite): landing ticker, `translateX(0)`→`translateX(-50%)` on a duplicated string.

## Screens / Views

### Global chrome — Top nav
Sticky, height 64px, white, `border-bottom: 4px solid #0a0a0a`. Left: wordmark **SCRIBE** (Archivo Black, 26px, `-1px`) followed by a 12px red square with 2px black border. Right: **SE CONNECTER →** button — black bg, white text, 4px black border, Space Mono 700 uppercase, `box-shadow: 6px 6px 0 #FF2E00`; hover collapses the shadow to `2px 2px 0` and translates `(4px,4px)` (same effect as the hero buttons). Clicking either the wordmark (→ landing) or the CTA (→ login) navigates.

### 1. Landing
- **Eyebrow chip**: mono uppercase, `3px` black border, inline block — "● Assistant de réunion — audio → compte-rendu".
- **Hero H1**: Archivo Black, `clamp(48px,9vw,128px)`, line-height 0.92, `-3px` tracking, uppercase. Three lines; the word **compte-rendu** is wrapped in a red highlight box (red bg, **white** text, 4px black border, `box-decoration-break: clone`).
- **Sub**: Space Mono 16px, max-width 520px.
- **CTA row**: two buttons (gap 16px). Both share the same treatment — black bg, white text, 4px black border, `box-shadow: 8px 8px 0 #FF2E00`; hover collapses shadow to `2px 2px 0` and translates `(6px,6px)`. Labels "Démarrer" (no arrow) and "Voir une démo".
- **Marquee**: full-bleed black band, top+bottom 4px borders, Archivo Black white 22px scrolling ticker.
- **REC widget card**: 4px border, `box-shadow: 12px 12px 0 #0a0a0a`. Black header bar with white mono text + blinking red "● REC 24:07". Waveform (40 bars, `bar` animation). 3-cell stat grid separated by 4px borders — Participants `04`, Actions détectées `07`, and a red cell (white text) Résumé `AUTO`.
- **Features**: H2 "Trois choses. / Rien de plus." Then a 3-col grid inside a 4px border (cells separated by 4px borders). On card hover the cell turns red bg with white text. Each card: outlined numeral (`-webkit-text-stroke: 2px currentColor; -webkit-text-fill-color: transparent` so the stroke follows the inherited color — black by default, **white** on hover), uppercase title, mono description. Content: 01 Enregistre / 02 Transcrit / 03 Rédige.
- **CTA strip**: full-width black block, hover → red (text stays white); "PRET A ENREGISTRER ?" + a white "Se connecter →" button carrying the same shadow/translate effect as the hero buttons (`box-shadow: 8px 8px 0 #FF2E00`, hover collapse + translate). Navigates to login.
- **Footer**: 4px top border, mono uppercase — "SCRIBE© 2026" / "Chiffré · Privé · Sans bla-bla".

### 2. Login / Signup
Max-width 560px, centered. "← Retour" → landing. H1 toggles "Connexion" / "Créer un compte"; sub-copy toggles too. Form card: 4px border, `box-shadow: 10px 10px 0 #0a0a0a`.
- **Signup-only** field: Nom complet.
- **E-mail** input (4px border; turns red `#FF2E00` on error), inline error "E-mail invalide."
- **Mot de passe** input (type password; red border on error), inline error "8+ caractères, 1 majuscule, 1 caractère spécial."
- Submit block (black, hover red) — label toggles "Se connecter →" / "S'inscrire →".
- Below card: toggle link between login and signup.
- **Validation**: email regex `^[^\s@]+@[^\s@]+\.[^\s@]+$`; password `length>=8 && /[A-Z]/ && /[^A-Za-z0-9]/`. Submit marks both fields touched; advances to Token only if both valid.

### 3. Token verification
Max-width 560px. "← Retour" → login. Red badge (white text) "● Code envoyé". H1 "Vérification", sub "Code à 6 chiffres envoyé à {email}". Six single-char numeric inputs in a flex row (gap 10px, `aspect-ratio: 1`, Archivo Black 28px, 4px border, focus → red bg); typing a digit auto-advances focus to the next cell. "Valider →" block with `8px 8px 0 #FF2E00` shadow (hover collapse) → Consent. "Réessayer / renvoyer le code" clears all cells.

### 4. Consent
Max-width 620px. H1 "Consentement". Bordered explainer box with three lettered points (A/B/C) separated by 3px borders: user controls which meetings are recorded; data encrypted & deletable; no third-party sharing. Custom checkbox: 26px square, 4px border, red fill + white ✕ when checked. Submit "Entrer dans Scribe →" is disabled (opacity 0.4, `cursor: not-allowed`) until consent is checked.

### 5. App shell
Flex row, min-height `calc(100vh - 64px)`.
- **Sidebar** (88px, 4px right border): stacked square tabs, each 4px bottom border, icon (Archivo Black) + tiny mono label. Active tab: black bg / white text (red bg for the live tab). Tabs: **Dicta** (●), **Direct** (~) — *only present while recording* — **Récaps** (▤). "Quitter" pinned to bottom (hover red) → landing.
- Main area re-fires the `slam` animation on every tab change (changing `key`).

#### 5a. Dictaphone tab
H2 "Dictaphone". Big **REC button**: 200×200 square, 6px border, `box-shadow: 10px 10px 0 #0a0a0a`. Idle = red bg, black `●`, "Rec". Recording = red bg, white `■`, "Stop", plus `pulse` animation. Beside it: Statut (PRÊT / EN COURS) + timer `mm:ss`. Clicking toggles recording: starts a 1s interval timer and jumps to the En direct tab; stopping clears the timer and returns to Dictaphone. Below: "Enregistrements récents" list inside a 4px border — rows with title (Archivo 800) + mono date · duration, and an "Ouvrir →" chip; hover → red; click opens that recap in Comptes-rendus.

#### 5b. En direct tab (only while recording)
H2 "En direct" + blinking red REC timer pill (white text, 4px border). Waveform box (48 bars, 4px border). "Intervenants" grid (cells separated by 4px borders): each shows a colored square dot (2–3px black border), name (Archivo 800), and state PARLE / SILENCE. The active speaker's cell gets a red background and toggles on a `secs % 8` cadence (Léa first half, Marc second half — demo behavior).

#### 5c. Comptes-rendus tab (master/detail)
- **Master** (320px, 4px right border): header "Comptes-rendus" + list; selected row has red bg. Click selects.
- **Detail** (re-fires `slam` on each selection via changing `key`): H2 title, mono meta line (date · duration · N participants). Participant chips row (3px-bordered chips with colored dot). Three stacked bordered panels:
  1. **Résumé** — black header bar (white text) + mono paragraph.
  2. **Actions** — red header bar (**white** text), rows separated by 3px borders, each `□ **Who** — what`.
  3. **Transcription** — black header bar (white text), rows separated by 3px borders, each `**Who** (colored) timestamp (grey)` then the line text.

## State Management
Single component state machine:
- `screen`: `'landing' | 'login' | 'token' | 'consent' | 'app'`.
- `signup` (bool), `name`, `email`, `pwd`, `emailTouched`, `pwdTouched`.
- `token`: array of 6 single chars.
- `consent` (bool).
- `tab`: `'rec' | 'live' | 'recaps'`; `recording` (bool); `secs` (int, 1s interval while recording).
- `selIdx` (selected recap index).
- Animation re-trigger keys: `mountKey` (screen change), `appKey` (tab change), `selKey` (recap selection) — each incremented to force React remount so `slam` replays. Port this with keyed remounts or an equivalent re-animate hook.
- Recap data (3 sample meetings) is static in the prototype; back it with a real API in production.

## Interactions & Behavior
- Navigation is client-side screen swapping (no routing in the prototype; add real routes per screen in production).
- Timer: `setInterval` 1000ms while recording; clear on stop and on unmount.
- Auto-advance focus across token cells; digits only (`replace(/\D/g,'')`).
- All hover states listed above use hard color inversions (black↔red, white→red) with no transition easing on color — the motion is in the shadow/translate, not the color.
- Form validation is inline and eager after first touch.

## Assets
No external image assets — all visuals are type, borders, CSS bars and Unicode glyphs (● ■ ~ ▤ □ ✕ →). Fonts from Google Fonts (Archivo Black, Archivo, Space Mono). Real meeting-platform logos (Meet/Zoom/Teams) are referenced only as marquee text here; supply real brand SVGs in production if needed.

## Files
- `Scribe Brut.dc.html` — the full prototype (all five screens + app tabs). Template markup + logic class in one file.
