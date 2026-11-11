
FROM node:20.11.1-alpine AS base
WORKDIR /app

COPY package*.json ./

FROM base AS development

RUN npm ci
COPY . .

RUN chown -R node:node /app
USER node
EXPOSE 5173

CMD ["npm", "run", "dev"]

FROM base AS builder
RUN npm ci
COPY . .
RUN npm run build


FROM nginx:alpine AS production
RUN apk upgrade --no-cache

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
