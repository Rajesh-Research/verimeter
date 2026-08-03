# Stage 1: Install dependencies and build Next.js app
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package descriptors
COPY package*.json ./

# Install npm packages
RUN npm ci

# Copy frontend source files
COPY src/ ./src/
COPY public/ ./public/
COPY tsconfig.json tailwind.config.js postcss.config.js next.config.mjs ./

# Disable telemetry and build the production bundle
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2: Runtime runner image
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# Copy static assets and optimized pages
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000

# Start Next.js production server
CMD ["npm", "start"]
