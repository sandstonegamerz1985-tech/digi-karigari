// Supabase is loaded from the CDN in index.html. The publishable key is designed
// for browser use; never put a service_role or secret key in this frontend.
const { createClient } = window.supabase;

if (!createClient) {
  throw new Error("Supabase client failed to load. Check the Supabase CDN script in index.html.");
}

export const supabaseClient = createClient(
  "https://fgszkmkrtoahlhykqwbp.supabase.co",
  "sb_publishable_wuQMeEqi0BbMhb4lSmdF4Q_-J1WkARe"
);
