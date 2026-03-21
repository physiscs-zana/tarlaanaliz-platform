/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* Redirect: /calibration merged into /qc */
import { redirect } from "next/navigation";

export default function CalibrationRedirect() {
  redirect("/qc");
}
