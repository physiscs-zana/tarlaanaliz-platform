/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-014: Kooperatif tarla yonetimi — uyelerin tarlalarini listeler. */
/* KR-013: Tarla benzersizligi aynidir: il+ilce+mahalle+ada+parsel. "Tarla kaydi tekil, sahiplik/erisim ayri." */

export default function CoopFieldsPage() {
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Kooperatif Tarlalari</h1>
      <p className="text-sm text-slate-500">
        Kooperatif uyelerine ait tarlalar burada listelenir. Tarla kaydi tekil olup sahiplik ve erisim ayri yonetilir.
      </p>

      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500">
        Tarla verisi yukleniyor...
      </div>
    </section>
  );
}
