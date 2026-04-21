from uuid import UUID
import csv
import io
from collections import defaultdict
from sqlalchemy.orm import Session

from app.repositories.integration_event_repository import IntegrationEventRepository


class AuditService:
    @staticmethod
    def generate_team_audit_csv(db: Session, team_id: UUID):
        buffer = io.StringIO()
        repo = IntegrationEventRepository(db)
        rows = repo.get_audit_log(team_id)
        writer = csv.writer(buffer)

        writer.writerow(["event_id", "event_type", "team_id", "task_id", "title", "created_at"])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        for row in rows:
            writer.writerow([
                row.event_id,
                row.event_type,
                row.payload.get("team_id"),
                row.payload.get("task_id"),
                row.payload.get("title"),
                row.created_at,
            ])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    @staticmethod
    def generate_aggregated_team_audit_csv(db: Session, team_id: UUID):
        buffer = io.StringIO()
        repo = IntegrationEventRepository(db)
        rows = repo.get_audit_log(team_id)
        error_rows = repo.get_processing_error_logs(team_id)
        writer = csv.writer(buffer)

        metric_names = {
            "task.created": "tasks_created",
            "task.status_changed": "task_status_changed",
            "task.deleted": "tasks_deleted",
        }
        aggregated_metrics: dict[tuple[str, str], int] = defaultdict(int)
        error_counts: dict[tuple[str, str], int] = defaultdict(int)

        for row in rows:
            metric_name = metric_names.get(row.event_type)
            if metric_name is None:
                continue

            event_date = row.created_at.date().isoformat()
            aggregated_metrics[(event_date, metric_name)] += 1

        for error_row in error_rows:
            error_date = error_row.failed_at.date().isoformat()
            metric_name = metric_names.get(error_row.event_type)
            if metric_name is None:
                continue
            error_counts[(error_date, metric_name)] += 1

        writer.writerow(["date", "metric_name", "metric_value", "errors_count", "notes"])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        row_keys = sorted(set(aggregated_metrics.keys()) | set(error_counts.keys()))

        for event_date, metric_name in row_keys:
            writer.writerow(
                [
                    event_date,
                    metric_name,
                    aggregated_metrics.get((event_date, metric_name), 0),
                    error_counts.get((event_date, metric_name), 0),
                    "",
                ]
            )
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

        
