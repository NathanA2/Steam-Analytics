# Use a Node.js base image
FROM node:14

# Set the working directory in the container
WORKDIR /client

# Install dependencies
COPY package.json /client/
RUN npm install

# Bundle app source
COPY . /client

# Expose port and start application
EXPOSE 3000
CMD ["npm", "start"]