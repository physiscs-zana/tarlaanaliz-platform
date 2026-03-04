// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// Gerçek Next.js route'larıyla senkronize. Middleware ROLE_PREFIXES ile uyumlu.

export const routes = {
  login: '/login',
  register: '/register',
  forbidden: '/forbidden',

  // Farmer routes
  farmerHome: '/fields',
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
