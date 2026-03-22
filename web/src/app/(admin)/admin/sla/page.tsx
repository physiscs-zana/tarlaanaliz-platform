/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: SLA artik /audit sayfasinda denetim kayitlariyla birlikte. */

import { redirect } from "next/navigation";

export default function SlaRedirectPage() {
  redirect("/audit");
}
