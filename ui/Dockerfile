FROM docker.io/library/node:18.15.0-alpine AS build
WORKDIR /app
ENV PATH=/app/node_modules/.bin:$PATH
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Environment variables needed for build
ENV REACT_APP_CMF_API_URL=${REACT_APP_CMF_API_URL}

COPY package.json ./
COPY package-lock.json ./
# --unsafe-perm skips fchown calls that fail in rootless Podman and cause EMFILE cascade
RUN npm ci --legacy-peer-deps --no-audit --no-fund --unsafe-perm --cache /tmp/.npm
COPY . ./
RUN npm run build

# Production environment
FROM docker.io/library/nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
EXPOSE 3000
ENTRYPOINT ["/docker-entrypoint.sh"]