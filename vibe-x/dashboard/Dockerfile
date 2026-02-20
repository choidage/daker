###############################################################################
# VIBE-X Next.js Dashboard Frontend
#
# Multi-stage build: deps → build → runtime
# output: 'standalone' 모드로 최소 이미지 크기 달성
###############################################################################

# --- Stage 1: Install dependencies ---
FROM node:22-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --ignore-scripts

# --- Stage 2: Build ---
FROM node:22-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG API_BACKEND_URL=http://backend:8000
ENV API_BACKEND_URL=${API_BACKEND_URL}

RUN npm run build

# --- Stage 3: Production runtime ---
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nextjs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3000/ || exit 1

CMD ["node", "server.js"]
