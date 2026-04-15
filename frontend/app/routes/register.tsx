import {
  Form,
  Link,
  data,
  redirect,
  useActionData,
  useNavigation,
} from "react-router";

import type { Route } from "./+types/register";
import {
  appendSetCookieHeaders,
  fetchGateway,
  getCurrentUser,
  getGatewayErrorMessage,
} from "../lib/auth.server";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Register | TodoProject" },
    { name: "description", content: "Register page for TodoProject." },
  ];
}

export async function loader({ request }: Route.LoaderArgs) {
  const { user, headers } = await getCurrentUser(request);

  if (user) {
    throw redirect("/", { headers });
  }

  return null;
}

export async function action({ request }: Route.ActionArgs) {
  const formData = await request.formData();
  const username = formData.get("username")?.toString().trim() ?? "";
  const email = formData.get("email")?.toString().trim() ?? "";
  const password = formData.get("password")?.toString() ?? "";

  if (!username || !email || !password) {
    return data(
      { error: "Username, email, and password are required." },
      { status: 400 },
    );
  }

  const response = await fetchGateway(request, "/api/v1/auth/register", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({ username, email, password }),
  });

  if (!response.ok) {
    return data(
      {
        error: await getGatewayErrorMessage(
          response,
          "Unable to create your account.",
        ),
      },
      { status: response.status },
    );
  }

  const headers = new Headers();
  appendSetCookieHeaders(headers, response);

  throw redirect("/", { headers });
}

export default function Register() {
  const actionData = useActionData<typeof action>();
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Register</h1>
        <Form method="post" className="mt-6 space-y-4">
          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              name="email"
              autoComplete="username"
              inputMode="email"
              required
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
            />
          </div>

          <div>
            <label htmlFor="username" className="mb-1 block text-sm font-medium text-slate-700">
              Username
            </label>
            <input
              id="username"
              type="text"
              name="username"
              autoComplete="nickname"
              required
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              name="password"
              autoComplete="new-password"
              required
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
            />
          </div>

          {actionData?.error ? (
            <p className="text-sm text-red-600">{actionData.error}</p>
          ) : null}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isSubmitting ? "Creating account..." : "Register"}
          </button>
        </Form>

        <p className="mt-4 text-sm text-slate-600">
          Already have an account?{" "}
          <Link to="/login" className="text-blue-600 hover:underline">
            Login
          </Link>
        </p>
      </div>
    </main>
  );
}
