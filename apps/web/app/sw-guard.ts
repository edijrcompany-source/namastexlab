/** Limpa Service Workers estranhos da origin localhost:3000 (dev).

 * Causa raiz do "bug do loop": apps anteriores (ex.: AzyHub) registraram SW
 * nesta origin e continuam interceptando a navegação, servindo o app velho
 * no lugar do nosso chat. Este guard remove qualquer SW que não seja nosso
 * (não registramos nenhum) e esvazia os caches — uma vez só, no client.
 */
export async function purgeAlienServiceWorkers(): Promise<number> {
  if (typeof navigator === "undefined" || !("serviceWorker" in navigator)) return 0;
  const regs = await navigator.serviceWorker.getRegistrations();
  let n = 0;
  for (const r of regs) {
    await r.unregister();
    n += 1;
  }
  if (typeof caches !== "undefined") {
    const keys = await caches.keys();
    await Promise.all(keys.map((k) => caches.delete(k)));
  }
  return n;
}
