# Log Analyzer Frontend

React + TypeScript frontend for the Local LLM Log Analyzer app.

It allows users to:

- paste logs or stacktraces
- select language and source
- run local LLM analysis
- review structured incident output
- browse and delete stored analyses

## Development

```bash
npm install
npm run dev
```

The Vite dev server expects the FastAPI backend on `http://127.0.0.1:8000`.
