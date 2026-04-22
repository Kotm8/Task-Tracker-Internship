import { useEffect, useRef, useState } from "react";
import { Form, Link } from "react-router";

import type {
  TaskResponse,
  TaskFilters,
  TeamMember,
  TeamSummary,
} from "../../lib/dashboard.server";

const nextStatusesByCurrentStatus: Record<TaskResponse["status"], TaskResponse["status"][]> = {
  todo: ["in_progress", "cancelled"],
  in_progress: ["todo", "review", "cancelled"],
  review: ["in_progress", "done", "cancelled"],
  done: ["review"],
  cancelled: ["todo", "in_progress", "review"],
};

const statusPillClassNames: Record<TaskResponse["status"], string> = {
  todo: "bg-red-100 text-red-700",
  in_progress: "bg-orange-100 text-orange-700",
  review: "bg-yellow-100 text-yellow-700",
  done: "bg-green-100 text-green-700",
  cancelled: "bg-red-100 text-red-700",
};

function formatStatusLabel(status: TaskResponse["status"]) {
  return status.replace("_", " ");
}

function formatDeadline(deadline: string) {
  const date = new Date(deadline);

  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");

  return `${day}-${month} ${hours}:${minutes}`;
}

function formatDateTimeLocalValue(value?: string) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");

  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function formatTimeLeft(deadline: string) {
  const target = new Date(deadline).getTime();
  const now = Date.now();
  const diff = target - now;

  if (diff <= 0) {
    return "expired";
  }

  const totalMinutes = Math.floor(diff / (1000 * 60));
  const totalHours = Math.floor(diff / (1000 * 60 * 60));
  const totalDays = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (totalDays >= 1) {
    return totalDays === 1 ? "1 day left" : `${totalDays} days left`;
  }

  if (totalHours >= 1) {
    return totalHours === 1 ? "1 hour left" : `${totalHours} hours left`;
  }

  if (totalMinutes >= 1) {
    return totalMinutes === 1 ? "1 minute left" : `${totalMinutes} minutes left`;
  }

  return "less than a minute left";
}

type TasksPanelProps = {
  selectedTeam: TeamSummary | null;
  tasks: TaskResponse[];
  canViewSelectedTeamTasks: boolean;
  canCreateTask: boolean;
  canDeleteTask: boolean;
  canExportAudit: boolean;
  isViewingAllTasks: boolean;
  isViewingAllTeams: boolean;
  teamMembers: TeamMember[];
  assigneeNamesById: Map<string, string>;
  buildTasksToggleUrl: () => string;
  clearTaskFiltersUrl: string;
  taskFilters: TaskFilters;
  currentUserId: string;
  isSubmittingCreateTask: boolean;
  createTaskError?: string;
  createTaskValues?: {
    title?: string;
    description?: string;
    assignedTo?: string;
    deadline?: string;
  };
  submittingTaskStatusId?: string;
  taskStatusChangeError?: string;
  taskStatusChangeErrorTaskId?: string;
  submittingDeleteTaskId?: string;
  deleteTaskError?: string;
  deleteTaskErrorTaskId?: string;
};

export function TasksPanel({
  selectedTeam,
  tasks,
  canViewSelectedTeamTasks,
  canCreateTask,
  canDeleteTask,
  canExportAudit,
  isViewingAllTasks,
  isViewingAllTeams,
  teamMembers,
  assigneeNamesById,
  buildTasksToggleUrl,
  clearTaskFiltersUrl,
  taskFilters,
  currentUserId,
  isSubmittingCreateTask,
  createTaskError,
  createTaskValues,
  submittingTaskStatusId,
  taskStatusChangeError,
  taskStatusChangeErrorTaskId,
  submittingDeleteTaskId,
  deleteTaskError,
  deleteTaskErrorTaskId,
}: TasksPanelProps) {
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false);
  const [isCreateTaskDismissed, setIsCreateTaskDismissed] = useState(false);
  const [taskPendingDelete, setTaskPendingDelete] = useState<TaskResponse | null>(null);
  const [isAuditExportConfirmOpen, setIsAuditExportConfirmOpen] = useState(false);
  const wasSubmittingCreateTaskRef = useRef(false);
  const wasSubmittingDeleteTaskRef = useRef(false);

  useEffect(() => {
    if (createTaskError) {
      setIsCreateTaskOpen(true);
      setIsCreateTaskDismissed(false);
    }
  }, [createTaskError, createTaskValues]);

  useEffect(() => {
    setIsCreateTaskOpen(false);
    setIsCreateTaskDismissed(false);
    setTaskPendingDelete(null);
    setIsAuditExportConfirmOpen(false);
  }, [selectedTeam?.id]);

  useEffect(() => {
    if (isSubmittingCreateTask) {
      wasSubmittingCreateTaskRef.current = true;
      return;
    }

    if (wasSubmittingCreateTaskRef.current) {
      if (!createTaskError) {
        setIsCreateTaskOpen(false);
        setIsCreateTaskDismissed(false);
      }

      wasSubmittingCreateTaskRef.current = false;
    }
  }, [createTaskError, isSubmittingCreateTask]);

  useEffect(() => {
    if (!deleteTaskErrorTaskId || !deleteTaskError) {
      return;
    }

    const failedTask = tasks.find((task) => task.id === deleteTaskErrorTaskId);

    if (failedTask) {
      setTaskPendingDelete(failedTask);
    }
  }, [tasks, deleteTaskError, deleteTaskErrorTaskId]);

  useEffect(() => {
    if (submittingDeleteTaskId) {
      wasSubmittingDeleteTaskRef.current = true;
      return;
    }

    if (wasSubmittingDeleteTaskRef.current) {
      if (!deleteTaskError) {
        setTaskPendingDelete(null);
      }

      wasSubmittingDeleteTaskRef.current = false;
    }
  }, [deleteTaskError, submittingDeleteTaskId]);

  const createTaskFormValues = isCreateTaskDismissed ? undefined : createTaskValues;
  const visibleCreateTaskError = isCreateTaskDismissed ? undefined : createTaskError;
  const isSubmittingDeleteTask =
    taskPendingDelete !== null && submittingDeleteTaskId === taskPendingDelete.id;
  const visibleDeleteTaskError =
    taskPendingDelete !== null && deleteTaskErrorTaskId === taskPendingDelete.id
      ? deleteTaskError
      : undefined;

  function handleCloseCreateTask() {
    setIsCreateTaskDismissed(true);
    setIsCreateTaskOpen(false);
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            {selectedTeam ? `${selectedTeam.name} tasks` : "Your tasks"}
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            {selectedTeam?.role === "pm" && isViewingAllTasks
              ? "All tasks in the selected team."
              : "Tasks assigned to you in the selected team."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {selectedTeam?.role === "pm" ? (
            <Link
              to={buildTasksToggleUrl()}
              className={`shrink-0 whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${
                isViewingAllTasks
                  ? "bg-slate-900 text-white"
                  : "bg-slate-100 text-slate-700"
              }`}
            >
              {isViewingAllTasks ? "All tasks" : "Your tasks"}
            </Link>
          ) : null}
          {selectedTeam && canExportAudit ? (
            <button
              type="button"
              onClick={() => setIsAuditExportConfirmOpen(true)}
              className="shrink-0 whitespace-nowrap rounded-full border border-slate-300 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700 transition hover:bg-slate-100"
            >
              Export audit
            </button>
          ) : null}
          {selectedTeam && canViewSelectedTeamTasks ? (
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
              {tasks.length} {isViewingAllTasks ? "total" : "assigned"}
            </span>
          ) : null}
        </div>
      </div>

      {selectedTeam && canCreateTask ? (
        isCreateTaskOpen ? (
          <Form method="post" className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <input type="hidden" name="intent" value="create-task" />
            <input type="hidden" name="team_id" value={selectedTeam.id} />

            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Create a task</h3>
                <p className="mt-1 text-sm text-slate-500">
                  Assign it to someone who is currently in {selectedTeam.name}.
                </p>
              </div>
              <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
                PM only
              </span>
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <label className="text-sm">
                <span className="mb-1 block font-medium text-slate-700">Title</span>
                <input
                  type="text"
                  name="title"
                  required
                  defaultValue={createTaskFormValues?.title ?? ""}
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 outline-none focus:border-slate-500"
                  placeholder="Prepare sprint summary"
                />
              </label>

              <label className="text-sm">
                <span className="mb-1 block font-medium text-slate-700">Assign to</span>
                <select
                  name="assigned_to"
                  required
                  defaultValue={createTaskFormValues?.assignedTo ?? teamMembers[0]?.id ?? ""}
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 outline-none focus:border-slate-500"
                >
                  {teamMembers.map((member) => (
                    <option key={member.id} value={member.id}>
                      {member.username} ({member.role})
                    </option>
                  ))}
                </select>
              </label>

              <label className="text-sm md:col-span-2">
                <span className="mb-1 block font-medium text-slate-700">Description</span>
                <textarea
                  name="description"
                  rows={3}
                  defaultValue={createTaskFormValues?.description ?? ""}
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 outline-none focus:border-slate-500"
                  placeholder="Add any details the assignee needs."
                />
              </label>

              <label className="text-sm">
                <span className="mb-1 block font-medium text-slate-700">Deadline</span>
                <input
                  type="datetime-local"
                  name="deadline"
                  required
                  defaultValue={formatDateTimeLocalValue(createTaskFormValues?.deadline)}
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 outline-none focus:border-slate-500"
                />
              </label>
            </div>

            <div className="mt-4 flex items-center justify-between gap-3">
              {visibleCreateTaskError ? (
                <p className="text-sm text-red-600">{visibleCreateTaskError}</p>
              ) : (
                <span className="text-sm text-slate-500">
                  New tasks open in <span className="font-medium text-slate-700">todo</span>.
                </span>
              )}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleCloseCreateTask}
                  className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
                  disabled={isSubmittingCreateTask}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                  disabled={isSubmittingCreateTask || teamMembers.length === 0}
                >
                  {isSubmittingCreateTask ? "Creating..." : "Add task"}
                </button>
              </div>
            </div>
          </Form>
        ) : (
          <div className="mt-4">
            <button
              type="button"
              onClick={() => setIsCreateTaskOpen(true)}
              className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
            >
              Add task
            </button>
          </div>
        )
      ) : null}

      <Form method="get" className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
        {selectedTeam ? <input type="hidden" name="team" value={selectedTeam.id} /> : null}
        {isViewingAllTeams ? <input type="hidden" name="scope" value="all" /> : null}
        {isViewingAllTasks ? <input type="hidden" name="tasks" value="all" /> : null}

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <label className="text-sm">
            <span className="mb-1 block font-medium text-slate-700">Status</span>
            <select
              name="status"
              defaultValue={taskFilters.status ?? ""}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 outline-none focus:border-slate-500"
            >
              <option value="">All statuses</option>
              <option value="todo">Todo</option>
              <option value="in_progress">In progress</option>
              <option value="review">In review</option>
              <option value="done">Done</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </label>

          <label className="text-sm">
            <span className="mb-1 block font-medium text-slate-700">Deadline</span>
            <select
              name="deadline"
              defaultValue={taskFilters.deadline ?? ""}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 outline-none focus:border-slate-500"
            >
              <option value="">Any deadline</option>
              <option value="before">Before now</option>
              <option value="after">After now</option>
            </select>
          </label>

          <label className="text-sm">
            <span className="mb-1 block font-medium text-slate-700">Sort by</span>
            <select
              name="sort"
              defaultValue={taskFilters.sort ?? ""}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 outline-none focus:border-slate-500"
            >
              <option value="">Default order</option>
              <option value="deadline">Deadline</option>
              <option value="created_at">Created at</option>
              <option value="updated_at">Updated at</option>
            </select>
          </label>

          <label className="text-sm">
            <span className="mb-1 block font-medium text-slate-700">Direction</span>
            <select
              name="direction"
              defaultValue={taskFilters.direction}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 outline-none focus:border-slate-500"
            >
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
          </label>
        </div>

        <div className="mt-4 flex items-center justify-end gap-3">
          <Link
            to={clearTaskFiltersUrl}
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Clear
          </Link>
          <button
            type="submit"
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Apply
          </button>
        </div>
      </Form>

      {selectedTeam ? (
        canViewSelectedTeamTasks ? (
          tasks.length > 0 ? (
            <div className="mt-4 space-y-3">
              {tasks.map((task) => (
                <article
                  key={task.id}
                  className="rounded-lg border border-slate-200 bg-slate-50 p-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-base font-semibold text-slate-900">
                          {task.title}
                        </h3>
                        <span className="text-sm text-slate-500">
                          {`Assigned to ${
                            assigneeNamesById.get(task.assigned_to) ?? "Unknown user"
                          }`}
                        </span>
                      </div>
                      {task.description ? (
                        <p className="mt-2 text-sm text-slate-600">
                          {task.description}
                        </p>
                      ) : null}
                      <p className="mt-3 text-sm text-slate-500">
                        Deadline: {formatDeadline(task.deadline)} - Time left:{" "}
                        {formatTimeLeft(task.deadline)}
                      </p>
                  </div>
                    <div className="flex shrink-0 items-center gap-2">
                      {canDeleteTask ? (
                        <button
                          type="button"
                          onClick={() => setTaskPendingDelete(task)}
                          className="rounded-full border border-red-200 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-wide text-red-600 transition hover:bg-red-50"
                        >
                          Delete
                        </button>
                      ) : null}
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${
                          statusPillClassNames[task.status]
                        }`}
                      >
                        {formatStatusLabel(task.status)}
                      </span>
                    </div>
                  </div>

                  {task.assigned_to === currentUserId ? (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {nextStatusesByCurrentStatus[task.status].map((nextStatus) => (
                        <Form key={nextStatus} method="post">
                          <input type="hidden" name="intent" value="change-task-status" />
                          <input type="hidden" name="team_id" value={task.team_id} />
                          <input type="hidden" name="task_id" value={task.id} />
                          <input type="hidden" name="status" value={nextStatus} />
                          <button
                            type="submit"
                            className="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
                            disabled={submittingTaskStatusId === task.id}
                          >
                            {submittingTaskStatusId === task.id
                              ? "Updating..."
                              : formatStatusLabel(nextStatus)}
                          </button>
                        </Form>
                      ))}
                    </div>
                  ) : null}

                  {taskStatusChangeErrorTaskId === task.id && taskStatusChangeError ? (
                    <p className="mt-3 text-sm text-red-600">{taskStatusChangeError}</p>
                  ) : null}
                </article>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm text-slate-500">
              {isViewingAllTasks
                ? "No tasks were created for this team yet."
                : "You do not have any assigned tasks in this team."}
            </p>
          )
        ) : (
          <p className="mt-4 text-sm text-slate-500">
            You can view this team because you&apos;re an admin, but tasks are only available for teams you belong to.
          </p>
        )
      ) : (
        <p className="mt-4 text-sm text-slate-500">
          Pick a team to see the tasks assigned to you.
        </p>
      )}

      {taskPendingDelete && selectedTeam ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4">
          <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-lg">
            <div>
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-lg font-semibold text-slate-900">Delete task</h2>
                <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-red-700">
                  PM only
                </span>
              </div>
              <p className="mt-1 text-sm text-slate-500">
                Are you sure you want to delete{" "}
                <span className="font-medium text-slate-700">{taskPendingDelete.title}</span>?
                This cannot be undone.
              </p>
            </div>

            <Form method="post" className="mt-5 space-y-4">
              <input type="hidden" name="intent" value="delete-task" />
              <input type="hidden" name="team_id" value={selectedTeam.id} />
              <input type="hidden" name="task_id" value={taskPendingDelete.id} />

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                <p>
                  Assigned to{" "}
                  <span className="font-medium text-slate-700">
                    {assigneeNamesById.get(taskPendingDelete.assigned_to) ?? "Unknown user"}
                  </span>
                </p>
                <p className="mt-1">Deadline: {formatDeadline(taskPendingDelete.deadline)}</p>
              </div>

              {visibleDeleteTaskError ? (
                <p className="text-sm text-red-600">{visibleDeleteTaskError}</p>
              ) : null}

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setTaskPendingDelete(null)}
                  className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  disabled={isSubmittingDeleteTask}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-red-300"
                  disabled={isSubmittingDeleteTask}
                >
                  {isSubmittingDeleteTask ? "Deleting..." : "Yes, delete"}
                </button>
              </div>
            </Form>
          </div>
        </div>
      ) : null}

      {isAuditExportConfirmOpen && selectedTeam ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4">
          <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-lg">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Export audit log</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Download a CSV report for <span className="font-medium text-slate-700">{selectedTeam.name}</span>?
                </p>
              </div>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
                PM only
              </span>
            </div>

            <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              Choose how you want to export the audit data for this team.
            </div>

            <div className="mt-5 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setIsAuditExportConfirmOpen(false)}
                className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <a
                href={`/api/v1/tasks/${selectedTeam.id}/audit.csv?mode=raw`}
                onClick={() => setIsAuditExportConfirmOpen(false)}
                className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
              >
                Raw events CSV
              </a>
              <a
                href={`/api/v1/tasks/${selectedTeam.id}/audit.csv?mode=aggregated`}
                onClick={() => setIsAuditExportConfirmOpen(false)}
                className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
              >
                Aggregated CSV
              </a>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
