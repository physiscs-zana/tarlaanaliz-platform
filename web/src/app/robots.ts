/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: Platform dışa açık endpoint'lerde kontrollü erişim bildirimi yayınlar. */

import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/api/", "/admin/", "/expert/", "/pilot/", "/benim-sayfam", "/fields/", "/missions/", "/results/", "/payments/", "/profile/", "/subscriptions/"],
    },
    sitemap: "https://tarlaanaliz.com/sitemap.xml",
  };
}
