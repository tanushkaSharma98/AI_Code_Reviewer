# Use official Node image
FROM node:20-alpine as build

WORKDIR /app

# Add build tools for native modules on Alpine
RUN apk add --no-cache python3 make g++

# Install dependencies
COPY package.json ./
RUN npm install

# Copy source code and build
COPY . .
RUN npm run build

# Production image
FROM node:20-alpine as prod
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"] 