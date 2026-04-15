import { Form } from "react-router";

import type { TeamSummary } from "../../lib/dashboard.server";

type AddUserDialogProps = {
  isOpen: boolean;
  selectedTeam: TeamSummary | null;
  isSubmitting: boolean;
  errorMessage?: string;
  onClose: () => void;
  onSubmit: () => void;
};

export function AddUserDialog({
  isOpen,
  selectedTeam,
  isSubmitting,
  errorMessage,
  onClose,
  onSubmit,
}: AddUserDialogProps) {
  if (!isOpen || !selectedTeam) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-lg">
        <div>
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Add user</h2>
            <p className="mt-1 text-sm text-slate-500">
              Add a user to {selectedTeam.name} by email.
            </p>
          </div>
        </div>

        <Form method="post" className="mt-5 space-y-4" onSubmit={onSubmit}>
          <input type="hidden" name="intent" value="add-user" />
          <input type="hidden" name="teamId" value={selectedTeam.id} />

          <div>
            <label
              htmlFor="add-user-email"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              Email
            </label>
            <input
              id="add-user-email"
              type="email"
              name="email"
              required
              autoComplete="email"
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
            />
          </div>

          <div>
            <label
              htmlFor="add-user-role"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              Role
            </label>
            <select
              id="add-user-role"
              name="role"
              defaultValue="member"
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 outline-none focus:border-slate-500"
            >
              <option value="member">Member</option>
              <option value="tl">TL</option>
              <option value="pm">PM</option>
            </select>
          </div>

          {errorMessage ? (
            <p className="text-sm text-red-600">{errorMessage}</p>
          ) : null}

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Adding..." : "Add user"}
            </button>
          </div>
        </Form>
      </div>
    </div>
  );
}
