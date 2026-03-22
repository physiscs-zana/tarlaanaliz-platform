/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* Redirect: /review/{id} → /reviews/{id} (kanonik sayfa) */

import { redirect } from "next/navigation";

interface Props {
  readonly params: { readonly reviewId: string };
}

export default function ReviewRedirectPage({ params }: Props) {
  redirect(`/reviews/${params.reviewId}`);
}
