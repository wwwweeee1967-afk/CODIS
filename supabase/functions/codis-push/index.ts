// CODIS — Web Push sender for timer endings (Supabase Edge Function, Deno).
// Called every minute by pg_cron (sql/codis_push.sql §5) with header `x-codis-cron: <CODIS_CRON_SECRET>`.
// Claims due timers with push_claim_due (each event is claimed exactly once → no duplicate sends on reruns),
// sends to every device of that user, and drops subscriptions the push service reports as gone (404/410).
//
// Secrets (Dashboard → Edge Functions → Secrets; NEVER in the repo or the page):
//   VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT (e.g. mailto:you@example.com), CODIS_CRON_SECRET
//   SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are provided by Supabase automatically.
// Deploy: supabase functions deploy codis-push --no-verify-jwt   (the cron secret header is the gate)
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
  if (!a || a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("method not allowed", { status: 405 });
  if (!safeEqual(req.headers.get("x-codis-cron") ?? "", env("CODIS_CRON_SECRET"))) return new Response("forbidden", { status: 403 });
  if (!env("VAPID_PUBLIC_KEY") || !env("VAPID_PRIVATE_KEY") || !URL_ || !SRK) return new Response("not configured", { status: 500 });
  webpush.setVapidDetails(env("VAPID_SUBJECT") || "mailto:admin@example.com", env("VAPID_PUBLIC_KEY"), env("VAPID_PRIVATE_KEY"));

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
