# Enhanced global search across platform entities.

class SearchService:
    @staticmethod
    def search(user_id: int, query: str, limit: int = 10) -> dict:
        from database import enhanced_global_search
        return enhanced_global_search(user_id, query.strip(), limit=limit)

    @staticmethod
    def format_results(results: dict, query: str) -> str:
        from database import format_enhanced_search_results
        return format_enhanced_search_results(results, query)

    @staticmethod
    def search_and_format(user_id: int, query: str, limit: int = 10) -> str:
        results = SearchService.search(user_id, query, limit)
        return SearchService.format_results(results, query)
