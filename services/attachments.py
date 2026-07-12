# Universal attachment engine.


class AttachmentService:
    @staticmethod
    def attach_file(
        entity_type: str,
        entity_id: int,
        file_id: int,
        uploaded_by: int,
    ) -> int:
        from database import attach_file
        return attach_file(entity_type, entity_id, file_id, uploaded_by)

    @staticmethod
    def get_attachments(entity_type: str, entity_id: int, limit: int = 50) -> list:
        from database import get_attachments
        return get_attachments(entity_type, entity_id, limit=limit)

    @staticmethod
    def remove_attachment(attachment_id: int, user_id: int) -> bool:
        from database import remove_attachment
        return remove_attachment(attachment_id, user_id)
