FROM nginx:alpine

# Copy the frontend file to a template location
COPY index.html /etc/nginx/templates/index.html.template

# Default backend URL (can be overridden by environment variable)
ENV BACKEND_URL=http://localhost:8080

# Use an entrypoint script to substitute the environment variable
# Nginx alpine comes with envsubst
CMD ["/bin/sh", "-c", "envsubst '${BACKEND_URL}' < /etc/nginx/templates/index.html.template > /usr/share/nginx/html/index.html && nginx -g 'daemon off;'"]

EXPOSE 80
