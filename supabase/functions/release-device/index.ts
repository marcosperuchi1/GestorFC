import { createClient } from 'npm:@supabase/supabase-js@2.95.0';
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};
function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}
async function sha256Hex(value: string) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest)).map(b => b.toString(16).padStart(2, '0')).join('');
}
Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ error: 'method_not_allowed' }, 405);
  const authHeader = req.headers.get('Authorization') ?? '';
  if (!authHeader.startsWith('Bearer ')) return json({ error: 'missing_authorization' }, 401);
  const url = Deno.env.get('SUPABASE_URL');
  const publishableMap = JSON.parse(Deno.env.get('SUPABASE_PUBLISHABLE_KEYS') ?? '{}');
  const secretMap = JSON.parse(Deno.env.get('SUPABASE_SECRET_KEYS') ?? '{}');
  const publishableKey = publishableMap.default;
  const secretKey = secretMap.default;
  if (!url || !publishableKey || !secretKey) return json({ error: 'server_configuration_error' }, 500);
  const token = authHeader.slice('Bearer '.length);
  const userClient = createClient(url, publishableKey, {
    global: { headers: { Authorization: authHeader } },
    auth: { persistSession: false, autoRefreshToken: false },
  });
  const { data: userData, error: userError } = await userClient.auth.getUser(token);
  const user = userData?.user;
  if (userError || !user) return json({ error: 'invalid_session' }, 401);
  let body: { device_id?: string } = {};
  try { body = await req.json(); } catch { return json({ error: 'invalid_json' }, 400); }
  const deviceId = String(body.device_id ?? '').trim();
  if (!/^[a-z0-9][a-z0-9-]{12,254}$/i.test(deviceId)) return json({ error: 'invalid_device_id' }, 400);
  const deviceHash = await sha256Hex(deviceId);
  const admin = createClient(url, secretKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
  const { data, error } = await admin.from('device_authorizations')
    .delete()
    .eq('user_id', user.id)
    .eq('device_hash', deviceHash)
    .is('revoked_at', null)
    .select('id');
  if (error) return json({ error: 'device_release_failed' }, 500);
  return json({ ok: true, released: (data?.length ?? 0) > 0 });
});