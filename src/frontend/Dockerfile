# Use an official Node runtime as a parent image
FROM node:18-alpine

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the React app
RUN npm run build

# Serve the built app (using a simple static server, e.g., serve)
# You might need to install 'serve' globally or as a dev dependency
RUN npm install -g serve \
    && adduser -D appuser
EXPOSE 3000

# Health check to ensure the frontend is serving content
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:3000/ >/dev/null || exit 1

USER appuser

CMD ["serve", "-s", "build", "-l", "3000"]
