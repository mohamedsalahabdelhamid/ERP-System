# syntax=docker/dockerfile:1

# ============================================================
# ERP frontend image (React + Vite) -> static build served by Nginx.
# Nginx also proxies /api to the backend so the whole stack is
# reachable from a single origin (easy deployment anywhere).
# ============================================================
FROM node:22-alpine AS build

WORKDIR /app

# Install dependencies first for better layer caching.
COPY package*.json ./
RUN npm install

# Build the static site.
COPY . .
RUN npm run build

# ---- Runtime: static files + reverse proxy ----
FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
