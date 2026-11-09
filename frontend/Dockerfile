# syntax=docker/dockerfile:1
#
# Production image of the frontend, used by the CI (.github/workflows/frontend.yml)
# and by `docker compose --profile full up --build`.
# Adapted from the `Frontend` branch.

# ---------------------------------------------------------------------------
# Stage 1: build the static files with Node
# ---------------------------------------------------------------------------
FROM node:24-alpine AS build

WORKDIR /app

# Copy the manifests first so Docker can cache the `npm ci` layer: it is only
# re-run when the dependencies change, not on every code change.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Build-time variables. Vite embeds them in the bundle, so they must be set
# before `npm run build` (see src/vite-env.d.ts).
ARG VITE_API_BASE_URL=/api
ARG VITE_API_MODE=real
ARG VITE_BASE_PATH=/

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_API_MODE=$VITE_API_MODE \
    VITE_BASE_PATH=$VITE_BASE_PATH

RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2: serve them with Nginx (no Node in the final image)
# ---------------------------------------------------------------------------
FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
