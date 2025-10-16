FROM node:18.15.0-alpine AS build
WORKDIR /app
ENV PATH=/app/node_modules/.bin:$PATH

# Environment variables needed for build
ENV REACT_APP_CMF_API_URL=${REACT_APP_CMF_API_URL}

COPY package.json ./
COPY package-lock.json ./
RUN npm install --silent
RUN npm install svg.js
RUN npm install d3
RUN npm install react-scripts@5.0.1 -g --silent
COPY . ./
RUN npm run build

# Production environment
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
EXPOSE 3000
ENTRYPOINT ["/docker-entrypoint.sh"]