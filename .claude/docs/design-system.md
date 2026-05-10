# Design System Rules (Digital Agency of Japan)

## Component Library

- Use `@digital-go-jp/design-system` as the primary component library
- Never build custom equivalents of components already provided by the design system
- Before writing a new component, verify the design system does not offer one that meets the requirement
- Import components from the library package, not from internal copies or forks

## Design Tokens

- All color, spacing, typography, border-radius, and shadow values must come from design-system CSS custom properties (e.g., `--color-*`, `--spacing-*`, `--font-size-*`)
- Hardcoded hex values, pixel sizes, or font stacks that duplicate token definitions are not allowed
- If a token does not exist for the required value, raise it as a design gap rather than adding an ad hoc value

## Typography

- Primary typeface: BIZ UDPGothic (sans-serif)
- Serif typeface: BIZ UDPMincho (serif, use only where the design explicitly calls for it)
- Do not introduce third-party or custom fonts; use system font stacks only as fallback
- Font-size, line-height, and letter-spacing values must use the design system's typography tokens

## Color

- Use only colors defined in the design system's token set
- Do not add custom color values to the project stylesheet or component styles
- Verify that all text-on-background combinations meet the contrast ratio required by accessibility rules

## Accessibility

- All components and pages must meet WCAG 2.1 Level AA
- Comply with JIS X 8341-3:2016 (Japanese national standard for web accessibility)
- Required checks:
  - Keyboard navigation: every interactive element must be reachable and operable by keyboard alone
  - Focus visibility: focus indicators must always be visible; never suppress the default outline without providing an equivalent
  - Screen reader: verify heading hierarchy, landmark regions, and alt text on all images
  - Color contrast: meet the minimum ratios (4.5:1 for normal text, 3:1 for large text and UI components)
  - Form labels: every input has a programmatically associated label
- Accessibility checks are part of the definition of done for any UI change

## Icons

- Use only icons from the design system's icon set
- Do not add third-party icon libraries (Font Awesome, Material Icons, Heroicons, etc.) alongside the design system
- Icons used for meaning (not decoration) must have accessible labels (`aria-label` or visually hidden text)

## Grid and Spacing

- Use the design system's grid classes and spacing tokens for layout
- Do not invent custom spacing values or create parallel grid utilities
- Responsive breakpoints must follow the design system's defined breakpoints

## Customization

- Override design system defaults only where the design system explicitly documents an extension point
- Every override must have a comment explaining why it is necessary and which constraint it addresses
- Never modify design system component source directly; apply customization through documented APIs (CSS custom property overrides, prop-based variants)
- If a required variant does not exist in the design system, prefer requesting it upstream over building a one-off
