/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: role tabanlı yönlendirme + public landing page. */

import { cookies } from "next/headers";
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
/* SVG icon components (inline — no external deps)                    */
/* ------------------------------------------------------------------ */
function IconDrone({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M3 8l3.5 3.5M20.5 8L17 11.5M3 16l3.5-3.5M20.5 16L17 12.5" />
      <circle cx="3" cy="8" r="1.5" fill="currentColor" />
      <circle cx="20.5" cy="8" r="1.5" fill="currentColor" />
      <circle cx="3" cy="16" r="1.5" fill="currentColor" />
      <circle cx="20.5" cy="16" r="1.5" fill="currentColor" />
    </svg>
  );
}

function IconLeaf({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66.95-2.3c.48.17.98.3 1.34.3C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75" />
    </svg>
  );
}

function IconChart({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 3v18h18" />
      <path d="M7 16l4-8 4 4 5-9" />
    </svg>
  );
}

function IconShield({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}

function IconMoney({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="1" x2="12" y2="23" />
      <path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
    </svg>
  );
}

function IconUsers({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
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

/* ------------------------------------------------------------------ */
/* Landing Page                                                       */
/* ------------------------------------------------------------------ */
export default function HomePage() {
  tryRoleRedirect();

  return (
    <div className="min-h-screen bg-white">
      {/* ============================================================ */}
      {/* Navbar                                                       */}
      {/* ============================================================ */}
      <nav className="sticky top-0 z-40 border-b border-slate-100 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600">
              <IconLeaf className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-bold text-slate-900">TarlaAnaliz</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="hidden rounded-md px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 sm:inline-flex"
            >
              Giriş Yap
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-700"
            >
              Ücretsiz Üye Ol
            </Link>
          </div>
        </div>
      </nav>

      {/* ============================================================ */}
      {/* Hero                                                         */}
      {/* ============================================================ */}
      <section className="relative overflow-hidden bg-gradient-to-b from-emerald-50 via-white to-white">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-emerald-100/40 via-transparent to-transparent" />
        <div className="relative mx-auto max-w-6xl px-4 pb-20 pt-16 sm:px-6 sm:pb-28 sm:pt-24">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-1.5 text-sm font-medium text-emerald-700">
              <IconDrone className="h-4 w-4" />
              Drone ile Tarla Analizi
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
              Tarlanızın sağlığını
              <span className="mt-1 block text-emerald-600">havadan analiz edin</span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-slate-600 sm:text-xl">
              TarlaAnaliz, drone ile multispektral görüntüleme yaparak tarlalarınızdaki hastalık,
              sulama eksikliği ve verim kaybını erken tespit eder.
              Uzman agronomi raporlarıyla bilinçli kararlar alın.
            </p>
            <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
              <Link
                href="/register"
                className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-emerald-600/20 transition hover:bg-emerald-700 hover:shadow-emerald-600/30 sm:w-auto"
              >
                Hemen Üye Ol
                <IconArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="#nasil-calisir"
                className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-8 py-3.5 text-base font-semibold text-slate-700 transition hover:bg-slate-50 sm:w-auto"
              >
                Nasıl Çalışır?
              </Link>
            </div>
          </div>

          {/* Stats strip */}
          <div className="mx-auto mt-16 grid max-w-2xl grid-cols-3 gap-8 sm:mt-20">
            {[
              { value: "81", label: "İl Kapsama" },
              { value: "7/24", label: "Analiz Desteği" },
              { value: "%95", label: "Tespit Doğruluğu" },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl font-bold text-emerald-600 sm:text-4xl">{stat.value}</div>
                <div className="mt-1 text-sm text-slate-500">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* Features                                                     */}
      {/* ============================================================ */}
      <section className="bg-white py-20 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              Neden TarlaAnaliz?
            </h2>
            <p className="mt-4 text-lg text-slate-600">
              Geleneksel tarla kontrolünün ötesine geçin. Drone teknolojisi ve yapay zeka
              ile tarlanızı profesyonelce izleyin.
            </p>
          </div>

          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: <IconDrone className="h-6 w-6" />,
                title: "Drone ile Görüntüleme",
                description:
                  "Profesyonel pilotlarımız tarlanızı multispektral kameralarla tarar. NDVI, NDRE ve termal haritalar oluşturulur.",
              },
              {
                icon: <IconLeaf className="h-6 w-6" />,
                title: "Bitki Sağlığı Analizi",
                description:
                  "Yapay zeka modelleri hastalık belirtilerini, stres bölgelerini ve sulama sorunlarını otomatik olarak tespit eder.",
              },
              {
                icon: <IconChart className="h-6 w-6" />,
                title: "Uzman Agronomi Raporu",
                description:
                  "Deneyimli agronomistlerimiz AI sonuçlarını inceler ve size özel tarla raporu hazırlar.",
              },
              {
                icon: <IconMoney className="h-6 w-6" />,
                title: "Uygun Fiyat",
                description:
                  "Dekar başına uygun fiyatlandırma. Kooperatif üyeleri için ek indirimler. Ödemeyi online yapın.",
              },
              {
                icon: <IconShield className="h-6 w-6" />,
                title: "Veri Güvenliği",
                description:
                  "KVKK uyumlu altyapı. Tarla koordinatlarınız ve kişisel bilgileriniz şifrelenmiş ortamda saklanır.",
              },
              {
                icon: <IconUsers className="h-6 w-6" />,
                title: "Kooperatif Desteği",
                description:
                  "Bireysel veya kooperatif üyesi olarak kullanın. Kooperatif yöneticileri tüm tarlaları tek panelden izler.",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="group rounded-xl border border-slate-200 bg-white p-6 transition hover:border-emerald-200 hover:shadow-md"
              >
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 transition group-hover:bg-emerald-100">
                  {feature.icon}
                </div>
                <h3 className="mb-2 text-lg font-semibold text-slate-900">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-slate-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* How it works                                                 */}
      {/* ============================================================ */}
      <section id="nasil-calisir" className="bg-slate-50 py-20 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              4 Adımda Tarla Analizi
            </h2>
            <p className="mt-4 text-lg text-slate-600">
              Kayıt olun, tarlanızı ekleyin, tarama talebi oluşturun, raporunuzu alın.
            </p>
          </div>

          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                step: "1",
                title: "Üye Olun",
                description: "Telefon numaranız ve 6 haneli PIN ile saniyeler içinde üye olun. E-posta gerekmez.",
              },
              {
                step: "2",
                title: "Tarlanızı Ekleyin",
                description: "Harita üzerinden tarlanızın sınırlarını çizin veya kadastro numarasıyla otomatik tanımlayın.",
              },
              {
                step: "3",
                title: "Tarama Talebi Oluşturun",
                description: "Analiz görevini oluşturun, ödemenizi yapın. Uygun havada pilotumuz tarlanızı tarar.",
              },
              {
                step: "4",
                title: "Raporunuzu Alın",
                description: "AI analizi ve uzman incelemesiyle hazırlanan detaylı tarla raporunuzu görüntüleyin.",
              },
            ].map((item) => (
              <div key={item.step} className="relative rounded-xl bg-white p-6 shadow-sm">
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-emerald-600 text-lg font-bold text-white">
                  {item.step}
                </div>
                <h3 className="mb-2 text-lg font-semibold text-slate-900">{item.title}</h3>
                <p className="text-sm leading-relaxed text-slate-600">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* Who is it for?                                               */}
      {/* ============================================================ */}
      <section className="bg-white py-20 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              Kimler Kullanıyor?
            </h2>
          </div>

          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                title: "Bireysel Çiftçiler",
                description:
                  "Kendi tarlasını profesyonelce izlemek isteyen çiftçiler. Küçük veya büyük fark etmez — her tarla analiz edilebilir.",
                color: "emerald",
              },
              {
                title: "Kooperatifler",
                description:
                  "Üyelerinin tarlalarını toplu yönetin. Kooperatif panelinden tüm analiz sonuçlarını takip edin, toplu indirimlerden yararlanın.",
                color: "brand",
              },
              {
                title: "Ziraat Mühendisleri",
                description:
                  "Uzman portal üzerinden AI analizlerini inceleyin, tarla raporları hazırlayın ve çiftçilere danışmanlık verin.",
                color: "amber",
              },
            ].map((persona) => (
              <div
                key={persona.title}
                className="rounded-xl border border-slate-200 bg-gradient-to-b from-slate-50 to-white p-8"
              >
                <h3 className="mb-3 text-xl font-semibold text-slate-900">{persona.title}</h3>
                <p className="text-sm leading-relaxed text-slate-600">{persona.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* CTA                                                          */}
      {/* ============================================================ */}
      <section className="bg-emerald-600 py-20 sm:py-24">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Tarlanızın potansiyelini keşfedin
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-emerald-100">
            Ücretsiz üye olun, ilk tarlanızı ekleyin ve drone ile tarla analizi deneyimini yaşayın.
          </p>
          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/register"
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-white px-8 py-3.5 text-base font-semibold text-emerald-700 shadow-lg transition hover:bg-emerald-50 sm:w-auto"
            >
              Ücretsiz Üye Ol
              <IconArrowRight className="h-5 w-5" />
            </Link>
            <Link
              href="/login"
              className="inline-flex w-full items-center justify-center rounded-lg border border-emerald-400 px-8 py-3.5 text-base font-semibold text-white transition hover:bg-emerald-500 sm:w-auto"
            >
              Giriş Yap
            </Link>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* Footer                                                       */}
      {/* ============================================================ */}
      <footer className="border-t border-slate-200 bg-white py-12">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600">
                <IconLeaf className="h-4 w-4 text-white" />
              </div>
              <span className="font-semibold text-slate-900">TarlaAnaliz</span>
            </div>
            <nav className="flex flex-wrap items-center justify-center gap-6 text-sm text-slate-500">
              <Link href="/login" className="transition hover:text-slate-900">Giriş Yap</Link>
              <Link href="/register" className="transition hover:text-slate-900">Üye Ol</Link>
              <Link href="#nasil-calisir" className="transition hover:text-slate-900">Nasıl Çalışır?</Link>
            </nav>
            <p className="text-sm text-slate-400">
              &copy; 2026 TarlaAnaliz
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
