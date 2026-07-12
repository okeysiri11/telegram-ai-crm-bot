# Comment engine for deals, tasks, events, documents, requests.


class CommentService:
    @staticmethod
    def add_comment(
        entity_type: str,
        entity_id: int,
        author_id: int,
        comment_text: str,
    ) -> int:
        from database import add_comment
        return add_comment(entity_type, entity_id, author_id, comment_text)

    @staticmethod
    def get_comments(entity_type: str, entity_id: int, limit: int = 50) -> list:
        from database import get_comments
        return get_comments(entity_type, entity_id, limit=limit)

    @staticmethod
    def delete_comment(comment_id: int, user_id: int) -> bool:
        from database import soft_delete
        return soft_delete("comment", comment_id, user_id)
