import type { AuthenticatedUser } from "./auth.server";
import { getCurrentUser } from "./auth.server";
import {
  createGatewayRequestContext,
  fetchGatewayWithRefresh,
} from "./gateway.server";

export type TeamRole = "member" | "pm" | "tl";

export type TeamSummary = {
  id: string;
  name: string;
  role: TeamRole | null;
};

export type TeamMember = {
  id: string;
  username: string;
  email: string;
  role: TeamRole;
};

export type TaskResponse = {
  id: string;
  team_id: string;
  title: string;
  description: string | null;
  status: "todo" | "in_progress" | "review" | "done" | "cancelled";
  created_by: string;
  assigned_to: string;
  deadline: string;
  created_at: string;
  updated_at: string;
};

export type TaskDeadlineFilter = "before" | "after";
export type TaskSortField = "deadline" | "created_at" | "updated_at";
export type TaskSortDirection = "asc" | "desc";

export type TaskFilters = {
  status?: TaskResponse["status"];
  deadline?: TaskDeadlineFilter;
  sort?: TaskSortField;
  direction: TaskSortDirection;
};

type PaginatedTaskResponse = {
  items: TaskResponse[];
  page: number;
  limit: number;
  total: number;
};

export type DashboardData = {
  user: AuthenticatedUser | null;
  teams: TeamSummary[];
  isViewingAllTeams: boolean;
  selectedTeam: TeamSummary | null;
  selectedTeamMembers: TeamMember[];
  tasks: TaskResponse[];
  canViewSelectedTeamTasks: boolean;
  isViewingAllTasks: boolean;
  taskFilters: TaskFilters;
  headers: Headers;
};

export type AuthenticatedDashboardData = Omit<DashboardData, "user"> & {
  user: AuthenticatedUser;
};

async function readJson<T>(
  context: ReturnType<typeof createGatewayRequestContext>,
  path: string,
  errorMessage: string,
) {
  const { response } = await fetchGatewayWithRefresh(context, path);

  if (!response.ok) {
    throw new Error(errorMessage);
  }

  return (await response.json()) as T;
}

export async function getDashboardData(request: Request): Promise<DashboardData> {
  const context = createGatewayRequestContext(request);
  const currentUser = await getCurrentUser(context);

  if (!currentUser.user) {
    return {
      user: null,
      teams: [],
      isViewingAllTeams: false,
      selectedTeam: null,
      selectedTeamMembers: [],
      tasks: [],
      canViewSelectedTeamTasks: false,
      isViewingAllTasks: false,
      taskFilters: { direction: "asc" },
      headers: context.responseHeaders,
    };
  }

  const currentUrl = new URL(request.url);
  const isViewingAllTeams =
    currentUser.user.role === "admin" &&
    currentUrl.searchParams.get("scope") === "all";
  const userTeams = await readJson<TeamSummary[]>(
    context,
    "/api/v1/teams",
    "Failed to load teams.",
  );
  const userTeamRoles = new Map(userTeams.map((team) => [team.id, team.role]));
  const teams = isViewingAllTeams
    ? (
        await readJson<Array<{ id: string; name: string }>>(
          context,
          "/api/v1/teams/all",
          "Failed to load all teams.",
        )
      ).map((team) => ({
        ...team,
        role: userTeamRoles.get(team.id) ?? null,
      }))
    : userTeams;

  const teamIdFromQuery = currentUrl.searchParams.get("team");
  const status = currentUrl.searchParams.get("status");
  const deadline = currentUrl.searchParams.get("deadline");
  const sort = currentUrl.searchParams.get("sort");
  const direction = currentUrl.searchParams.get("direction");
  const taskFilters: TaskFilters = {
    status:
      status && ["todo", "in_progress", "review", "done", "cancelled"].includes(status)
        ? (status as TaskResponse["status"])
        : undefined,
    deadline:
      deadline && ["before", "after"].includes(deadline)
        ? (deadline as TaskDeadlineFilter)
        : undefined,
    sort:
      sort && ["deadline", "created_at", "updated_at"].includes(sort)
        ? (sort as TaskSortField)
        : undefined,
    direction:
      direction === "desc" ? "desc" : "asc",
  };
  const selectedTeam =
    teams.find((team) => team.id === teamIdFromQuery) ?? teams[0] ?? null;

  if (!selectedTeam) {
    return {
      user: currentUser.user,
      teams,
      isViewingAllTeams,
      selectedTeam: null,
      selectedTeamMembers: [],
      tasks: [],
      canViewSelectedTeamTasks: false,
      isViewingAllTasks: false,
      taskFilters,
      headers: context.responseHeaders,
    };
  }

  const selectedTeamMembers = await readJson<TeamMember[]>(
    context,
    `/api/v1/teams/${selectedTeam.id}/members`,
    "Failed to load team members.",
  );

  const canViewSelectedTeamTasks =
    selectedTeam.role !== null || !isViewingAllTeams;
  const isViewingAllTasks =
    selectedTeam.role === "pm" && currentUrl.searchParams.get("tasks") === "all";
  let tasks: TaskResponse[] = [];

  if (canViewSelectedTeamTasks) {
    const taskQuery = new URLSearchParams({
      limit: "50",
      page: "1",
      direction: taskFilters.direction,
    });

    if (taskFilters.status) {
      taskQuery.set("status", taskFilters.status);
    }

    if (taskFilters.deadline) {
      taskQuery.set("deadline", taskFilters.deadline);
    }

    if (taskFilters.sort) {
      taskQuery.set("sort", taskFilters.sort);
    }

    const paginatedTasks = await readJson<PaginatedTaskResponse>(
      context,
      isViewingAllTasks
        ? `/api/v1/tasks/${selectedTeam.id}?${taskQuery.toString()}`
        : `/api/v1/tasks/${selectedTeam.id}/my?${taskQuery.toString()}`,
      isViewingAllTasks
        ? "Failed to load team tasks."
        : "Failed to load assigned tasks.",
    );
    tasks = paginatedTasks.items;
  }

  return {
    user: currentUser.user,
    teams,
    isViewingAllTeams,
    selectedTeam,
    selectedTeamMembers,
    tasks,
    canViewSelectedTeamTasks,
    isViewingAllTasks,
    taskFilters,
    headers: context.responseHeaders,
  };
}
