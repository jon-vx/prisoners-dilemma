FROM node:24.21.0-bookworm-slim AS base

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1


FROM base AS dependencies

COPY package.json package-lock.json ./
RUN npm ci


FROM base AS build

COPY --from=dependencies /app/node_modules ./node_modules
COPY . .

RUN mkdir -p public && npm run build


FROM base AS runtime

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
COPY --from=build --chown=node:node /app/public ./public

USER node

EXPOSE 3000

CMD ["node", "server.js"]
