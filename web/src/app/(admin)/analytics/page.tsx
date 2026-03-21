/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* Redirect: /analytics merged into /dashboard */
import { redirect } from "next/navigation";

export default function AnalyticsRedirect() {
  redirect("/dashboard");
}
