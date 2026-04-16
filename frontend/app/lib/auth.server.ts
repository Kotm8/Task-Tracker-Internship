import { fetchGatewayWithRefresh } from "./gateway.server";
import type { GatewayRequestContext } from "./gateway.server";

export { appendSetCookieHeaders, fetchGateway } from "./gateway.server";

export type AuthenticatedUser = {
  id: string;
  username: string;
  email: string;
  role: "user" | "admin";
};

export async function getGatewayErrorMessage(
  response: Response,
  fallbackMessage: string,
) {
  try {
    const payload = await response.json();

    if (typeof payload?.detail === "string") {
      return payload.detail;
    }

    if (Array.isArray(payload?.detail)) {
      return payload.detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join(", ");
    }
  } catch {
    return fallbackMessage;
  }

  return fallbackMessage;
}

export async function getCurrentUser(request: Request | GatewayRequestContext) {
  const { response, headers } = await fetchGatewayWithRefresh(request, "/api/v1/users/whoami");

  if (response.status === 401) {
    return { user: null, headers };
  }

  if (!response.ok) {
    throw new Error("Failed to fetch the current user.");
  }

  return {
    user: (await response.json()) as AuthenticatedUser,
    headers,
  };
}
