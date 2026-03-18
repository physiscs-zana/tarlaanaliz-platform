// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// Gerçek Next.js route'larıyla senkronize. Middleware ROLE_PREFIXES ile uyumlu.
// KR-062: Tek kaynak gerçek — route tanımları burada kanonik, middleware import eder.

export const routes = {
  login: '/login',
  register: '/register',
  forbidden: '/forbidden',

  // Farmer routes
  benimSayfam: '/benim-sayfam',
  farmerHome: '/benim-sayfam',
  fields: '/fields',
  missions: '/missions',
  subscriptions: '/subscriptions',
  results: '/results',
  payments: '/payments',
  farmerProfile: '/profile',

  // Expert routes
  expertHome: '/queue',
  queue: '/queue',
  reviews: '/reviews',
  expertProfile: '/expert/profile',
  expertSettings: '/expert/settings',
  expertSla: '/expert/sla',

  // Pilot routes
  pilotHome: '/pilot/missions',
  pilotMissions: '/pilot/missions',
  planner: '/planner',
  capacity: '/capacity',
  weatherBlock: '/weather-block',
  pilotProfile: '/pilot/profile',
  pilotSettings: '/pilot/settings',

  // Cooperative routes (KR-014)
  coopMembers: '/coop/members',
  coopInvite: '/coop/invite',
  coopFields: '/coop/fields',
  coopDashboard: '/coop/dashboard',

  // İl Operatörü routes (KR-083)
  ilDashboard: '/il/dashboard',
  ilMetrics: '/il/metrics',

  // Billing Admin routes (KR-033)
  billingPayments: '/billing/payments',
  billingRefunds: '/billing/refunds',

  // Admin routes
  adminHome: '/analytics',
  analytics: '/analytics',
  audit: '/audit',
  auditViewer: '/audit-viewer',
  pricing: '/pricing',
  priceManagement: '/price-management',
  adminSla: '/admin/sla',
  users: '/users',
  adminPayments: '/admin/payments',
  calibration: '/calibration',
  qc: '/qc',
  apiKeys: '/api-keys',
  experts: '/experts',
  expertManagement: '/expert-management',
  pilots: '/pilots',
  dashboard: '/dashboard',
} as const;

export type AppRoute = (typeof routes)[keyof typeof routes];

/** Public paths — no auth required. */
export const PUBLIC_PATHS = new Set<string>([routes.login, routes.register, '/', '/api/health', routes.forbidden]);

/**
 * KR-063: Role group → allowed path prefixes mapping (kanonik kaynak).
 * Middleware bu matrisi import eder.
 * Detaylı SSOT rolleri (FARMER_SINGLE, COOP_OWNER vb.) useAuth.ts'deki ROLE_TO_GROUP ile gruba eşlenir.
 */
export const ROLE_PREFIXES: Record<string, readonly string[]> = {
  admin: [
    routes.analytics, routes.audit, routes.auditViewer, routes.pricing,
    routes.priceManagement, routes.adminSla, routes.users, routes.adminPayments,
    routes.calibration, routes.qc, routes.apiKeys, routes.experts,
    routes.expertManagement, routes.pilots, routes.dashboard,
    // KR-083: İl Operatörü (admin grubunda, PII görmez)
    routes.ilDashboard, routes.ilMetrics,
    // KR-033: Billing Admin
    routes.billingPayments, routes.billingRefunds,
  ],
  expert: [routes.queue, '/review', routes.reviews, routes.expertSettings, routes.expertSla, routes.expertProfile],
  farmer: [
    routes.benimSayfam, routes.fields, routes.missions, routes.subscriptions, routes.results, routes.payments, routes.farmerProfile,
    // KR-014: Kooperatif yönetim sayfaları (COOP_OWNER, COOP_ADMIN farmer grubunda)
    routes.coopMembers, routes.coopInvite, routes.coopFields, routes.coopDashboard,
  ],
  pilot: [routes.pilotMissions, routes.planner, routes.capacity, routes.weatherBlock, routes.pilotSettings, routes.pilotProfile],
};
