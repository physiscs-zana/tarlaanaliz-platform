/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-081: QC ve kalibrasyon artik /audit sayfasinda birlesti. */

import { redirect } from "next/navigation";

export default function QcRedirectPage() {
  redirect("/audit");
}
