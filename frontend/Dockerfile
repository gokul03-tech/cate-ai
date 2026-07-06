# =============================================================================
# Frontend Dockerfile — React + Vite (Production Build)
# =============================================================================

FROM node:20-alpine AS builder

WORKDIR /app

# Build argument for API URL
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline

# Copy source and build
COPY . .
RUN npm run build

# =============================================================================
# Nginx production server
# =============================================================================

FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx config for React Router (SPA routing)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
