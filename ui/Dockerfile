FROM node:18.15.0-alpine
WORKDIR /app
ENV PATH=/app/node_modules/.bin:$PATH
COPY package.json ./
COPY package-lock.json ./
RUN npm install --silent
RUN npm install svg.js
RUN npm install d3
RUN npm install react-scripts@5.0.1 -g --silent
COPY . ./
CMD ["npm", "start"]
