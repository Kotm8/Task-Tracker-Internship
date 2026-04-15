function getGatewayUrl() {
  const gatewayUrl = process.env.GATEWAY_URL;

  if (!gatewayUrl) {
    throw new Error("GATEWAY_URL is not set.");
  }

  return gatewayUrl;
}

export type GatewayRequestContext = {
  request: Request;
  cookieHeader: string | null;
  responseHeaders: Headers;
};

function isGatewayRequestContext(
  value: Request | GatewayRequestContext,
): value is GatewayRequestContext {
  return "responseHeaders" in value;
}

export function createGatewayRequestContext(request: Request): GatewayRequestContext {
  return {
    request,
    cookieHeader: request.headers.get("cookie"),
    responseHeaders: new Headers(),
  };
}

function getContext(source: Request | GatewayRequestContext) {
  return isGatewayRequestContext(source)
    ? source
    : createGatewayRequestContext(source);
}

function getForwardedHeaders(cookieHeader: string | null, headers?: HeadersInit) {
  const forwardedHeaders = new Headers(headers);

  if (cookieHeader && !forwardedHeaders.has("cookie")) {
    forwardedHeaders.set("cookie", cookieHeader);
  }

  return forwardedHeaders;
}

export function getSetCookieHeaders(response: Response) {
  if (typeof response.headers.getSetCookie === "function") {
    return response.headers.getSetCookie();
  }

  const header = response.headers.get("set-cookie");
  return header ? [header] : [];
}

export function appendSetCookieHeaders(headers: Headers, response: Response) {
  for (const cookie of getSetCookieHeaders(response)) {
    headers.append("set-cookie", cookie);
  }
}

function mergeCookies(
  cookieHeader: string | null,
  setCookieHeaders: string[],
) {
  const cookieMap = new Map<string, string>();

  if (cookieHeader) {
    for (const cookie of cookieHeader.split(";")) {
      const [name, ...rest] = cookie.trim().split("=");

      if (!name || rest.length === 0) {
        continue;
      }

      cookieMap.set(name, rest.join("="));
    }
  }

  for (const setCookie of setCookieHeaders) {
    const [cookiePair] = setCookie.split(";");
    const [name, ...rest] = cookiePair.trim().split("=");

    if (!name) {
      continue;
    }

    if (rest.length === 0 || (rest.length === 1 && rest[0] === "")) {
      cookieMap.delete(name);
      continue;
    }

    cookieMap.set(name, rest.join("="));
  }

  return Array.from(cookieMap.entries())
    .map(([name, value]) => `${name}=${value}`)
    .join("; ");
}

function syncResponseCookies(context: GatewayRequestContext, response: Response) {
  const cookies = getSetCookieHeaders(response);

  for (const cookie of cookies) {
    context.responseHeaders.append("set-cookie", cookie);
  }

  if (cookies.length > 0) {
    context.cookieHeader = mergeCookies(context.cookieHeader, cookies);
  }
}

export async function fetchGateway(
  request: Request,
  path: string,
  init?: RequestInit,
) {
  return await fetch(new URL(path, getGatewayUrl()), {
    ...init,
    headers: getForwardedHeaders(request.headers.get("cookie"), init?.headers),
  });
}

export async function fetchGatewayWithRefresh(
  source: Request | GatewayRequestContext,
  path: string,
  init?: RequestInit,
) {
  const context = getContext(source);
  const response = await fetch(new URL(path, getGatewayUrl()), {
    ...init,
    headers: getForwardedHeaders(context.cookieHeader, init?.headers),
  });

  if (response.status !== 401) {
    syncResponseCookies(context, response);
    return { response, headers: context.responseHeaders };
  }

  const refreshResponse = await fetch(new URL("/api/v1/auth/refresh", getGatewayUrl()), {
    method: "POST",
    headers: getForwardedHeaders(context.cookieHeader),
  });

  syncResponseCookies(context, refreshResponse);

  if (!refreshResponse.ok) {
    return { response, headers: context.responseHeaders };
  }

  const retryResponse = await fetch(new URL(path, getGatewayUrl()), {
    ...init,
    headers: getForwardedHeaders(context.cookieHeader, init?.headers),
  });

  syncResponseCookies(context, retryResponse);

  return { response: retryResponse, headers: context.responseHeaders };
}
