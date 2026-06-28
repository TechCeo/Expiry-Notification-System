FROM node:22-alpine AS build
ARG NPM_CONFIG_STRICT_SSL=true
ENV NPM_CONFIG_STRICT_SSL=${NPM_CONFIG_STRICT_SSL}
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS production
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=5 CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
