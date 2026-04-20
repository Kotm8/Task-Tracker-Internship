from enum import StrEnum

class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"

class TeamPermission(StrEnum):
    CREATE_TASK = "create_task"
    VIEW_USER_TASKS = "view_user_tasks"
    VIEW_ALL_TASKS = "view_all_tasks"
    CHANGE_TASK_STATUS = "change_task_status"
    DELETE_TASK = "delete_task"
