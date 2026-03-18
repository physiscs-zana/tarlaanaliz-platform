# =============================================================================
# Dockerfile — Frontend (Next.js) production container
# KR-040: Multi-stage build, non-root user, minimal image
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Dependencies — install node_modules
# ---------------------------------------------------------------------------
FROM node:20-alpine AS deps

WORKDIR /app

# pnpm setup
RUN corepack enable && corepack prepare pnpm@8.15.9 --activate

COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile 2>/dev/null || pnpm install

# ---------------------------------------------------------------------------
# Stage 2: Builder — build the Next.js app
# ---------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@8.15.9 --activate

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build-time environment variables
# ROOT CAUSE FIX: NEXT_PUBLIC_API_BASE_URL = domain only (no /api/v1 suffix)
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_WS_URL
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
ENV NEXT_PUBLIC_WS_URL=${NEXT_PUBLIC_WS_URL}
ENV NEXT_TELEMETRY_DISABLED=1

RUN pnpm build

# ---------------------------------------------------------------------------
# Stage 3: Runtime — minimal production image
# ---------------------------------------------------------------------------
FROM node:20-alpine AS runtime

WORKDIR /app

# Non-root user [KR-040: least privilege]
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 appuser

# Copy only what's needed for production
COPY --from=builder /app/public ./public
COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static

USER appuser

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3000/ || exit 1

CMD ["node", "server.js"]
