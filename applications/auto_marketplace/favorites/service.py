# Favorites and saved searches.

from __future__ import annotations

from events.publisher import publish

from applications.auto_marketplace.authentication.models import Favorite, SavedSearch
from applications.auto_marketplace.customer_portal.events import FavoriteAddedEvent
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class FavoritesService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    async def add_favorite(self, user_id: str, vehicle_id: str) -> Favorite:
        fav = Favorite(user_id=user_id, vehicle_id=vehicle_id)
        self._store.favorites.save(fav.favorite_id, fav)
        await publish(FavoriteAddedEvent(user_id=user_id, vehicle_id=vehicle_id))
        return fav

    def remove_favorite(self, favorite_id: str) -> bool:
        return self._store.favorites.delete(favorite_id)

    def list_favorites(self, user_id: str) -> list[Favorite]:
        return [f for f in self._store.favorites.list_all() if f.user_id == user_id]

    def save_search(self, user_id: str, name: str, criteria: dict) -> SavedSearch:
        search = SavedSearch(user_id=user_id, name=name, criteria=criteria)
        return self._store.saved_searches.save(search.search_id, search)

    def list_saved_searches(self, user_id: str) -> list[SavedSearch]:
        return [s for s in self._store.saved_searches.list_all() if s.user_id == user_id]

    def delete_saved_search(self, search_id: str) -> bool:
        return self._store.saved_searches.delete(search_id)


favorites_service = FavoritesService()
