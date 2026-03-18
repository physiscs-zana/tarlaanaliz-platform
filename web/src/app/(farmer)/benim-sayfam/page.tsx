/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-002: Harita katman renk kodlari ve anlam aciklamalari. */

export default function BenimSayfamPage() {
  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Benim Sayfam</h1>
        <p className="mt-1 text-sm text-slate-600">TarlaAnaliz platformuna hosgeldiniz. Asagidaki adimlari takip ederek tarlanizi analiz ettirebilirsiniz.</p>
      </div>
      <div className="rounded-xl border border-emerald-200 bg-gradient-to-r from-emerald-50 to-white p-5">
        <h2 className="text-lg font-semibold text-emerald-800">Nas&#305;l &#199;al&#305;&#351;&#305;r?</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-4">
          {[
            { step: "1", title: "Tarla Ekle", desc: "Il, ilce, ada/parsel ve bitki turunu girin.", href: "/fields" },
            { step: "2", title: "Analiz Talebi", desc: "Tarlaniz icin drone analiz talebi olusturun.", href: "/fields" },
            { step: "3", title: "Odeme Yap", desc: "Analiz ucretini odeyin.", href: "/payments" },
            { step: "4", title: "Sonuclari Gor", desc: "Hastalik, zararli, ot ve su haritalarini inceleyin.", href: "/results" },
          ].map((item) => (
            <a key={item.step} href={item.href} className="rounded-lg border border-slate-200 bg-white p-3 hover:shadow-sm transition">
              <div className="mb-2 flex h-7 w-7 items-center justify-center rounded-full bg-emerald-600 text-xs font-bold text-white">{item.step}</div>
              <h3 className="text-sm font-semibold text-slate-900">{item.title}</h3>
              <p className="mt-0.5 text-xs text-slate-500">{item.desc}</p>
            </a>
          ))}
        </div>
      </div>

      {/* KR-002: Harita Renk Kodlari Aciklamasi */}
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold text-slate-900">Harita Renk Kodlari</h2>
        <p className="mt-1 text-sm text-slate-500">Analiz sonuclarinda gordugunuz renklerin anlami:</p>
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {[
            { color: "#22c55e", label: "Saglik (Genel)", desc: "Tarlaniz genel olarak saglikli." },
            { color: "#f97316", label: "Hastalik", desc: "Bitki hastaligi tespit edilen bolgeler." },
            { color: "#ef4444", label: "Zararli Bocek", desc: "Bocek zarari gorulmus alanlar." },
            { color: "#a855f7", label: "Mantar", desc: "Mantar enfeksiyonu saptanan bolgeler." },
            { color: "#eab308", label: "Yabanci Ot", desc: "Yabanci ot yogunlugu yuksek alanlar." },
            { color: "#3b82f6", label: "Su Stresi", desc: "Sulama yetersizligi veya fazlaligi." },
            { color: "#6b7280", label: "Azot Stresi", desc: "Azot eksikligi gorulmus bolgeler." },
            { color: "#dc2626", label: "Termal Stres", desc: "Sicaklik stresi altindaki alanlar." },
          ].map((item) => (
            <div key={item.label} className="flex items-start gap-3 rounded border border-slate-100 p-2">
              <div className="mt-0.5 h-5 w-5 flex-shrink-0 rounded" style={{ backgroundColor: item.color }} />
              <div>
                <span className="text-sm font-medium text-slate-900">{item.label}</span>
                <p className="text-xs text-slate-500">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Ornek Analiz Sonucu */}
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold text-slate-900">Ornek Analiz Haritasi</h2>
        <p className="mt-1 text-sm text-slate-500">Asagida analiz edilmis ornek bir tarla gorunumu bulunmaktadir.</p>
        <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
          {/* SVG-based example analyzed field map */}
          <svg viewBox="0 0 400 250" className="w-full h-auto" role="img" aria-label="Ornek analiz haritasi">
            {/* Field background */}
            <rect x="20" y="20" width="360" height="210" rx="8" fill="#22c55e" opacity="0.35" />
            {/* Healthy areas */}
            <rect x="30" y="30" width="120" height="90" rx="4" fill="#22c55e" opacity="0.6" />
            <rect x="260" y="30" width="110" height="80" rx="4" fill="#22c55e" opacity="0.55" />
            {/* Disease area */}
            <rect x="160" y="40" width="90" height="70" rx="4" fill="#f97316" opacity="0.65" />
            <text x="185" y="80" fontSize="11" fill="#92400e" fontWeight="600">Hastalik</text>
            {/* Weed area */}
            <rect x="30" y="140" width="100" height="70" rx="4" fill="#eab308" opacity="0.6" />
            <text x="50" y="180" fontSize="11" fill="#854d0e" fontWeight="600">Yabanci Ot</text>
            {/* Water stress area */}
            <rect x="280" y="130" width="90" height="80" rx="4" fill="#3b82f6" opacity="0.5" />
            <text x="290" y="175" fontSize="11" fill="#1e40af" fontWeight="600">Su Stresi</text>
            {/* Pest area */}
            <rect x="145" y="140" width="70" height="60" rx="4" fill="#ef4444" opacity="0.6" />
            <text x="152" y="175" fontSize="10" fill="#991b1b" fontWeight="600">Zararli</text>
            {/* Fungus area */}
            <rect x="225" y="145" width="50" height="50" rx="4" fill="#a855f7" opacity="0.55" />
            <text x="229" y="175" fontSize="10" fill="#6b21a8" fontWeight="600">Mantar</text>
            {/* Healthy label */}
            <text x="55" y="75" fontSize="11" fill="#166534" fontWeight="600">Saglikli</text>
            <text x="285" y="75" fontSize="11" fill="#166534" fontWeight="600">Saglikli</text>
          </svg>
          <p className="mt-2 text-center text-xs text-slate-400">Bu gorsel ornektir. Gercek analiz sonuclariniz drone taramasi sonrasi olusturulur.</p>
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
