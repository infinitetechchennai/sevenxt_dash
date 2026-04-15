# SevenXT Dashboard Frontend

React + Vite frontend for SevenXT admin operations (orders, products, users, refunds, reports).

## Requirements

- Node.js 18+
- npm

## Run Locally

From `Frontend/`:

1. Install dependencies:
   - `npm install`
2. Configure environment variables in `.env` (API base URL and other required keys).
3. Start development server:
   - `npm run dev`

Default local URL: `http://localhost:5173`

## Build for Production

- `npm run build`
- Output is generated in `dist/`.

## Notes

- Keep API endpoints in sync with backend deployment.
- Do not commit secrets in `.env` files.
