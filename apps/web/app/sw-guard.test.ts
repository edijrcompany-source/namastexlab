import { purgeAlienServiceWorkers } from "@/app/sw-guard";

// jsdom não tem serviceWorker — o guard deve retornar 0 sem explodir
describe("sw-guard", () => {
  it("retorna 0 quando navigator.serviceWorker não existe (jsdom/SSR)", async () => {
    const n = await purgeAlienServiceWorkers();
    expect(n).toBe(0);
  });

  it("remove registrations alienígenas quando a API existe", async () => {
    const fakeUnregister = vi.fn().mockResolvedValue(undefined);
    const registrations = [{ unregister: fakeUnregister }];
    Object.defineProperty(navigator, "serviceWorker", {
      value: { getRegistrations: vi.fn().mockResolvedValue(registrations) },
      configurable: true,
    });
    const fakeCache = {
      keys: vi.fn().mockResolvedValue(["sw-azyhub"]),
      delete: vi.fn().mockResolvedValue(true),
    };
    vi.stubGlobal("caches", fakeCache);

    const n = await purgeAlienServiceWorkers();
    expect(n).toBe(1);
    expect(fakeUnregister).toHaveBeenCalledOnce();
    expect(fakeCache.delete).toHaveBeenCalledWith("sw-azyhub");

    vi.unstubAllGlobals();
    Object.defineProperty(navigator, "serviceWorker", {
      value: undefined,
      configurable: true,
    });
  });
});
