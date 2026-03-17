// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"use client";

import { useRouter } from "next/navigation";

import { clearAuthStorage } from "@/lib/authStorage";
import { COOKIE_TOKEN_KEY, COOKIE_ROLE_KEY } from "@/lib/constants";
import { Button } from "@/components/ui/button";

export function LogoutButton() {
  const router = useRouter();

  const handleLogout = () => {
    clearAuthStorage();
    if (typeof document !== "undefined") {
      document.cookie = `${COOKIE_TOKEN_KEY}=;path=/;max-age=0`;
      document.cookie = `${COOKIE_ROLE_KEY}=;path=/;max-age=0`;
    }
    router.push("/login");
  };

  return (
    <Button variant="ghost" size="sm" className="w-full justify-start text-slate-500 hover:text-slate-900" onClick={handleLogout}>
      Çıkış Yap
    </Button>
  );
}
