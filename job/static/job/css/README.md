# CSS architecture

The visual baseline for the current refactoring is Git commit `170b110`.
Changes to CSS organization must preserve the rendered appearance of that commit.

## Cascade order

`main.css` loads styles in the following order:

1. `variable.css` — existing design tokens.
2. `fonts.css` — local `@font-face` declarations.
3. `base.css` — element defaults and typography shared by every page.
4. `_typography.css` — branded font utility classes.
5. `layout.css` — document-level spacing and containers.
6. `header.css` and `footer.css` — site chrome.
7. `components.css` — reusable project components.
8. `pages/*.css` — page-specific rules.
9. `bootstrap_overrides.css` — final Bootstrap overrides.

The import order is part of the current UI and must not be changed casually.

## Refactoring rules

- Move one component at a time and keep selectors and declarations unchanged.
- Do not combine CSS cleanup with HTML utility-class replacement.
- Keep Bootstrap grid, form, navbar, carousel, modal, and accessibility classes.
- Compare changes against `170b110` at desktop, tablet, and mobile widths.
- Keep responsive changes separate from structural cleanup.
- Avoid introducing new `!important` declarations.

## Known issues to address incrementally

- Responsive rules are distributed across six files.
- Several custom properties are used without local declarations and currently fall back to Bootstrap or inherited values.
