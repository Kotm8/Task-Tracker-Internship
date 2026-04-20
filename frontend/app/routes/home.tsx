import { useEffect, useRef, useState } from "react";
import type { Route } from "./+types/home";
import { Form, data, redirect, useActionData, useNavigation } from "react-router";

import {
  appendSetCookieHeaders,
  fetchGateway,
  getGatewayErrorMessage,
} from "../lib/auth.server";
import {
  AddUserDialog,
  CreateTeamDialog,
  TasksPanel,
  TeamsSidebar,
  TeamUsersPanel,
} from "../components/home";
import type {
  AuthenticatedDashboardData,
  TeamMember,
} from "../lib/dashboard.server";
import { getDashboardData } from "../lib/dashboard.server";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Home | TodoProject" },
    { name: "description", content: "TodoProject home page." },
  ];
}

export async function loader({ request }: Route.LoaderArgs) {
  const dashboardData = await getDashboardData(request);
  const { headers, ...payload } = dashboardData;

  if (!payload.user) {
    throw redirect("/login", { headers });
  }

  return data(payload as AuthenticatedDashboardData, { headers });
}

export async function action({ request }: Route.ActionArgs) {
  const formData = await request.formData();
  const intent = formData.get("intent");

  if (intent === "add-user") {
    const teamId = formData.get("teamId")?.toString() ?? "";
    const email = formData.get("email")?.toString().trim() ?? "";
    const role = formData.get("role")?.toString() ?? "";

    if (!teamId || !email || !["member", "tl", "pm"].includes(role)) {
      return data(
        {
          addUserError: "Email and role are required.",
          addUserTeamId: teamId,
        },
        { status: 400 },
      );
    }

    const response = await fetchGateway(request, `/api/v1/teams/${teamId}/members`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        email,
        role,
      }),
    });

    if (!response.ok) {
      return data(
        {
          addUserError: await getGatewayErrorMessage(
            response,
            "Unable to add this user to the team.",
          ),
          addUserTeamId: teamId,
        },
        { status: response.status },
      );
    }

    const currentUrl = new URL(request.url);
    throw redirect(`${currentUrl.pathname}${currentUrl.search}`);
  }

  if (intent === "change-role") {
    const teamId = formData.get("teamId")?.toString() ?? "";
    const userId = formData.get("userId")?.toString() ?? "";
    const role = formData.get("role")?.toString() ?? "";

    if (!teamId || !userId || !["member", "tl", "pm"].includes(role)) {
      return data(
        {
          roleChangeError: "Role is required.",
          roleChangeTeamId: teamId,
          roleChangeUserId: userId,
        },
        { status: 400 },
      );
    }

    const response = await fetchGateway(request, `/api/v1/teams/${teamId}/members/role`, {
      method: "PATCH",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,
        role,
      }),
    });

    if (!response.ok) {
      return data(
        {
          roleChangeError: await getGatewayErrorMessage(
            response,
            "Unable to change this user's team role.",
          ),
          roleChangeTeamId: teamId,
          roleChangeUserId: userId,
        },
        { status: response.status },
      );
    }

    const currentUrl = new URL(request.url);
    throw redirect(`${currentUrl.pathname}${currentUrl.search}`);
  }

  if (intent === "remove-user") {
    const teamId = formData.get("teamId")?.toString() ?? "";
    const userId = formData.get("userId")?.toString() ?? "";

    if (!teamId || !userId) {
      return data(
        {
          removeUserError: "User is required.",
          removeUserTeamId: teamId,
          removeUserUserId: userId,
        },
        { status: 400 },
      );
    }

    const response = await fetchGateway(
      request,
      `/api/v1/teams/${teamId}/members/${userId}`,
      {
        method: "DELETE",
      },
    );

    if (!response.ok) {
      return data(
        {
          removeUserError: await getGatewayErrorMessage(
            response,
            "Unable to remove this user from the team.",
          ),
          removeUserTeamId: teamId,
          removeUserUserId: userId,
        },
        { status: response.status },
      );
    }

    const currentUrl = new URL(request.url);
    throw redirect(`${currentUrl.pathname}${currentUrl.search}`);
  }

  if (intent === "create-task") {
    const teamId = formData.get("team_id")?.toString() ?? "";
    const title = formData.get("title")?.toString().trim() ?? "";
    const description = formData.get("description")?.toString().trim() ?? "";
    const assignedTo = formData.get("assigned_to")?.toString() ?? "";
    const deadline = formData.get("deadline")?.toString() ?? "";

    if (!teamId || !title || !assignedTo || !deadline) {
      return data(
        {
          createTaskError: "Title, assignee, and deadline are required.",
          createTaskTeamId: teamId,
          createTaskTitle: title,
          createTaskDescription: description,
          createTaskAssignedTo: assignedTo,
          createTaskDeadline: deadline,
        },
        { status: 400 },
      );
    }

    const parsedDeadline = new Date(deadline);

    if (Number.isNaN(parsedDeadline.getTime())) {
      return data(
        {
          createTaskError: "Deadline is invalid.",
          createTaskTeamId: teamId,
          createTaskTitle: title,
          createTaskDescription: description,
          createTaskAssignedTo: assignedTo,
          createTaskDeadline: deadline,
        },
        { status: 400 },
      );
    }

    const teamMembersResponse = await fetchGateway(
      request,
      `/api/v1/teams/${teamId}/members`,
    );

    if (!teamMembersResponse.ok) {
      return data(
        {
          createTaskError: await getGatewayErrorMessage(
            teamMembersResponse,
            "Unable to validate the selected assignee.",
          ),
          createTaskTeamId: teamId,
          createTaskTitle: title,
          createTaskDescription: description,
          createTaskAssignedTo: assignedTo,
          createTaskDeadline: deadline,
        },
        { status: teamMembersResponse.status },
      );
    }

    const teamMembers = (await teamMembersResponse.json()) as TeamMember[];

    if (!teamMembers.some((member) => member.id === assignedTo)) {
      return data(
        {
          createTaskError: "Pick a user who is currently in this team.",
          createTaskTeamId: teamId,
          createTaskTitle: title,
          createTaskDescription: description,
          createTaskAssignedTo: assignedTo,
          createTaskDeadline: deadline,
        },
        { status: 400 },
      );
    }

    const response = await fetchGateway(request, `/api/v1/tasks/${teamId}`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "Idempotency-Key": crypto.randomUUID(),
      },
      body: JSON.stringify({
        title,
        description: description || null,
        assigned_to: assignedTo,
        deadline: parsedDeadline.toISOString(),
      }),
    });

    if (!response.ok) {
      return data(
        {
          createTaskError: await getGatewayErrorMessage(
            response,
            "Unable to create this task.",
          ),
          createTaskTeamId: teamId,
          createTaskTitle: title,
          createTaskDescription: description,
          createTaskAssignedTo: assignedTo,
          createTaskDeadline: deadline,
        },
        { status: response.status },
      );
    }

    const currentUrl = new URL(request.url);
    currentUrl.searchParams.set("team", teamId);
    currentUrl.searchParams.set("tasks", "all");
    throw redirect(`${currentUrl.pathname}${currentUrl.search}`);
  }

  if (intent === "change-task-status") {
    const teamId = formData.get("team_id")?.toString() ?? "";
    const taskId = formData.get("task_id")?.toString() ?? "";
    const status = formData.get("status")?.toString() ?? "";

    if (!teamId || !taskId || !["todo", "in_progress", "review", "done", "cancelled"].includes(status)) {
      return data(
        {
          taskStatusChangeError: "A valid next status is required.",
          taskStatusChangeTeamId: teamId,
          taskStatusChangeTaskId: taskId,
        },
        { status: 400 },
      );
    }

    const response = await fetchGateway(request, `/api/v1/tasks/${teamId}`, {
      method: "PATCH",
      headers: {
        "content-type": "application/json",
        "Idempotency-Key": crypto.randomUUID(),
      },
      body: JSON.stringify({
        task_id: taskId,
        status,
      }),
    });

    if (!response.ok) {
      return data(
        {
          taskStatusChangeError: await getGatewayErrorMessage(
            response,
            "Unable to change this task status.",
          ),
          taskStatusChangeTeamId: teamId,
          taskStatusChangeTaskId: taskId,
        },
        { status: response.status },
      );
    }

    const currentUrl = new URL(request.url);
    throw redirect(`${currentUrl.pathname}${currentUrl.search}`);
  }

  if (intent === "delete-task") {
    const teamId = formData.get("team_id")?.toString() ?? "";
    const taskId = formData.get("task_id")?.toString() ?? "";

    if (!teamId || !taskId) {
      return data(
        {
          deleteTaskError: "Task is required.",
          deleteTaskTeamId: teamId,
          deleteTaskTaskId: taskId,
        },
        { status: 400 },
      );
    }

    const response = await fetchGateway(request, `/api/v1/tasks/${teamId}/task`, {
      method: "DELETE",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        task_id: taskId,
      }),
    });

    if (!response.ok) {
      return data(
        {
          deleteTaskError: await getGatewayErrorMessage(
            response,
            "Unable to delete this task.",
          ),
          deleteTaskTeamId: teamId,
          deleteTaskTaskId: taskId,
        },
        { status: response.status },
      );
    }

    const currentUrl = new URL(request.url);
    throw redirect(`${currentUrl.pathname}${currentUrl.search}`);
  }

  if (intent === "create-team") {
    const name = formData.get("name")?.toString().trim() ?? "";

    if (!name) {
      return data(
        {
          createTeamError: "Team name is required.",
        },
        { status: 400 },
      );
    }

    const response = await fetchGateway(request, "/api/v1/teams", {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({ name }),
    });

    if (!response.ok) {
      return data(
        {
          createTeamError: await getGatewayErrorMessage(
            response,
            "Unable to create this team.",
          ),
        },
        { status: response.status },
      );
    }

    const createdTeam = (await response.json()) as { id: string; name: string };
    const params = new URLSearchParams();
    params.set("team", createdTeam.id);
    params.set("scope", "all");

    throw redirect(`/?${params.toString()}`);
  }

  const response = await fetchGateway(request, "/api/v1/auth/logout", {
    method: "POST",
  });

  const headers = new Headers();
  appendSetCookieHeaders(headers, response);

  throw redirect("/login", { headers });
}

export default function Home({ loaderData }: Route.ComponentProps) {
  const actionData = useActionData<typeof action>();
  const navigation = useNavigation();
  const [isAddUserOpen, setIsAddUserOpen] = useState(false);
  const [isCreateTeamOpen, setIsCreateTeamOpen] = useState(false);
  const wasSubmittingAddUserRef = useRef(false);
  const wasSubmittingCreateTeamRef = useRef(false);
  const {
    user,
    teams,
    isViewingAllTeams,
    selectedTeam,
    selectedTeamMembers,
    tasks,
    canViewSelectedTeamTasks,
    isViewingAllTasks,
    taskFilters,
  } = loaderData;
  const teamMembersById = new Map(
    selectedTeamMembers.map((member) => [member.id, member]),
  );
  const isSubmittingAddUser =
    navigation.state === "submitting" &&
    navigation.formData?.get("intent") === "add-user";
  const isSubmittingCreateTeam =
    navigation.state === "submitting" &&
    navigation.formData?.get("intent") === "create-team";
  const isSubmittingCreateTask =
    navigation.state === "submitting" &&
    navigation.formData?.get("intent") === "create-task";
  const submittingRoleUserId =
    navigation.state === "submitting" &&
    navigation.formData?.get("intent") === "change-role"
      ? navigation.formData?.get("userId")?.toString()
      : undefined;
  const submittingRemoveUserId =
    navigation.state === "submitting" &&
    navigation.formData?.get("intent") === "remove-user"
      ? navigation.formData?.get("userId")?.toString()
      : undefined;
  const submittingTaskStatusId =
    navigation.state === "submitting" &&
    navigation.formData?.get("intent") === "change-task-status"
      ? navigation.formData?.get("taskId")?.toString()
      : undefined;
  const submittingDeleteTaskId =
    navigation.state === "submitting" &&
    navigation.formData?.get("intent") === "delete-task"
      ? navigation.formData?.get("taskId")?.toString()
      : undefined;
  const isAddUserDialogOpen = isAddUserOpen;
  const addUserTeamId =
    actionData && "addUserTeamId" in actionData ? actionData.addUserTeamId : undefined;
  const addUserError =
    actionData && "addUserError" in actionData ? actionData.addUserError : undefined;
  const createTeamError =
    actionData && "createTeamError" in actionData ? actionData.createTeamError : undefined;
  const roleChangeTeamId =
    actionData && "roleChangeTeamId" in actionData
      ? actionData.roleChangeTeamId
      : undefined;
  const roleChangeUserId =
    actionData && "roleChangeUserId" in actionData
      ? actionData.roleChangeUserId
      : undefined;
  const roleChangeError =
    actionData && "roleChangeError" in actionData
      ? actionData.roleChangeError
      : undefined;
  const removeUserTeamId =
    actionData && "removeUserTeamId" in actionData
      ? actionData.removeUserTeamId
      : undefined;
  const removeUserUserId =
    actionData && "removeUserUserId" in actionData
      ? actionData.removeUserUserId
      : undefined;
  const removeUserError =
    actionData && "removeUserError" in actionData
      ? actionData.removeUserError
      : undefined;
  const createTaskTeamId =
    actionData && "createTaskTeamId" in actionData
      ? actionData.createTaskTeamId
      : undefined;
  const createTaskTitle =
    actionData && "createTaskTitle" in actionData
      ? actionData.createTaskTitle
      : undefined;
  const createTaskDescription =
    actionData && "createTaskDescription" in actionData
      ? actionData.createTaskDescription
      : undefined;
  const createTaskAssignedTo =
    actionData && "createTaskAssignedTo" in actionData
      ? actionData.createTaskAssignedTo
      : undefined;
  const createTaskDeadline =
    actionData && "createTaskDeadline" in actionData
      ? actionData.createTaskDeadline
      : undefined;
  const createTaskError =
    actionData && "createTaskError" in actionData
      ? actionData.createTaskError
      : undefined;
  const taskStatusChangeTeamId =
    actionData && "taskStatusChangeTeamId" in actionData
      ? actionData.taskStatusChangeTeamId
      : undefined;
  const taskStatusChangeTaskId =
    actionData && "taskStatusChangeTaskId" in actionData
      ? actionData.taskStatusChangeTaskId
      : undefined;
  const taskStatusChangeError =
    actionData && "taskStatusChangeError" in actionData
      ? actionData.taskStatusChangeError
      : undefined;
  const deleteTaskTeamId =
    actionData && "deleteTaskTeamId" in actionData
      ? actionData.deleteTaskTeamId
      : undefined;
  const deleteTaskTaskId =
    actionData && "deleteTaskTaskId" in actionData
      ? actionData.deleteTaskTaskId
      : undefined;
  const deleteTaskError =
    actionData && "deleteTaskError" in actionData
      ? actionData.deleteTaskError
      : undefined;
  const buildTeamUrl = (teamId: string) => {
    const params = new URLSearchParams();

    params.set("team", teamId);

    if (isViewingAllTeams) {
      params.set("scope", "all");
    }

    if (isViewingAllTasks) {
      params.set("tasks", "all");
    }

    if (taskFilters.status) {
      params.set("status", taskFilters.status);
    }

    if (taskFilters.deadline) {
      params.set("deadline", taskFilters.deadline);
    }

    if (taskFilters.sort) {
      params.set("sort", taskFilters.sort);
    }

    if (taskFilters.direction !== "asc") {
      params.set("direction", taskFilters.direction);
    }

    return `/?${params.toString()}`;
  };

  const buildTasksToggleUrl = () => {
    if (!selectedTeam) {
      return "/";
    }

    const params = new URLSearchParams();
    params.set("team", selectedTeam.id);

    if (isViewingAllTeams) {
      params.set("scope", "all");
    }

    if (!isViewingAllTasks) {
      params.set("tasks", "all");
    }

    if (taskFilters.status) {
      params.set("status", taskFilters.status);
    }

    if (taskFilters.deadline) {
      params.set("deadline", taskFilters.deadline);
    }

    if (taskFilters.sort) {
      params.set("sort", taskFilters.sort);
    }

    if (taskFilters.direction !== "asc") {
      params.set("direction", taskFilters.direction);
    }

    return `/?${params.toString()}`;
  };

  const buildClearTaskFiltersUrl = () => {
    const params = new URLSearchParams();

    if (selectedTeam) {
      params.set("team", selectedTeam.id);
    }

    if (isViewingAllTeams) {
      params.set("scope", "all");
    }

    if (isViewingAllTasks) {
      params.set("tasks", "all");
    }

    return params.size > 0 ? `/?${params.toString()}` : "/";
  };

  const assigneeNamesById = new Map(
    selectedTeamMembers.map((member) => [member.id, member.username]),
  );

  useEffect(() => {
    if (addUserTeamId === selectedTeam?.id && Boolean(addUserError)) {
      setIsAddUserOpen(true);
    }
  }, [addUserError, addUserTeamId, selectedTeam?.id]);

  useEffect(() => {
    if (createTeamError) {
      setIsCreateTeamOpen(true);
    }
  }, [createTeamError]);

  useEffect(() => {
    if (isSubmittingAddUser) {
      wasSubmittingAddUserRef.current = true;
      return;
    }

    if (wasSubmittingAddUserRef.current) {
      if (!addUserError) {
        setIsAddUserOpen(false);
      }

      wasSubmittingAddUserRef.current = false;
    }
  }, [addUserError, isSubmittingAddUser]);

  useEffect(() => {
    if (isSubmittingCreateTeam) {
      wasSubmittingCreateTeamRef.current = true;
      return;
    }

    if (wasSubmittingCreateTeamRef.current) {
      if (!createTeamError) {
        setIsCreateTeamOpen(false);
      }

      wasSubmittingCreateTeamRef.current = false;
    }
  }, [createTeamError, isSubmittingCreateTeam]);

  return (
    <main className="min-h-screen">
      <header className="w-full border-b border-slate-200 bg-white shadow-sm">
        <div className="flex w-full items-center justify-between gap-4 px-6 py-5">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold text-slate-900">
              Hi, {user.username}
            </h1>
            {user.role === "admin" ? (
              <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-red-700">
                Admin
              </span>
            ) : null}
          </div>

          <Form method="post">
            <button
              type="submit"
              name="intent"
              value="logout"
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
            >
              Logout
            </button>
          </Form>
        </div>
      </header>

      <div className="grid gap-6 px-6 py-6 lg:grid-cols-[260px_minmax(0,1fr)_340px]">
        <TeamsSidebar
          teams={teams}
          userRole={user.role}
          isViewingAllTeams={isViewingAllTeams}
          selectedTeamId={selectedTeam?.id}
          buildTeamUrl={buildTeamUrl}
          canCreateTeam={user.role === "admin"}
          onOpenCreateTeam={() => setIsCreateTeamOpen(true)}
        />

        <TasksPanel
          selectedTeam={selectedTeam}
          tasks={tasks}
          canViewSelectedTeamTasks={canViewSelectedTeamTasks}
          canCreateTask={selectedTeam?.role === "pm"}
          canDeleteTask={selectedTeam?.role === "pm"}
          isViewingAllTasks={isViewingAllTasks}
          isViewingAllTeams={isViewingAllTeams}
          teamMembers={selectedTeamMembers}
          assigneeNamesById={assigneeNamesById}
          buildTasksToggleUrl={buildTasksToggleUrl}
          clearTaskFiltersUrl={buildClearTaskFiltersUrl()}
          taskFilters={taskFilters}
          currentUserId={user.id}
          isSubmittingCreateTask={isSubmittingCreateTask}
          createTaskError={createTaskTeamId === selectedTeam?.id ? createTaskError : undefined}
          createTaskValues={
            createTaskTeamId === selectedTeam?.id
              ? {
                  title: createTaskTitle,
                  description: createTaskDescription,
                  assignedTo: createTaskAssignedTo,
                  deadline: createTaskDeadline,
                }
              : undefined
          }
          submittingTaskStatusId={submittingTaskStatusId}
          taskStatusChangeError={
            taskStatusChangeTeamId === selectedTeam?.id ? taskStatusChangeError : undefined
          }
          taskStatusChangeErrorTaskId={
            taskStatusChangeTeamId === selectedTeam?.id ? taskStatusChangeTaskId : undefined
          }
          submittingDeleteTaskId={submittingDeleteTaskId}
          deleteTaskError={deleteTaskTeamId === selectedTeam?.id ? deleteTaskError : undefined}
          deleteTaskErrorTaskId={
            deleteTaskTeamId === selectedTeam?.id ? deleteTaskTaskId : undefined
          }
        />

        <TeamUsersPanel
          selectedTeam={selectedTeam}
          selectedTeamMembers={selectedTeamMembers}
          currentUserId={user.id}
          canAddUser={user.role === "admin" && Boolean(selectedTeam)}
          canChangeRoles={user.role === "admin"}
          submittingRoleUserId={submittingRoleUserId}
          submittingRemoveUserId={submittingRemoveUserId}
          roleChangeError={roleChangeTeamId === selectedTeam?.id ? roleChangeError : undefined}
          roleChangeErrorUserId={
            roleChangeTeamId === selectedTeam?.id ? roleChangeUserId : undefined
          }
          removeUserError={removeUserTeamId === selectedTeam?.id ? removeUserError : undefined}
          removeUserErrorUserId={
            removeUserTeamId === selectedTeam?.id ? removeUserUserId : undefined
          }
          onOpenAddUser={() => setIsAddUserOpen(true)}
        />
      </div>

      <AddUserDialog
        isOpen={user.role === "admin" && isAddUserDialogOpen}
        selectedTeam={selectedTeam}
        isSubmitting={isSubmittingAddUser}
        errorMessage={addUserTeamId === selectedTeam?.id ? addUserError : undefined}
        onSubmit={() => setIsAddUserOpen(false)}
        onClose={() => setIsAddUserOpen(false)}
      />

      <CreateTeamDialog
        isOpen={user.role === "admin" && isCreateTeamOpen}
        isSubmitting={isSubmittingCreateTeam}
        errorMessage={createTeamError}
        onSubmit={() => setIsCreateTeamOpen(false)}
        onClose={() => setIsCreateTeamOpen(false)}
      />
    </main>
  );
}
