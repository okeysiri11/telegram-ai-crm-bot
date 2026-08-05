import type { IProvider } from "./interfaces/IProvider.js";
import type { ProviderSnapshot } from "./types.js";

export class ProviderRegistry {
  private readonly providers = new Map<string, IProvider>();

  register(provider: IProvider): void {
    if (this.providers.has(provider.id)) {
      throw new Error(`Provider already registered: ${provider.id}`);
    }
    this.providers.set(provider.id, provider);
  }

  get(id: string): IProvider | undefined {
    return this.providers.get(id);
  }

  require(id: string): IProvider {
    const p = this.providers.get(id);
    if (!p) throw new Error(`Provider not found: ${id}`);
    return p;
  }

  list(): readonly IProvider[] {
    return Object.freeze([...this.providers.values()]);
  }

  snapshots(): ProviderSnapshot[] {
    return this.list().map((p) => p.snapshot());
  }

  findByCapability(capabilityId: string): IProvider | undefined {
    const connected = this.list().filter((p) => p.snapshot().connected);
    const pool = connected.length ? connected : this.list();
    return pool.find((p) =>
      p.capabilities().some(
        (c) =>
          c.id === capabilityId ||
          capabilityId.startsWith(c.id) ||
          c.id === "*",
      ),
    );
  }

  clear(): void {
    this.providers.clear();
  }
}
