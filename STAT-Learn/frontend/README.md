# manthaino-frontend

Next.js 16 (App Router) + TypeScript + Tailwind + shadcn/ui.

## Setup

```bash
cd frontend
npm ci
cp .env.example .env.local 2>/dev/null || true
```

## Environment

| Variable | Default |
|----------|---------|
| `NEXT_PUBLIC_BACKEND_URL` | `http://localhost:8000` |
| `NEXT_PUBLIC_AI_SERVICE_URL` | `http://localhost:8001` |

## Development

```bash
npm run dev
```

Requires backend session (log in via `/auth/login`). API client: `src/lib/api.ts`.

## Test / build

```bash
npm run lint
npx tsc --noEmit
npm run build
```
