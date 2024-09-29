# Use Node.js as the base image
FROM node:18-alpine AS builder

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json from card-app folder
COPY card-app/package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the application code from card-app folder
COPY card-app .

# Build the Next.js application
RUN npm run build

# Start a new stage for a smaller production image
FROM node:18-alpine AS runner

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

WORKDIR /app

# Copy necessary files from the builder stage
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules

# Set environment variables
# ARG NEXT_PUBLIC_API_URL
# ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Expose the port the app runs on
EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Start the application
CMD ["npm", "start"]