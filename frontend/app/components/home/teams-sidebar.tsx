import { Link } from "react-router";

import type { AuthenticatedUser } from "../../lib/auth.server";
import type { TeamSummary } from "../../lib/dashboard.server";

type TeamsSidebarProps = {
  teams: TeamSummary[];
  userRole: AuthenticatedUser["role"];
  isViewingAllTeams: boolean;
  selectedTeamId?: string;
  buildTeamUrl: (teamId: string) => string;
  canCreateTeam: boolean;
  onOpenCreateTeam: () => void;
};

export function TeamsSidebar({
  teams,
  userRole,
  isViewingAllTeams,
  selectedTeamId,
  buildTeamUrl,
  canCreateTeam,
  onOpenCreateTeam,
}: TeamsSidebarProps) {
  return (
    <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-slate-900">Teams</h2>
          <span className="text-sm text-slate-500">{teams.length} total</span>
        </div>
        {userRole === "admin" ? (
          <Link
            to={isViewingAllTeams ? "/" : "/?scope=all"}
            className={`shrink-0 whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${
              isViewingAllTeams
                ? "bg-slate-900 text-white"
                : "bg-slate-100 text-slate-700"
            }`}
          >
            {isViewingAllTeams ? "All teams" : "Your teams"}
          </Link>
        ) : null}
      </div>

      {teams.length > 0 ? (
        <div className="mt-4 space-y-3">
          {teams.map((team) => {
            const isActive = selectedTeamId === team.id;

            return (
              <Link
                key={team.id}
                to={buildTeamUrl(team.id)}
                className={`block rounded-lg border p-4 transition ${
                  isActive
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-slate-200 bg-slate-50 text-slate-900 hover:bg-slate-100"
                }`}
              >
                <p className="text-base font-semibold">{team.name}</p>
                <p
                  className={`mt-2 text-sm ${
                    isActive ? "text-slate-200" : "text-slate-500"
                  }`}
                >
                  {team.role ? `Role: ${team.role.toUpperCase()}` : "Admin view"}
                </p>
              </Link>
            );
          })}
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">
          You are not assigned to any teams yet.
        </p>
      )}

      {canCreateTeam ? (
        <div className="mt-6">
          <button
            type="button"
            onClick={onOpenCreateTeam}
            className="w-full rounded-lg bg-slate-900 px-4 py-3 text-sm font-medium text-white hover:bg-slate-800"
          >
            Create team
          </button>
        </div>
      ) : null}
    </aside>
  );
}
