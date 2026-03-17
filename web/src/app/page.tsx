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
/* SVG icon components                                                */
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
      {/* ============ Navbar ============ */}
      <nav className="sticky top-0 z-40 border-b border-slate-100 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600">
              <IconLeaf className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold text-slate-900">TarlaAnaliz</span>
          </Link>
          <div className="flex items-center gap-2 sm:gap-3">
            <Link href="/login" className="rounded-md px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100">
              Giriş Yap
            </Link>
            <Link href="/register" className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-emerald-700 sm:px-4">
              Üye Ol
            </Link>
          </div>
        </div>
      </nav>

      {/* ============ Hero ============ */}
      <section className="relative overflow-hidden">
        <div className="mx-auto max-w-6xl px-4 pb-10 pt-8 sm:pb-14 sm:pt-12">
          <div className="grid items-center gap-8 lg:grid-cols-2 lg:gap-12">
            {/* Text */}
            <div>
              <div className="mb-4 inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 sm:text-sm">
                Drone ile Tarla Tarama
              </div>
              <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl">
                Tarlanızın sağlığını
                <span className="block text-emerald-600">havadan görün</span>
              </h1>
              <p className="mt-4 max-w-lg text-base leading-relaxed text-slate-600 sm:text-lg">
                TarlaAnaliz, tarlanızı drone ile tarayarak hastalık, zararlı böcek,
                su eksikliği ve verim kaybını erken tespit eder. Sonuçları uzmanlar
                inceler, size anlaşılır bir rapor sunar.
              </p>
              <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                <Link
                  href="/register"
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-md shadow-emerald-600/20 transition hover:bg-emerald-700 sm:text-base"
                >
                  Ücretsiz Üye Ol
                  <IconArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="#nasil-calisir"
                  className="inline-flex items-center justify-center rounded-lg border border-slate-300 px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 sm:text-base"
                >
                  Nasıl Çalışır?
                </Link>
              </div>
            </div>
            {/* Hero image */}
            <div className="relative">
              <Image
                src="/images/hero-drone.png"
                alt="Drone ile tarla tarama — ısı haritası görüntüsü"
                width={800}
                height={500}
                className="w-full rounded-xl shadow-lg"
                priority
              />
            </div>
          </div>
        </div>
      </section>

      {/* ============ Stats ============ */}
      <section className="border-y border-slate-100 bg-slate-50">
        <div className="mx-auto grid max-w-4xl grid-cols-3 divide-x divide-slate-200 px-4 py-6 sm:py-8">
          {[
            { value: "81", label: "İl Kapsama" },
            { value: "7/24", label: "Destek" },
            { value: "%95", label: "Tespit Doğruluğu" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-2xl font-bold text-emerald-600 sm:text-3xl">{stat.value}</div>
              <div className="mt-0.5 text-xs text-slate-500 sm:text-sm">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ============ Neler Tespit Edilir? (with infographic) ============ */}
      <section className="py-12 sm:py-16">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center text-2xl font-bold text-slate-900 sm:text-3xl">
            Tarlanızda Neler Tespit Edilir?
          </h2>
          <p className="mx-auto mt-2 max-w-xl text-center text-sm text-slate-600 sm:text-base">
            Drone ile çekilen özel kamera görüntüleri yapay zeka tarafından analiz edilir.
          </p>

          <div className="mt-8 grid items-center gap-8 lg:grid-cols-2">
            {/* Infographic image */}
            <Image
              src="/images/analiz-infografik.png"
              alt="Drone tarla tarama — 7 farklı analiz katmanı"
              width={900}
              height={550}
              className="w-full rounded-xl"
            />
            {/* Detection list */}
            <div className="space-y-3">
              {[
                { title: "Bitki Hastalığı Tespiti", desc: "Yaprak yanıklığı, mantar ve virüs belirtilerini erkenden görür." },
                { title: "Zararlı Böcek Tespiti", desc: "Böcek zararı olan bölgeleri harita üzerinde işaretler." },
                { title: "Su Eksikliği", desc: "Hangi bölgelerde sulama yetersiz, hangilerinde fazla — hepsini gösterir." },
                { title: "Azot Durumu", desc: "Gübreleme ihtiyacını bölge bölge belirler, gereksiz masrafı önler." },
                { title: "Bitki Canlılığı (NDVI)", desc: "Tarlanızın genel sağlık durumunu renk haritasıyla özetler." },
                { title: "Yabancı Ot Tespiti", desc: "Ot basan bölgeleri tespit eder, hedefe yönelik ilaçlama yapmanızı sağlar." },
              ].map((item) => (
                <div key={item.title} className="flex gap-3">
                  <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                    <IconCheck className="h-3.5 w-3.5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 sm:text-base">{item.title}</h3>
                    <p className="text-xs text-slate-500 sm:text-sm">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ============ Önce / Sonra ============ */}
      <section className="bg-slate-50 py-12 sm:py-16">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center text-2xl font-bold text-slate-900 sm:text-3xl">
            Gözle Görünmeyen Sorunları Ortaya Çıkarır
          </h2>
          <p className="mx-auto mt-2 max-w-xl text-center text-sm text-slate-600 sm:text-base">
            Aynı tarla — solda normal görüntü, sağda drone analiz sonucu.
            Kırmızı bölgeler sorunlu alanları gösterir.
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            <div className="overflow-hidden rounded-xl border border-slate-200">
              <Image
                src="/images/tarla-oncesi.png"
                alt="Tarla — normal havadan görüntü (RGB)"
                width={600}
                height={450}
                className="w-full"
              />
              <div className="bg-white px-4 py-2.5 text-center text-sm font-medium text-slate-700">
                Normal Görüntü
              </div>
            </div>
            <div className="overflow-hidden rounded-xl border border-emerald-200">
              <Image
                src="/images/tarla-sonrasi.png"
                alt="Tarla — drone analiz sonucu (NDVI ısı haritası)"
                width={600}
                height={450}
                className="w-full"
              />
              <div className="bg-emerald-50 px-4 py-2.5 text-center text-sm font-medium text-emerald-700">
                Analiz Sonucu (Sorunlu Alanlar Kırmızı)
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============ Nasıl Çalışır? ============ */}
      <section id="nasil-calisir" className="py-12 sm:py-16">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center text-2xl font-bold text-slate-900 sm:text-3xl">
            4 Adımda Tarla Analizi
          </h2>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { step: "1", title: "Üye Olun", desc: "Telefon numaranız ve 6 haneli şifre ile üye olun. E-posta gerekmez." },
              { step: "2", title: "Tarlanızı Ekleyin", desc: "Haritadan tarlanızın sınırlarını çizin veya ada/parsel numarası girin." },
              { step: "3", title: "Tarama İsteyin", desc: "Analiz talebinizi oluşturun, ödemeyi yapın. Uygun havada tarlanız taranır." },
              { step: "4", title: "Raporunuzu Alın", desc: "Yapay zeka ve uzmanlar tarlanızı inceleyip size anlaşılır rapor sunar." },
            ].map((item) => (
              <div key={item.step} className="rounded-xl border border-slate-200 bg-white p-5">
                <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-full bg-emerald-600 text-base font-bold text-white">
                  {item.step}
                </div>
                <h3 className="mb-1 text-base font-semibold text-slate-900">{item.title}</h3>
                <p className="text-sm leading-relaxed text-slate-500">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ Katman Görseli + Neden TarlaAnaliz? ============ */}
      <section className="bg-slate-50 py-12 sm:py-16">
        <div className="mx-auto max-w-6xl px-4">
          <div className="grid items-center gap-8 lg:grid-cols-2">
            <Image
              src="/images/katman-kupu.png"
              alt="Multispektral analiz katmanları — NDVI, hastalık, zararlı, su eksikliği"
              width={700}
              height={500}
              className="w-full rounded-xl"
            />
            <div>
              <h2 className="text-2xl font-bold text-slate-900 sm:text-3xl">
                Tek Taramada 7 Farklı Analiz
              </h2>
              <p className="mt-3 text-sm leading-relaxed text-slate-600 sm:text-base">
                Drone özel kameralarla tarlanızı tek seferde tarar.
                Yapay zeka bu görüntüleri 7 farklı katmanda analiz eder:
                bitki sağlığı, hastalık, zararlı böcek, su durumu, azot ihtiyacı,
                yabancı ot ve genel verim tahmini.
              </p>
              <ul className="mt-4 space-y-2">
                {[
                  "Her bölge ayrı ayrı değerlendirilir",
                  "Sorunlu alanlar harita üzerinde işaretlenir",
                  "Uzmanlar sonuçları kontrol edip rapor yazar",
                  "Rapor telefonunuza bildirim olarak gelir",
                ].map((text) => (
                  <li key={text} className="flex items-start gap-2 text-sm text-slate-700 sm:text-base">
                    <IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                    {text}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ============ CTA ============ */}
      <section className="bg-emerald-600 py-12 sm:py-16">
        <div className="mx-auto max-w-3xl px-4 text-center">
          <h2 className="text-2xl font-bold text-white sm:text-3xl">
            Tarlanızın durumunu öğrenin
          </h2>
          <p className="mt-2 text-sm text-emerald-100 sm:text-base">
            Ücretsiz üye olun, tarlanızı ekleyin ve drone ile analiz deneyimini yaşayın.
          </p>
          <div className="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Link
              href="/register"
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-white px-6 py-3 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50 sm:w-auto sm:text-base"
            >
              Ücretsiz Üye Ol
              <IconArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/login"
              className="inline-flex w-full items-center justify-center rounded-lg border border-emerald-400 px-6 py-3 text-sm font-semibold text-white transition hover:bg-emerald-500 sm:w-auto sm:text-base"
            >
              Giriş Yap
            </Link>
          </div>
        </div>
      </section>

      {/* ============ Footer ============ */}
      <footer className="border-t border-slate-200 bg-white py-8">
        <div className="mx-auto max-w-6xl px-4">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-600">
                <IconLeaf className="h-3.5 w-3.5 text-white" />
              </div>
              <span className="font-semibold text-slate-900">TarlaAnaliz</span>
            </div>
            <nav className="flex flex-wrap items-center justify-center gap-4 text-sm text-slate-500 sm:gap-6">
              <Link href="/login" className="transition hover:text-slate-900">Giriş Yap</Link>
              <Link href="/register" className="transition hover:text-slate-900">Üye Ol</Link>
              <Link href="#nasil-calisir" className="transition hover:text-slate-900">Nasıl Çalışır?</Link>
            </nav>
            <p className="text-xs text-slate-400">&copy; 2026 TarlaAnaliz</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
