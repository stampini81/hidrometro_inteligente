# Multi-stage build: backend Node app
FROM node:20-alpine AS deps
WORKDIR /app
COPY backend/package.json ./backend/package.json
RUN cd backend && npm install --omit=dev

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
# Allow overriding port at runtime
ENV PORT=3000
COPY --from=deps /app/backend/node_modules ./backend/node_modules
COPY backend ./backend
COPY frontend ./frontend
# serve frontend via backend at /dashboard (already configured in server.js)
EXPOSE 3000
CMD ["node", "backend/server.js"]
