// CODIS — Web Push sender for timer endings (Supabase Edge Function, Deno). CODIS-PUSH-AUTO: no manual secrets.
// Called every minute by pg_cron (sql/codis_push.sql §6) with header `x-codis-cron: <secret generated in Vault>`.
// • First run: generates the VAPID key pair with WebCrypto and stores it in Vault via push_keys_init (once, never replaced).
//   The page reads only the PUBLIC key (rpc push_vapid_public). Nothing secret is in the repo, the page, or the function settings.
// • Claims due timers with push_claim_due (each event is claimed exactly once → no duplicate sends on reruns),
//   sends to every device of that user, and drops subscriptions the push service reports as gone (404/410).
// SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are provided by Supabase automatically.
// Optional overrides (Edge Function secrets): VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT, CODIS_CRON_SECRET.
// Deploy with JWT verification OFF:  supabase functions deploy codis-push --no-verify-jwt
import webpush from "npm:web-push@3.6.7";

const env = (k: string) => Deno.env.get(k) ?? "";
const URL_ = env("SUPABASE_URL"), SRK = env("SUPABASE_SERVICE_ROLE_KEY");

async function rpc(name: string, body: unknown) {
  const r = await fetch(`${URL_}/rest/v1/rpc/${name}`, {
    method: "POST",
    headers: { apikey: SRK, Authorization: `Bearer ${SRK}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${name}: HTTP ${r.status} ${await r.text()}`);
  const t = await r.text();
  return t ? JSON.parse(t) : null;
}

function safeEqual(a: string, b: string) {
  if (!a || !b || a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

const b64url = (u: Uint8Array) => btoa(String.fromCharCode(...u)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

async function generateVapid() {
  const kp = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
  const pub = b64url(new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey)));   // 65-byte uncompressed point
  const jwk = await crypto.subtle.exportKey("jwk", kp.privateKey);
  return { pub, priv: String(jwk.d) };                                                       // 32-byte scalar, base64url
}

type Keys = { pub: string; priv: string; cron: string };
async function keys(): Promise<Keys> {
  const row = ((await rpc("push_keys", {})) ?? [])[0] ?? {};
  return {
    pub: env("VAPID_PUBLIC_KEY") || row.pub || "",
    priv: env("VAPID_PRIVATE_KEY") || row.priv || "",
    cron: env("CODIS_CRON_SECRET") || row.cron || "",
  };
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("method not allowed", { status: 405 });
  if (!URL_ || !SRK) return new Response("not configured", { status: 500 });
  let k = await keys();
  if (!safeEqual(req.headers.get("x-codis-cron") ?? "", k.cron)) return new Response("forbidden", { status: 403 });
  if (!k.pub || !k.priv) {
    const g = await generateVapid();
    await rpc("push_keys_init", { p_pub: g.pub, p_priv: g.priv });
    k = await keys();
    if (!k.pub || !k.priv) return new Response("keys unavailable", { status: 500 });
  }
  webpush.setVapidDetails(env("VAPID_SUBJECT") || "mailto:codis@codis.app", k.pub, k.priv);

  const rows: { event_id: string; title: string; body: string; endpoint: string; p256dh: string; auth: string }[] =
    (await rpc("push_claim_due", { p_limit: 200 })) ?? [];
  let sent = 0, gone = 0, failed = 0;
  await Promise.all(rows.map(async (r) => {
    const payload = JSON.stringify({ title: r.title, body: r.body, tag: r.event_id, url: "./" });
    try {
      await webpush.sendNotification({ endpoint: r.endpoint, keys: { p256dh: r.p256dh, auth: r.auth } }, payload, { TTL: 3600, urgency: "high" });
      sent++;
    } catch (e) {
      const code = (e as { statusCode?: number }).statusCode;
      if (code === 404 || code === 410) { gone++; await rpc("push_drop_endpoint", { p_endpoint: r.endpoint }).catch(() => {}); }
      else { failed++; console.error("push failed", code, (e as Error).message); }
    }
  }));
  return Response.json({ claimed: rows.length, sent, gone, failed });
});
