# Brand Kit

**Sprint:** 32.0 Production Studio MVP  
**Module:** `src/web/src/ai-production-studio/brandKit.ts` · UI `BrandKitPanel`

## Fields

- Logo URL · Primary / Secondary / Accent colors  
- Typography · Voice · Writing style · Visual style  
- Allowed models · Default AI providers  
- Forbidden phrases  

## Behavior

- Persisted in `ews_brand_kit_v1`  
- Injected into prompt variables via `brandVariables()` (`{{tone}}`, `{{colors}}`, `{{forbidden}}`, …)  
- Default provider used by `generateInStudio` when none selected  

Themes/visual tokens remain in Platform Builder deepLink — Brand Kit does not fork the design system.
