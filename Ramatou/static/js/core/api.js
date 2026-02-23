export async function api(url, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  const isFormData = options.body instanceof FormData;
  const headers = { ...(options.headers || {}) };
  if (!isFormData) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method) && csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  const response = await fetch(url, {
    headers,
    ...options,
  });

  if (!response.ok) {
    let message = "Erreur serveur.";
    try {
      const body = await response.json();
      message = body.error || body.message || message;
    } catch (_e) {
      // Ignore parse errors and keep default.
    }
    throw new Error(message);
  }
  return response.json();
}
