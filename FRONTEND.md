# Frontend Strategy

## Canonical Frontend
- **Folder:** `frontend-react`
- **Stack:** React + TypeScript + Vite + Tailwind CSS
- **Usage:** This is the only supported frontend for production deployments. Build and deployment pipelines should target this package.

## Legacy Frontends
The following folders are retained for reference and migration only. They are not deployed and should not receive new features unless explicitly planned for migration:
- `frontend`
- `frontend-spa`
- `frontend_spa`
- `frontend-mvp-v2`

## Notes
- New UI/UX work, including plan/limit surfaces, must live in `frontend-react`.
- If a legacy view needs a fix, prefer porting the feature into `frontend-react` instead of extending the legacy implementation.
