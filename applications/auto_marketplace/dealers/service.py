# DealerService — dealer and branch management.

from __future__ import annotations

from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.models import Dealer, DealerBranch
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class DealerService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def list_dealers(self) -> list[Dealer]:
        return self._store.dealers.list_all()

    def get_dealer(self, dealer_id: str) -> Dealer:
        dealer = self._store.dealers.get(dealer_id)
        if dealer is None:
            raise NotFoundError("Dealer", dealer_id)
        return dealer

    def create_dealer(self, dealer: Dealer) -> Dealer:
        return self._store.dealers.save(dealer.dealer_id, dealer)

    def add_branch(self, dealer_id: str, branch: DealerBranch) -> Dealer:
        dealer = self.get_dealer(dealer_id)
        dealer.branches.append(branch)
        return self._store.dealers.save(dealer_id, dealer)


dealer_service = DealerService()
