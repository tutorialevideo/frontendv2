# Frontend Dockerfile - Multi-stage build for Production
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies with legacy peer deps to avoid conflicts
RUN yarn install --network-timeout 100000 || npm install --legacy-peer-deps

# Copy source code
COPY . .

# Set production env - empty BACKEND_URL means use relative /api paths
ENV REACT_APP_BACKEND_URL=""
ENV CI=false

# Build the app (uses craco)
RUN yarn build || npm run build

# Production stage with Nginx
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
