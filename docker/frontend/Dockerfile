FROM node:22-slim

WORKDIR /app

RUN corepack enable

COPY frontend/package.json ./
RUN pnpm install --no-frozen-lockfile

COPY frontend /app

EXPOSE 3000

CMD ["pnpm", "dev", "--hostname", "0.0.0.0"]
