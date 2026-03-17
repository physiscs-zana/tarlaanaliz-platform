/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: health endpoint trace-id başlıklarını geri yansıtır. */

import { NextRequest, NextResponse } from "next/server";

export async function GET(_request: NextRequest) {
  // [FIX-6] Only return minimal status. Service name, timestamps, and trace IDs
  // leak deployment topology and timing information to external callers.
  // Internal monitoring should use a dedicated sidecar or internal-only route.
  return NextResponse.json(
    { status: "ok" },
    {
      status: 200,
      headers: {
        "cache-control": "no-store",
      },
    }
  );
}
