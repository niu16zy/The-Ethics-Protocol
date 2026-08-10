# ---- build the frontend ----
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Empty base URL makes the frontend call the API on its own origin, so the
# deployed container needs no CORS configuration.
ENV VITE_API_BASE_URL=""
RUN npm run build

# ---- backend runtime ----
FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pydantic

COPY backend/ ./backend/
COPY course_content.db ./course_content.db
COPY --from=frontend-build /frontend/dist ./frontend/dist

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
