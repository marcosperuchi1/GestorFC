
import { createClient } from "npm:@supabase/supabase-js@2.95.0";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

async function sha256Hex(value: string) {
  const data = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return json({ error: "method_not_allowed" }, 405);
  }

  const authHeader = req.headers.get("Authorization") ?? "";
  if (!authHeader.startsWith("Bearer ")) {
    return json({ error: "missing_authorization" }, 401);
  }

  const url = Deno.env.get("SUPABASE_URL");
  const publishableMap = JSON.parse(Deno.env.get("SUPABASE_PUBLISHABLE_KEYS") ?? "{}");
  const secretMap = JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") ?? "{}");
  const publishableKey = publishableMap.default;
  const secretKey = secretMap.default;

  if (!url || !publishableKey || !secretKey) {
    return json({ error: "server_configuration_error" }, 500);
  }

  const token = authHeader.slice("Bearer ".length);
  const userClient = createClient(url, publishableKey, {
    global: { headers: { Authorization: authHeader } },
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const { data: userData, error: userError } = await userClient.auth.getUser(token);
  const user = userData?.user;
  if (userError || !user) {
    return json({ error: "invalid_session" }, 401);
  }

  let body: { device_id?: string; device_name?: string } = {};
  try {
    body = await req.json();
  } catch {
    body = {};
  }

  const admin = createClient(url, secretKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  let { data: license, error: licenseError } = await admin
    .from("licenses")
    .select("plan,status,valid_until,max_devices")
    .eq("user_id", user.id)
    .maybeSingle();

  if (licenseError) {
    return json({ error: "license_lookup_failed" }, 500);
  }

  if (!license) {
    const { data: created, error: createError } = await admin
      .from("licenses")
      .insert({ user_id: user.id, plan: "free", status: "active", max_devices: 2 })
      .select("plan,status,valid_until,max_devices")
      .single();

    if (createError) {
      return json({ error: "license_creation_failed" }, 500);
    }
    license = created;
  }

  const now = new Date();
  const expired = !!license.valid_until && new Date(license.valid_until) < now;
  const active = license.status === "active" && !expired;
  const effectivePlan = active ? license.plan : "free";

  let deviceAuthorized = true;
  let activeDevices = 0;

  if ((effectivePlan === "premium" || effectivePlan === "author") && body.device_id) {
    const trimmedDeviceId = String(body.device_id).trim().slice(0, 256);
    if (!trimmedDeviceId) {
      return json({ error: "invalid_device_id" }, 400);
    }

    const deviceHash = await sha256Hex(trimmedDeviceId);

    const { data: existing, error: existingError } = await admin
      .from("device_authorizations")
      .select("id")
      .eq("user_id", user.id)
      .eq("device_hash", deviceHash)
      .is("revoked_at", null)
      .maybeSingle();

    if (existingError) {
      return json({ error: "device_lookup_failed" }, 500);
    }

    const { count, error: countError } = await admin
      .from("device_authorizations")
      .select("id", { count: "exact", head: true })
      .eq("user_id", user.id)
      .is("revoked_at", null);

    if (countError) {
      return json({ error: "device_count_failed" }, 500);
    }

    activeDevices = count ?? 0;

    if (!existing) {
      const maxDevices = effectivePlan === "author" ? 20 : Number(license.max_devices ?? 2);
      if (activeDevices >= maxDevices) {
        deviceAuthorized = false;
      } else {
        // Reuse a previously revoked fingerprint if this same installation
        // returns after logout or an admin device reset. The database has a
        // UNIQUE (user_id, device_hash), so INSERT would otherwise fail.
        const { error: insertError } = await admin
          .from("device_authorizations")
          .upsert({
            user_id: user.id,
            device_hash: deviceHash,
            device_name: body.device_name ? String(body.device_name).slice(0, 120) : null,
            last_seen_at: now.toISOString(),
            revoked_at: null,
          }, { onConflict: "user_id,device_hash" });

        if (insertError) {
          return json({ error: "device_registration_failed" }, 500);
        }
        activeDevices += 1;
      }
    } else {
      await admin
        .from("device_authorizations")
        .update({
          last_seen_at: now.toISOString(),
          device_name: body.device_name ? String(body.device_name).slice(0, 120) : undefined,
        })
        .eq("id", existing.id);
    }
  }

  const allowed = active && deviceAuthorized;

  return json({
    user_id: user.id,
    plan: effectivePlan,
    status: license.status,
    active,
    allowed,
    valid_until: license.valid_until,
    max_devices: effectivePlan === "author" ? 20 : license.max_devices,
    active_devices: activeDevices,
    device_authorized: deviceAuthorized,
    checked_at: now.toISOString(),
  });
});
