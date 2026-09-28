FROM node:20-alpine AS base

FROM base AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM base AS runner
WORKDIR /app
COPY --from=builder /app/package.json ./
COPY --from=builder /app/next.config.ts ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Note: The standalone build requires configuring next.config.ts with output: 'standalone'
# For MVP, we can just run the basic server if standalone fails.
EXPOSE 3000
CMD ["node", "server.js"]
