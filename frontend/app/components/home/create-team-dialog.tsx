import { Form } from "react-router";

type CreateTeamDialogProps = {
  isOpen: boolean;
  isSubmitting: boolean;
  errorMessage?: string;
  onClose: () => void;
  onSubmit: () => void;
};

export function CreateTeamDialog({
  isOpen,
  isSubmitting,
  errorMessage,
  onClose,
  onSubmit,
}: CreateTeamDialogProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-lg">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Create team</h2>
          <p className="mt-1 text-sm text-slate-500">
            Create a new team and jump straight into it.
          </p>
        </div>

        <Form method="post" className="mt-5 space-y-4" onSubmit={onSubmit}>
          <input type="hidden" name="intent" value="create-team" />

          <div>
            <label
              htmlFor="create-team-name"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              Team name
            </label>
            <input
              id="create-team-name"
              type="text"
              name="name"
              required
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
            />
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
              {isSubmitting ? "Creating..." : "Create team"}
            </button>
          </div>
        </Form>
      </div>
    </div>
  );
}
