from enum import StrEnum
from app.core.enums import TeamRole


class TeamPermission(StrEnum):
    CREATE_TASK = "create_task"
    VIEW_USER_TASKS = "view_user_tasks"
    VIEW_ALL_TASKS = "view_all_tasks"
    CHANGE_TASK_STATUS = "change_task_status"
    DELETE_TASK = "delete_task"
    GENERATE_REPORT = "generate_report"


TEAM_ROLE_PERMISSIONS: dict[TeamRole, set[TeamPermission]] = {
    TeamRole.PM: {
        TeamPermission.CREATE_TASK,
        TeamPermission.VIEW_USER_TASKS,
        TeamPermission.VIEW_ALL_TASKS,
        TeamPermission.CHANGE_TASK_STATUS,
        TeamPermission.DELETE_TASK,
        TeamPermission.GENERATE_REPORT
    },
    TeamRole.TL: {
        TeamPermission.VIEW_USER_TASKS,
        TeamPermission.VIEW_ALL_TASKS,
        TeamPermission.CHANGE_TASK_STATUS,
        TeamPermission.DELETE_TASK
    },
    TeamRole.MEMBER: {
        TeamPermission.VIEW_USER_TASKS,
        TeamPermission.CHANGE_TASK_STATUS,
    },
}