/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: role tabanlı yönlendirme + public landing page. */

import { cookies } from "next/headers";
import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";
import { COOKIE_ROLE_KEY } from "@/lib/constants";

/* ------------------------------------------------------------------ */
/* Authenticated users → role-based redirect                          */
/* ------------------------------------------------------------------ */
function tryRoleRedirect() {
  const store = cookies();
  const role = store.get(COOKIE_ROLE_KEY)?.value;
  if (role === "admin") redirect("/analytics");
  if (role === "expert") redirect("/queue");
  if (role === "farmer") redirect("/fields");
  if (role === "pilot") redirect("/pilot/missions");
}

/* ------------------------------------------------------------------ */
/* SVG Icons                                                          */
/* ------------------------------------------------------------------ */
function IconLeaf({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66.95-2.3c.48.17.98.3 1.34.3C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75" />
    </svg>
  );
}

function IconArrowRight({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>
  );
}

function IconCheck({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/* Landing Page                                                       */
/* ------------------------------------------------------------------ */
export default function HomePage() {
  tryRoleRedirect();

  return (
    <div className="min-h-screen bg-white">
      {/* ===== Navbar ===== */}
      <nav className="sticky top-0 z-40 border-b border-slate-100 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600">
              <IconLeaf className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold text-slate-900">TarlaAnaliz</span>
          </Link>
          <div className="flex items-center gap-2">
            <Link href="/login" className="rounded-md px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100">
              Giriş Yap
            </Link>
            <Link href="/register" className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-emerald-700">
              Üye Ol
            </Link>
          </div>
        </div>
      </nav>

      {/* ===== Hero ===== */}
      <section className="relative overflow-hidden bg-gradient-to-b from-emerald-50/60 to-white">
        <div className="mx-auto max-w-6xl px-4 pb-8 pt-8 sm:pb-12 sm:pt-10">
          <div className="grid items-center gap-6 lg:grid-cols-2 lg:gap-10">
            <div>
              <h1 className="text-3xl font-extrabold leading-tight tracking-tight text-slate-900 sm:text-4xl lg:text-[2.75rem]">
                Yeşil görünen tarlada
                <span className="block text-emerald-600">görünmeyeni yakalıyoruz</span>
              </h1>
              <p className="mt-3 text-base leading-relaxed text-slate-600 sm:text-lg">
                Tarlanızın <strong>&ldquo;check-up ve tahlilini&rdquo;</strong> drone ile yapıyoruz.
                Hastalık, zararlı böcek, yabancı ot ve su eksikliğini
                <strong> insan gözünden bir hafta önce</strong> tespit ediyoruz.
              </p>
              <div className="mt-3 flex flex-wrap gap-2 text-sm text-slate-500">
                <span className="rounded-full border border-slate-200 bg-white px-3 py-1">Erken Uyarı</span>
                <span className="rounded-full border border-slate-200 bg-white px-3 py-1">Hedefli İlaçlama</span>
                <span className="rounded-full border border-slate-200 bg-white px-3 py-1">Rapor + Harita</span>
              </div>
              <div className="mt-5 flex flex-col gap-2.5 sm:flex-row">
                <Link
                  href="/register"
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-emerald-600/20 transition hover:bg-emerald-700"
                >
                  Ücretsiz Üye Ol
                  <IconArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="#nasil-calisir"
                  className="inline-flex items-center justify-center rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  Nasıl Çalışır?
                </Link>
              </div>
            </div>
            <Image
              src="/images/hero-drone.png"
              alt="Drone tarla tarama — ısı haritası"
              width={800}
              height={500}
              className="w-full rounded-xl shadow-lg"
              priority
            />
          </div>
        </div>
      </section>

      {/* ===== Stats ===== */}
      <div className="border-y border-slate-100 bg-slate-50">
        <div className="mx-auto grid max-w-3xl grid-cols-3 divide-x divide-slate-200 py-5">
          {[
            { value: "81", label: "İl Kapsama" },
            { value: "1 Hafta", label: "Erken Tespit" },
            { value: "%95", label: "Doğruluk" },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-xl font-bold text-emerald-600 sm:text-2xl">{s.value}</div>
              <div className="text-xs text-slate-500">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ===== Tarlanın Röntgeni — Infographic ===== */}
      <section className="py-10 sm:py-14">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center text-2xl font-bold text-slate-900 sm:text-3xl">
            Tarlanın &ldquo;Röntgeni&rdquo; Nasıl Çekiliyor?
          </h2>
          <p className="mx-auto mt-2 max-w-2xl text-center text-sm text-slate-600 sm:text-base">
            Drone özel kameralarla tarlanızı santimetresine kadar tarar. Görüntüler merkezdeki
            bilgisayarlarda işlenerek 7 farklı katmanda analiz edilir.
          </p>
          <div className="mt-6 grid items-center gap-6 lg:grid-cols-2">
            <Image
              src="/images/analiz-infografik.png"
              alt="Drone tarla tarama — 7 analiz katmanı infografik"
              width={900}
              height={550}
              className="w-full rounded-xl"
            />
            <div className="space-y-2.5">
              {[
                { title: "Bitki Hastalığı", desc: "Mantar, virüs gibi belirtileri gözle görmeden tespit eder." },
                { title: "Zararlı Böcek", desc: "Böcek zararı olan bölgeleri harita üzerinde işaretler." },
                { title: "Yabancı Ot", desc: "Ot basan bölgeleri gösterir — sadece o bölgeyi ilaçlarsınız." },
                { title: "Su Eksikliği", desc: "Hangi bölgede sulama yetersiz, hangisinde fazla — hepsini görürsünüz." },
                { title: "Azot / Gübre Durumu", desc: "Nereye gübre lazım, nereye lazım değil — gereksiz masraftan kurtulun." },
                { title: "Bitki Canlılığı", desc: "Tarlanın genel sağlık durumunu renk haritasıyla özetler." },
              ].map((item) => (
                <div key={item.title} className="flex gap-2.5">
                  <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                    <IconCheck className="h-3 w-3" />
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-slate-900">{item.title}: </span>
                    <span className="text-sm text-slate-600">{item.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ===== Önce / Sonra ===== */}
      <section className="bg-slate-50 py-10 sm:py-14">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center text-2xl font-bold text-slate-900 sm:text-3xl">
            Gözle Görünmeyeni Ortaya Çıkarır
          </h2>
          <p className="mx-auto mt-2 max-w-xl text-center text-sm text-slate-600">
            Solda normal görüntü, sağda analiz sonucu. Kırmızı bölgeler sorunlu alanları gösterir.
          </p>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <div className="overflow-hidden rounded-xl border border-slate-200">
              <Image src="/images/tarla-oncesi.png" alt="Tarla — normal havadan görüntü" width={600} height={450} className="w-full" />
              <div className="bg-white px-4 py-2 text-center text-sm font-medium text-slate-700">Normal Görüntü</div>
            </div>
            <div className="overflow-hidden rounded-xl border border-emerald-200">
              <Image src="/images/tarla-sonrasi.png" alt="Tarla — analiz sonucu (ısı haritası)" width={600} height={450} className="w-full" />
              <div className="bg-emerald-50 px-4 py-2 text-center text-sm font-medium text-emerald-700">Analiz Sonucu</div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== Tasarruf Mesajı ===== */}
      <section className="py-10 sm:py-14">
        <div className="mx-auto max-w-4xl px-4">
          <div className="rounded-2xl bg-gradient-to-br from-emerald-600 to-emerald-700 p-6 text-white sm:p-8">
            <h2 className="text-xl font-bold sm:text-2xl">Tarlanın tamamını ilaçlamayın!</h2>
            <p className="mt-2 text-sm leading-relaxed text-emerald-100 sm:text-base">
              Sadece hastalıklı veya otlu bölgeyi ilaçlayın. Su ve gübre kullanımından tasarruf edin.
              Haftalık takiple tarlanızın durumunu yakından izleyin.
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {[
                { title: "Hedefli İlaçlama", desc: "Tarlayı komple değil, sadece sorunlu bölgeyi ilaçlayın" },
                { title: "Su Tasarrufu", desc: "Nereye ne kadar su gerektiğini bilin" },
                { title: "Gübre Tasarrufu", desc: "Azot durumunu bölge bölge görün, gereksiz gübrelemeden kaçının" },
              ].map((item) => (
                <div key={item.title} className="rounded-xl bg-white/10 p-3.5">
                  <h3 className="text-sm font-semibold">{item.title}</h3>
                  <p className="mt-1 text-xs text-emerald-100">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ===== 5 Adım İş Akışı ===== */}
      <section id="nasil-calisir" className="bg-slate-50 py-10 sm:py-14">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center text-2xl font-bold text-slate-900 sm:text-3xl">Uçtan Uca İş Akışı</h2>
          <p className="mx-auto mt-1 max-w-lg text-center text-sm text-slate-500">
            Drone &rarr; Harita &rarr; Analiz &rarr; Zonlama &rarr; Rapor
          </p>
          <div className="mt-6 grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {[
              { step: "1", title: "Tarama Uçuşu", desc: "Drone ile tarla taranır. Özel kamera görüntüleri hafıza kartına kaydedilir.", color: "bg-emerald-600" },
              { step: "2", title: "Harita Oluşturma", desc: "Görüntüler merkez bilgisayarda işlenir, tarlanın sağlık haritası çıkarılır.", color: "bg-emerald-500" },
              { step: "3", title: "Analiz", desc: "Hastalık, ot, böcek, su ve azot durumu tek tek incelenir.", color: "bg-amber-500" },
              { step: "4", title: "Zonlama", desc: "Sorunlu bölgeler işaretlenir. Hedefli müdahale planı oluşturulur.", color: "bg-orange-500" },
              { step: "5", title: "Rapor", desc: "Harita, erken teşhis, öneriler ve haftalık takip raporunuz hazırlanır.", color: "bg-blue-600" },
            ].map((item) => (
              <div key={item.step} className="rounded-xl border border-slate-200 bg-white p-4">
                <div className={`mb-2.5 flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold text-white ${item.color}`}>
                  {item.step}
                </div>
                <h3 className="text-sm font-semibold text-slate-900">{item.title}</h3>
                <p className="mt-1 text-xs leading-relaxed text-slate-500">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== Ürün Senaryoları ===== */}
      <section className="py-10 sm:py-14">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center text-2xl font-bold text-slate-900 sm:text-3xl">Her Ürün İçin Ayrı Çıktı</h2>
          <p className="mx-auto mt-1 max-w-lg text-center text-sm text-slate-500">Mısır, pamuk ve diğer bitkilerde aynı platform</p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-slate-200 p-5">
              <h3 className="text-lg font-bold text-slate-900">Mısır</h3>
              <ul className="mt-2 space-y-1.5 text-sm text-slate-600">
                <li className="flex gap-2"><IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />Bitki gelişim farkı — hastalık, mantar var mı?</li>
                <li className="flex gap-2"><IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />Yabancı ot kümeleri nerede, ne kadar?</li>
                <li className="flex gap-2"><IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />Su stresi / besin eksikliği tespiti</li>
                <li className="flex gap-2"><IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />Koçan döneminde riskli alanların işaretlenmesi</li>
              </ul>
            </div>
            <div className="rounded-xl border border-slate-200 p-5">
              <h3 className="text-lg font-bold text-slate-900">Pamuk</h3>
              <ul className="mt-2 space-y-1.5 text-sm text-slate-600">
                <li className="flex gap-2"><IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />Çıkış ve bitki sıklığı kontrolü (erken dönem)</li>
                <li className="flex gap-2"><IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />Susuzluk, sıcak ve besleme stresi alanları</li>
                <li className="flex gap-2"><IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />Ot baskısı ve tekrarlayan problem noktaları</li>
                <li className="flex gap-2"><IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />Hasada kadar haftalık karşılaştırma</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ===== Fiyatlandırma ===== */}
      <section className="bg-slate-50 py-10 sm:py-14">
        <div className="mx-auto max-w-5xl px-4">
          <h2 className="text-center text-2xl font-bold text-slate-900 sm:text-3xl">Fiyatlandırma</h2>
          <p className="mx-auto mt-1 text-center text-sm text-slate-500">Dönüm bazlı, bireysel ve kooperatif için iki model</p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {/* Model A */}
            <div className="overflow-hidden rounded-xl border-2 border-emerald-500 bg-white">
              <div className="bg-emerald-600 px-5 py-3 text-white">
                <h3 className="text-lg font-bold">Sezonluk Abonelik</h3>
                <p className="text-xs text-emerald-100">3-4 ay, 12-17 tarama + analiz</p>
              </div>
              <div className="p-5">
                <ul className="space-y-1.5 text-sm text-slate-600">
                  <li>7 veya 10 gün arayla tarama</li>
                  <li>Liste fiyata göre <strong className="text-emerald-700">%20 tasarruf</strong></li>
                  <li>Peşin ödeme</li>
                </ul>
                <div className="mt-4 rounded-lg bg-slate-50 p-3 text-sm">
                  <div className="text-slate-500">Örnek (1 dönüm, 10 tarama):</div>
                  <div className="text-lg font-bold text-slate-900">200 TL <span className="text-sm font-normal text-slate-400 line-through">250 TL</span></div>
                </div>
              </div>
            </div>
            {/* Model B */}
            <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
              <div className="bg-blue-600 px-5 py-3 text-white">
                <h3 className="text-lg font-bold">Tek Seferlik Tarama</h3>
                <p className="text-xs text-blue-100">1 tarama + analiz raporu</p>
              </div>
              <div className="p-5">
                <ul className="space-y-1.5 text-sm text-slate-600">
                  <li>Denemek veya tek seferlik kontrol için</li>
                  <li>Kooperatif: toplu planlama + hacim indirimi</li>
                  <li>Her üyeye ayrı rapor + kooperatif özeti</li>
                </ul>
                <div className="mt-4 rounded-lg bg-slate-50 p-3 text-sm">
                  <div className="text-slate-500">Örnek (1 dönüm, 1 tarama):</div>
                  <div className="text-lg font-bold text-slate-900">50 TL</div>
                </div>
              </div>
            </div>
          </div>
          <p className="mt-3 text-center text-xs text-slate-400">
            Fiyatlar &ldquo;örnek&rdquo;tir: bölge, alan, uçuş sıklığı ve hizmet kapsamına göre netleşir.
          </p>
        </div>
      </section>

      {/* ===== 7 Katman Görseli ===== */}
      <section className="py-10 sm:py-14">
        <div className="mx-auto max-w-6xl px-4">
          <div className="grid items-center gap-6 lg:grid-cols-2">
            <Image
              src="/images/katman-tarla.png"
              alt="7 analiz katmanı — tarla üzerinde"
              width={800}
              height={500}
              className="w-full rounded-xl"
            />
            <div>
              <h2 className="text-2xl font-bold text-slate-900 sm:text-3xl">
                Tek Taramada 7 Farklı Analiz
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-600 sm:text-base">
                Hem daha az masraf yapın, hem de ürün veriminiz artsın.
                Her bölge ayrı ayrı değerlendirilir, sorunlu alanlar harita üzerinde işaretlenir.
              </p>
              <ul className="mt-3 space-y-1.5">
                {[
                  "Sorunlu alanlar harita üzerinde gösterilir",
                  "Uzmanlar sonuçları kontrol eder, rapor yazar",
                  "Rapor telefonunuza bildirim olarak gelir",
                  "Çiftçi 30 saniyede anlasın diye tasarlandı",
                ].map((t) => (
                  <li key={t} className="flex items-start gap-2 text-sm text-slate-700">
                    <IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ===== CTA ===== */}
      <section className="bg-emerald-600 py-10 sm:py-12">
        <div className="mx-auto max-w-3xl px-4 text-center">
          <h2 className="text-2xl font-bold text-white sm:text-3xl">Tarlanızın durumunu öğrenin</h2>
          <p className="mt-2 text-sm text-emerald-100">
            Ücretsiz üye olun, tarlanızı ekleyin ve drone ile tarla analizi deneyimini yaşayın.
          </p>
          <div className="mt-5 flex flex-col items-center gap-2.5 sm:flex-row sm:justify-center">
            <Link
              href="/register"
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50 sm:w-auto"
            >
              Ücretsiz Üye Ol
              <IconArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/login"
              className="inline-flex w-full items-center justify-center rounded-lg border border-emerald-400 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-500 sm:w-auto"
            >
              Giriş Yap
            </Link>
          </div>
        </div>
      </section>

      {/* ===== Footer ===== */}
      <footer className="border-t border-slate-200 bg-white py-6">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-600">
              <IconLeaf className="h-3.5 w-3.5 text-white" />
            </div>
            <span className="font-semibold text-slate-900">TarlaAnaliz</span>
          </div>
          <nav className="flex flex-wrap items-center gap-4 text-sm text-slate-500">
            <Link href="/login" className="hover:text-slate-900">Giriş Yap</Link>
            <Link href="/register" className="hover:text-slate-900">Üye Ol</Link>
            <Link href="#nasil-calisir" className="hover:text-slate-900">Nasıl Çalışır?</Link>
          </nav>
          <p className="text-xs text-slate-400">&copy; 2026 TarlaAnaliz</p>
        </div>
      </footer>
    </div>
  );
}
