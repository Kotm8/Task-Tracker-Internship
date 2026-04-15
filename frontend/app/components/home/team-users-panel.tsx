import { Form } from "react-router";

import type { TeamMember, TeamSummary } from "../../lib/dashboard.server";

const rolePillClassNames: Record<string, string> = {
  pm: "bg-red-100 text-red-700",
  tl: "bg-green-100 text-green-700",
  member: "bg-blue-100 text-blue-700",
};

type TeamUsersPanelProps = {
  selectedTeam: TeamSummary | null;
  selectedTeamMembers: TeamMember[];
  currentUserId: string;
  canAddUser: boolean;
  canChangeRoles: boolean;
  submittingRoleUserId?: string;
  submittingRemoveUserId?: string;
  roleChangeError?: string;
  roleChangeErrorUserId?: string;
  removeUserError?: string;
  removeUserErrorUserId?: string;
  onOpenAddUser: () => void;
};

export function TeamUsersPanel({
  selectedTeam,
  selectedTeamMembers,
  currentUserId,
  canAddUser,
  canChangeRoles,
  submittingRoleUserId,
  submittingRemoveUserId,
  roleChangeError,
  roleChangeErrorUserId,
  removeUserError,
  removeUserErrorUserId,
  onOpenAddUser,
}: TeamUsersPanelProps) {
  return (
    <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            {selectedTeam ? selectedTeam.name : "No team selected"}
          </h2>
        </div>
        {selectedTeam ? (
          <span className="text-sm text-slate-500">
            {selectedTeamMembers.length} members
          </span>
        ) : null}
      </div>

      {selectedTeam ? (
        selectedTeamMembers.length > 0 ? (
          <div className="mt-4 space-y-3">
            {selectedTeamMembers.map((member) => (
              <div
                key={member.id}
                className="rounded-lg border border-slate-200 bg-slate-50 p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-sm font-semibold text-slate-900">
                        {member.username}
                      </p>
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${
                          rolePillClassNames[member.role]
                        }`}
                      >
                        {member.role}
                      </span>
                      {member.id === currentUserId ? (
                        <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white">
                          You
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-2 text-sm text-slate-500">{member.email}</p>
                  </div>

                  {canChangeRoles && selectedTeam ? (
                    <Form method="post">
                      <input type="hidden" name="intent" value="remove-user" />
                      <input type="hidden" name="teamId" value={selectedTeam.id} />
                      <input type="hidden" name="userId" value={member.id} />
                      <button
                        type="submit"
                        aria-label={`Remove ${member.username} from ${selectedTeam.name}`}
                        title="Remove user"
                        className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-lg leading-none text-slate-500 transition hover:border-red-200 hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={submittingRemoveUserId === member.id}
                      >
                        {submittingRemoveUserId === member.id ? "..." : "x"}
                      </button>
                    </Form>
                  ) : null}
                </div>

                {canChangeRoles && selectedTeam ? (
                  <Form method="post" className="mt-4 flex items-center gap-2">
                    <input type="hidden" name="intent" value="change-role" />
                    <input type="hidden" name="teamId" value={selectedTeam.id} />
                    <input type="hidden" name="userId" value={member.id} />
                    <select
                      name="role"
                      defaultValue={member.role}
                      className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-500"
                    >
                      <option value="member">Member</option>
                      <option value="tl">TL</option>
                      <option value="pm">PM</option>
                    </select>
                    <button
                      type="submit"
                      className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                      disabled={submittingRoleUserId === member.id}
                    >
                      {submittingRoleUserId === member.id ? "Saving..." : "Save"}
                    </button>
                  </Form>
                ) : null}

                {roleChangeErrorUserId === member.id && roleChangeError ? (
                  <p className="mt-3 text-sm text-red-600">{roleChangeError}</p>
                ) : null}

                {removeUserErrorUserId === member.id && removeUserError ? (
                  <p className="mt-3 text-sm text-red-600">{removeUserError}</p>
                ) : null}
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-sm text-slate-500">
            No users were found in this team.
          </p>
        )
      ) : (
        <p className="mt-4 text-sm text-slate-500">
          Pick a team to see its users.
        </p>
      )}

      {canAddUser ? (
        <div className="mt-6">
          <button
            type="button"
            onClick={onOpenAddUser}
            className="w-full rounded-lg bg-slate-900 px-4 py-3 text-sm font-medium text-white hover:bg-slate-800"
          >
            Add users
          </button>
        </div>
      ) : null}
    </aside>
  );
}
