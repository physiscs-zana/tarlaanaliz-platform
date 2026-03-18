export default function BenimSayfamPage() {
  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Benim Sayfam</h1>
        <p className="mt-1 text-sm text-slate-600">TarlaAnaliz platformuna hosgeldiniz. Asagidaki adimlari takip ederek tarlanizi analiz ettirebilirsiniz.</p>
      </div>
      <div className="rounded-xl border border-emerald-200 bg-gradient-to-r from-emerald-50 to-white p-5">
        <h2 className="text-lg font-semibold text-emerald-800">Nasil Calisir?</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-4">
          {[
            { step: "1", title: "Tarla Ekle", desc: "Il, ilce, ada/parsel ve bitki turunu girin.", href: "/fields" },
            { step: "2", title: "Gorev Olustur", desc: "Tarlaniz icin drone tarama gorevi olusturun.", href: "/missions" },
            { step: "3", title: "Sonuclari Gor", desc: "Hastalik, zararli, ot ve su haritalarini inceleyin.", href: "/results" },
            { step: "4", title: "Odeme Yap", desc: "Analiz ucretini odeyin ve raporunuzu alin.", href: "/payments" },
          ].map((item) => (
            <a key={item.step} href={item.href} className="rounded-lg border border-slate-200 bg-white p-3 hover:shadow-sm transition">
              <div className="mb-2 flex h-7 w-7 items-center justify-center rounded-full bg-emerald-600 text-xs font-bold text-white">{item.step}</div>
              <h3 className="text-sm font-semibold text-slate-900">{item.title}</h3>
              <p className="mt-0.5 text-xs text-slate-500">{item.desc}</p>
            </a>
          ))}
        </div>
      </div>
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
        <h2 className="text-sm font-semibold text-blue-800">Duyurular</h2>
        <ul className="mt-2 space-y-1.5 text-sm text-blue-700">
          <li>Sezonluk paketlerde erken kayit indirimi baslamistir.</li>
          <li>Pamuk ve misir tarlalari icin haftalik tarama onerilir.</li>
        </ul>
      </div>
    </section>
  );
}
