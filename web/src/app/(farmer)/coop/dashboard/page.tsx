/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-014: Kooperatif dashboard — uye sayisi, tarla sayisi, aktif gorev ozeti. */
/* KR-063: Erisim: COOP_OWNER rolune ozel dashboard. */

export default function CoopDashboardPage() {
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Kooperatif Dashboard</h1>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
          <p className="text-3xl font-bold text-slate-800">—</p>
          <p className="mt-1 text-sm text-slate-500">Toplam Uye</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
          <p className="text-3xl font-bold text-slate-800">—</p>
          <p className="mt-1 text-sm text-slate-500">Toplam Tarla</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
          <p className="text-3xl font-bold text-slate-800">—</p>
          <p className="mt-1 text-sm text-slate-500">Aktif Gorev</p>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="font-medium mb-2">Hizli Erisim</h2>
        <nav className="flex gap-3 text-sm">
          <a href="/coop/members" className="text-sky-600 hover:underline">Uyeler</a>
          <a href="/coop/invite" className="text-sky-600 hover:underline">Davet Et</a>
          <a href="/coop/fields" className="text-sky-600 hover:underline">Tarlalar</a>
          <a href="/fields" className="text-sky-600 hover:underline">Tarla Ekle</a>
        </nav>
      </div>
    </section>
  );
}
