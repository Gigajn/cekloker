# CekLoker Web (Next.js) — ditambahkan koordinator Fase 1-lanjutan.
# Build context = ROOT repo (lihat infra/docker-compose.yml).
FROM node:20-alpine

WORKDIR /srv/web

COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY apps/web/ ./

RUN npm run build

ENV NODE_ENV=production
EXPOSE 3000
CMD ["npm", "start"]
