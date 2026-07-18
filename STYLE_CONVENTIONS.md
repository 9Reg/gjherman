# GJ Herman — Cross-Site Style Conventions

> **Status:** All 10 decisions finalized (2026-07-18). Nothing below is pending — this is the settled reference.

## For AI assistants: read this first

This file is a **portable reference**, not a project file. It documents styling/CSS decisions that apply across all of GJ Herman's author websites — the main site (gjherman.com), and microsites like killingname.com (Shudder) and arc-world.com (Arcworld) — plus any future site in this family.

If you were just dropped into a repo that isn't `gjherman.com` itself and are reading this:

1. **This repo is one member of a family of sites that intentionally share underlying mechanics** (breakpoints, container math, header behavior, font stack, viewport units, token naming, etc.) even though each site has its own visual "mood" (colors, imagery, tone). The goal: a visitor bouncing between these sites should feel a consistent hand, even though each site looks distinct.
2. **Apply the decisions below by default** when writing new CSS/HTML for this repo, or when asked to review/audit this repo's existing styles.
3. **If existing code in this repo conflicts with a decision below**, flag the deviation to the user rather than silently leaving it — but don't rewrite it unprompted; these are standards to reconcile against, not an excuse for an unrequested refactor.
4. **If you (or the user) want to deviate from a decision here for a good reason specific to this site**, that's fine — but say so explicitly and note it, rather than drifting silently. Silent drift across repos is the exact problem this file exists to prevent.
5. **The source of truth for this file lives in the `gjherman.com` repo.** If work in this repo surfaces a reason to change or add a convention, tell the user so they can sync the change back to the master copy — don't just edit this local copy and consider it resolved.
6. **This file is meant to be temporary in any repo other than `gjherman.com`.** Once the styling task here is done, it's fine (and expected) to delete it from this repo unless the user says otherwise.

---

## Decisions

### 1. Header scroll behavior

**Decision:** Header is `position: fixed`, transparent/gradient over the hero (killingname's current look), and gains a solid/blurred background once the user scrolls past the hero — driven by a small vanilla-JS scroll listener toggling a class, not CSS-only scroll-driven animation (better browser support, and every repo can reuse the same snippet verbatim).

**Why:** A floating, transparent header looks best over a hero image (cinematic, not obscuring artwork), but needs to become legible once scrolled over body content — none of the three existing sites do this today (gjherman is sticky+always-opaque; killingname stays transparent forever; arc-world scrolls away). Reusable JS across repos beats a bespoke CSS approach per site.

**Reference implementation** (drop into any site, same file each time):

```js
// header-scroll.js
const header = document.querySelector('.site-header');
addEventListener('scroll', () => {
  header.classList.toggle('is-scrolled', scrollY > 40);
}, { passive: true });
```

```css
.site-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 20;
  background: transparent; /* or the site's hero-gradient overlay */
  transition: background 0.25s ease, backdrop-filter 0.25s ease;
}

.site-header.is-scrolled {
  background: var(--header-bg-solid); /* per-site opaque token, e.g. rgba(paper, 0.93) */
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--line);
}
```

**Applies to:** all sites. Since the header is `fixed` (out of flow), the first section on every page needs top padding equal to the header's visual height so content doesn't start underneath it — see [§3 Breakpoints](#3-breakpoints) / header height token.

### 2. Mobile navigation accessibility

**Decision:** Below the mobile breakpoint, nav links collapse behind a hamburger toggle that opens a full-screen or slide-in panel. Never hide nav with no replacement (killingname currently does `nav { display: none; }` below 560px with nothing to open it — that's the bug this fixes).

**Why:** Every link must stay reachable at every screen width. A hamburger scales better than wrapped always-visible links as a site's nav grows, and gives every site the same interaction pattern.

**Reference implementation** (adapt selectors per site, keep the mechanism identical):

```html
<button class="nav-toggle" aria-expanded="false" aria-controls="nav-links">
  <span class="sr-only">Menu</span>
</button>
<nav id="nav-links" class="nav-links">
  <!-- links -->
</nav>
```

```js
// nav-toggle.js
const toggle = document.querySelector('.nav-toggle');
const nav = document.getElementById('nav-links');
toggle.addEventListener('click', () => {
  const open = nav.classList.toggle('is-open');
  toggle.setAttribute('aria-expanded', open);
});
```

```css
.nav-toggle { display: none; }

@media (max-width: 560px) {
  .nav-toggle { display: inline-flex; }
  .nav-links {
    display: none;
    position: fixed;
    inset: var(--header-height) 0 0 0;
    background: var(--paper);
  }
  .nav-links.is-open { display: flex; flex-direction: column; }
}
```

**Applies to:** all sites, at whatever breakpoint is decided in [§3 Breakpoints](#3-breakpoints).

### 3. Breakpoints

**Decision:** Two breakpoints, everywhere: **880px** (tablet / stacked-layout tier) and **560px** (small-phone tier).

**Why:** gjherman already uses 880/560. killingname was close (860/560) and arc-world only had a single 900px tier with nothing tuned for small phones — 880/560 is the smallest converging change and gives every site the same two-tier rhythm.

```css
@media (max-width: 880px) {
  /* grids collapse to 1 column, nav-wrap stacks, etc. */
}

@media (max-width: 560px) {
  /* section padding tightens, hamburger nav kicks in (§2), etc. */
}
```

**Applies to:** all sites. Any layout-specific media query (grid-template-columns collapsing, padding tightening) should key off these two values rather than inventing a new one per component.

### 4. Container width & gutter

**Decision:** `--max: 1180px`, gutter formula `min(var(--max), calc(100% - 40px))` everywhere.

**Why:** killingname's current numbers (1180px/40px) — chosen over gjherman's 1120px/32px and over inventing a new value, to converge on an existing, already-shipped combination rather than adding a third number into the mix.

```css
:root {
  --max: 1180px;
}

.section-inner {
  width: min(var(--max), calc(100% - 40px));
  margin: 0 auto;
}
```

**Applies to:** all sites. Note gjherman and arc-world both need updating (gjherman from 1120/32, arc-world from its undefined `--max-width` — see [§10](#10-custom-property-hygiene)) to match.

### 5. Typography stack (body + heading fonts, and font-loading hygiene)

**Decision:** Font *choice* is per-site branding, not something to unify — each site's typeface is part of its mood, same as its color palette:
- gjherman.com → **Inter** (sans, headings in Georgia serif)
- arc-world.com → **IBM Plex Sans** (sans throughout)
- killingname.com → **Georgia/serif** (system font, no webfont needed)

**The actual bug isn't the font choice, it's that the loaded font doesn't match the declared one** on two sites today:
- gjherman's CSS declares `font-family: Inter, ...` but its `<head>` only loads IBM Plex Sans — Inter is never fetched, so it silently renders system-ui.
- arc-world's CSS declares `"IBM Plex Sans"` but its font `<link>` points at `https://bunny.net` (the homepage, not a font stylesheet URL) — so it also silently renders system-ui.

**Hard rule going forward:** whatever `font-family` a site's CSS declares as its primary face, verify a matching `<link>` (or `@font-face`) actually loads that exact family before shipping. Don't let CSS and `<head>` drift apart silently — check this any time either is touched.

**Fix owed** (tracked here, not yet applied):
- gjherman: change the bunny.net link to `https://fonts.bunny.net/css?family=inter:400,500,600,700` (or switch the CSS to IBM Plex Sans — either resolves the mismatch, but keep whichever is chosen).
- arc-world: change the link to `https://fonts.bunny.net/css?family=ibm-plex-sans:300,400,500,600,700`.

**Applies to:** whichever font each site already commits to. Any *new* site in the family picks its own typeface intentionally (as part of its visual identity) and just has to pass the hygiene check above.

### 6. Viewport height units

**Decision:** Use `svh` (small viewport height), not `vh`, for any full/near-full-height section (hero, etc.).

**Why:** `svh` accounts for mobile browser chrome (address bar) so hero sections don't visibly resize/jump as the bar shows or hides on scroll. killingname already does this; gjherman and arc-world still use plain `vh` and should switch.

```css
.hero {
  min-height: 88svh; /* not vh */
}
```

**Applies to:** all sites, any `Nvh` value sizing a hero or full-bleed section.

### 7. Color token naming convention

**Decision:** Don't force a shared naming scheme across sites. Each site keeps whatever semantic token names it already has (gjherman/killingname's `ink/muted/paper/line`, arc-world's `bg/text/muted/border`) — the requirement is only that *within* a site, every custom property actually used is actually defined (no dead/undefined `var()` references). See [§10 Custom property hygiene](#10-custom-property-hygiene) for the enforceable version of this rule.

**Why:** Palettes are already intentionally different per site (that's the mood); forcing matching token *names* on top adds churn without a real payoff, since nothing consumes these names across repos — each site's CSS is self-contained.

**Applies to:** nothing to change here specifically — see §10 for the actual actionable rule this implies.

### 8. Button design language

**Decision:** Button *shape* is per-site branding, not something to unify — gjherman/killingname's bordered rectangle and arc-world's solid pill both stay as-is, same as each site keeping its own palette and font.

**Shared mechanical floor regardless of shape:** every button (whatever its border-radius/fill) should keep a **minimum 44px tap-target height** — a WCAG-driven baseline all three already happen to meet today (44–46px), so this is codifying existing practice, not changing anything.

**Applies to:** nothing to change on existing sites. Any new site picks its own button shape as part of its visual identity, but keeps the 44px minimum height.

### 9. CSS reset scope

**Decision:** Reset only `box-sizing` on `*`. Don't blanket-zero `margin`/`padding` globally.

```css
* {
  box-sizing: border-box;
}
```

**Why:** gjherman and killingname already agree on this narrower reset. A blanket `margin: 0; padding: 0;` on every element (arc-world's current approach) guarantees no surprise spacing, but means every element's spacing must be explicitly re-declared somewhere — the narrower reset relies on normal browser defaults plus targeted per-element rules, which is what two of the three sites are already built around.

**Applies to:** arc-world should drop the global `margin: 0; padding: 0;` from its `*` rule and confirm nothing visually depended on it (spot-check layout after removing).

### 10. Custom property hygiene

**Decision:** No tooling — a manual checklist rule, checked whenever CSS is reviewed or shipped: every `var(--x)` reference must have a matching `:root` (or scoped parent) definition. This is what would have caught arc-world's `--max-width` and `--border`, both referenced but never defined, silently no-oping.

**Why:** These are small static sites without a build pipeline; adding stylelint/CI is real tooling overhead (package.json, config, a CI step) for a problem a one-line grep catches. If a site later grows a build step for other reasons, revisit adding a lint rule then — but don't add tooling solely for this.

**Check before shipping any CSS change:**

```bash
# List every var() reference, then cross-check each against :root definitions by eye
grep -oE 'var\(--[a-zA-Z0-9-]+' style.css | sed 's/var(//' | sort -u
```

**Applies to:** all sites. arc-world specifically owes a fix: define `--max-width` (or replace its usages with the `--max` container pattern from [§4](#4-container-width--gutter)) and define `--border` (or replace with `--line`, matching its own existing token for borders).

---

## Outstanding fixes, by repo

Nothing below has been applied yet — this is the checklist for when you're ready to bring each repo in line with the decisions above.

**gjherman**
- Header: switch from sticky+always-opaque to fixed+transparent-over-hero, add the `header-scroll.js` listener + `.is-scrolled` CSS (§1)
- Nav: replace always-visible wrapped links with hamburger toggle at 560px (§2)
- Container: `--max` 1120→1180, gutter 32px→40px (§4)
- Font: fix bunny.net link to actually load Inter, or switch CSS to IBM Plex Sans — pick one (§5)
- Viewport units: hero `vh` → `svh` (§6)
- Breakpoints (880/560) and reset scope (box-sizing only) already match — no change

**killingname**
- Header: keep fixed+transparent, add the `header-scroll.js` listener + `.is-scrolled` opaque state (currently stays transparent forever) (§1)
- Nav: replace `nav { display: none; }` at 560px with hamburger toggle — this is the live bug (§2)
- Breakpoint: 860→880 (560 already matches) (§3)
- Container (`--max: 1180`, 40px gutter), viewport units (`svh`), and reset scope already match — no change

**arc-world**
- Header: add fixed positioning + transparent-over-hero + `header-scroll.js` (currently static, scrolls away entirely — biggest structural change of the three) (§1)
- Nav: add hamburger toggle to match the shared pattern (currently just stacks, doesn't hide — optional convergence rather than a bug fix) (§2)
- Breakpoints: 900 → 880, add the missing 560px small-phone tier (§3)
- Container: define `--max: 1180`, adopt `min(var(--max), calc(100% - 40px))` in place of the current fixed `2rem` padding (§4)
- Font: fix the broken bunny.net link to actually load IBM Plex Sans (§5)
- Viewport units: hero `vh` → `svh` (§6)
- Reset: drop the blanket `margin: 0; padding: 0;` from `*` (§9)
- Define `--max-width` and `--border`, or replace their usages with `--max` (§4) and `--line` respectively (§10)

---

## Site registry

| Site | Domain | Repo | Role |
|---|---|---|---|
| GJ Herman (main) | gjherman.com | `gjherman` | Primary author site — hub, blog, book pages |
| Shudder | killingname.com | `killingname` | Horror novel microsite |
| Arcworld | arc-world.com | `arc-world` | Self-published sci-fi saga microsite |
