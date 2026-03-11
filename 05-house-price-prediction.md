# House Price Prediction — Complete Standalone Agent Prompt

## Project Identity

| Field | Value |
|-------|-------|
| **Project Folder** | `C:\Users\namsi\Desktop\Projects\House Price Prediction` |
| **Tech Stack** | React + Vite frontend (TypeScript/Tailwind) + Python/Flask backend |
| **Vercel URL** | https://house-price-prediction-ruddy-eight.vercel.app/ |
| **GitHub Repo** | `NamanSingh69/House-Price-Prediction` (already exists) |
| **Vercel Env Vars** | `GEMINI_API_KEY` is set |

### Key Files
- `frontend/src/App.tsx` — Main React component with property valuation form
- `frontend/src/` — React component tree
- `frontend/package.json` — Frontend dependencies (React, Vite, Tailwind, sonner)
- `app.py` or `backend/app.py` — Flask backend with ML prediction + Gemini AI analysis
- `gemini_model_resolver.py` — Backend model cascade handler (Pro → Flash fallback)
- `api/` — Vercel Serverless Functions
- `vercel.json` — Route configuration

---

## Shared Infrastructure Context (CRITICAL)

### Design System — "UX Mandate"
4 core states: Loading (skeleton screens), Success (sonner toasts), Empty (beautiful null states), Error (actionable recovery). Never use `alert()`.

### React Toast Standard: `sonner` library
```tsx
import { Toaster, toast } from 'sonner';
// <Toaster position="bottom-right" richColors />
```

### Smart Model Cascade (March 2026)
**Primary (Free Preview):** `gemini-3.1-pro-preview` → `gemini-3-flash-preview` → `gemini-3.1-flash-lite-preview`
**Fallback (Free Stable):** `gemini-2.5-pro` → `gemini-2.5-flash` → `gemini-2.5-flash-lite`
**Note:** `gemini-2.0-*` deprecated March 3, 2026. Do NOT use.
### Rate limit: 15 RPM, `localStorage.gemini_mode`, resets after 60s
### Security: Server-side API key via Vercel Serverless Functions, never hardcode
### Mobile: 375px–1920px, touch targets ≥ 44px, Tailwind responsive prefixes

---

## Current Live State (Verified March 10, 2026)

| Feature | Status | Details |
|---------|--------|---------|
| Site loads | ✅ 200 OK | Property valuation form with ML analysis UI |
| Login wall | ✅ None | |
| Pro/Fast Toggle | ✅ PRESENT | ⚡ PRO toggle visible in Agent Settings |
| Rate Limit Counter | ✅ PRESENT | Quota 50/50 shown in Agent Settings |
| Empty State | ✅ PRESENT | "Ready for Valuation" message before input |
| Skeleton Loaders | ✅ PRESENT | Skeletons render when Predict is clicked |
| Toasts | ⚠️ Error toast only | Error toast: "Agent Pipeline Failed: Failed to execute 'json' on 'Response': Unexpected end of JSON input" |
| Mobile Responsive | ✅ Yes | Layout adapts at 375px |
| Console Errors | ⚠️ JSON parse | JSON parse error in prediction pipeline |

**NOTE:** The old prompt said Pro/Fast toggle was "MISSING" — this is **WRONG**. The toggle, rate limit, skeletons, and empty state are ALL present. The only issue is the JSON parse bug in the prediction pipeline.

---

## Required Changes

### 1. Fix "Agent Pipeline Failed" JSON Parse Error (CRITICAL — PRIMARY OBJECTIVE)
This is the ONLY major bug. Everything else is working. The error message is:
> `Agent Pipeline Failed: Failed to execute 'json' on 'Response': Unexpected end of JSON input`

This indicates the frontend is trying to parse an empty or malformed JSON response from the backend.

**Debugging steps:**
1. Open DevTools → Network tab → trigger a prediction
2. Find the failing API call — check the response status code and body
3. Likely causes:
   - The serverless function is timing out (Vercel free tier: 10s for Node, 60s for Python)
   - The backend `/api/predict` route is crashing and returning an empty response
   - The Gemini API call in the backend is failing silently
4. **Fix the backend** to always return valid JSON, even on error:
   ```python
   @app.route('/api/predict', methods=['POST'])
   def predict():
       try:
           # ... prediction logic ...
           return jsonify(result)
       except Exception as e:
           return jsonify({"error": str(e)}), 500
   ```
5. **Fix the frontend** to handle non-JSON responses gracefully:
   ```typescript
   const response = await fetch('/api/predict', { ... });
   if (!response.ok) {
     const errorText = await response.text();
     toast.error(`Prediction failed: ${errorText}`);
     return;
   }
   const data = await response.json();
   ```

### 2. Verify Existing UX Features Still Work
Since all UX features (toggle, rate limit, skeletons, empty state) were working in the last audit, simply verify they still function after fixing the JSON bug:
- Pro/Fast toggle persists in `localStorage.gemini_mode`
- Rate limit counter decrements on API calls
- Skeleton loaders appear during prediction
- Success toast fires when prediction completes

### 3. Mobile Responsiveness Hardening
The site already adapts at 375px. Additionally verify:
- Property detail input fields (Area, Bedrooms, etc.) are easily tappable on mobile
- The prediction results card doesn't overflow
- Agent Settings modal scrolls properly on small screens

### 4. GitHub & Deployment
- Push to `House-Price-Prediction` repo: `git add -A && git commit -m "fix: JSON parse error in prediction pipeline, error handling" && git push`
- Redeploy: `npx vercel --prod --yes`
- Verify at https://house-price-prediction-ruddy-eight.vercel.app/

---

## Verification Checklist
1. ✅ Site loads without errors
2. ✅ Pro/Fast toggle visible and functional in Agent Settings
3. ✅ Rate limit counter visible and functional
4. ✅ Enter property details (Area: 2000, Bedrooms: 3, Bathrooms: 2, etc.) → click Predict
5. ✅ Skeleton loader appears during prediction
6. ✅ Prediction completes → **success toast fires (NOT "Agent Pipeline Failed")**
7. ✅ Results display correctly with price estimate
8. ✅ Resize to 375px → fully usable
9. ✅ DevTools console → zero errors
