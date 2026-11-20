#!/bin/sh

# Create runtime config with environment variables.
#
# If REACT_APP_CMF_API_URL is set, use it verbatim (needed when the API is
# served from a different host than the UI). If unset, emit the JavaScript
# expression `window.location.origin` so the browser calls the API against
# whatever origin it loaded the UI from — HTTP or HTTPS, automatically, with
# no mixed-content blocking.
if [ -n "${REACT_APP_CMF_API_URL:-}" ]; then
  API_URL_VALUE="\"${REACT_APP_CMF_API_URL}\""
else
  API_URL_VALUE="window.location.origin"
fi

cat > /usr/share/nginx/html/runtime-config.js <<EOF
window.RUNTIME_CONFIG = {
  REACT_APP_CMF_API_URL: ${API_URL_VALUE}
};
EOF

echo "Generated runtime configuration"
cat /usr/share/nginx/html/runtime-config.js

# Start nginx
exec nginx -g 'daemon off;'
