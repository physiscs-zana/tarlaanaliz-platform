/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: Profil sayfası — kullanıcı bilgileri ve oturum yönetimi. */

"use client";

import { useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie, decodeJwtPayload } from "@/lib/api";

interface ProfileData {
  phone: string;
  roles: string[];
  userId: string;
}

export default function FarmerProfilePage() {
  const [profile, setProfile] = useState<ProfileData | null>(null);

  useEffect(() => {
    const token = getTokenFromCookie();
    if (!token) return;
    const claims = decodeJwtPayload(token);
    setProfile({
      phone: (claims.phone as string) ?? "",
      roles: (claims.roles as string[]) ?? [],
      userId: (claims.user_id as string) ?? "",
    });
  }, []);

  if (!profile) {
    return <div className="py-12 text-center text-sm text-slate-500">Yükleniyor...</div>;
  }

  const maskPhone = (p: string) => {
    if (p.length < 4) return p;
    return p.slice(0, -4).replace(/./g, "*") + p.slice(-4);
  };

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Profilim</h1>
      <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-3">
        <div>
          <span className="text-sm text-slate-500">Telefon</span>
          <p className="text-base font-medium text-slate-900">{maskPhone(profile.phone)}</p>
        </div>
        <div>
          <span className="text-sm text-slate-500">Rol</span>
          <p className="text-base font-medium text-slate-900">
            {profile.roles.map((r) => r.replace(/_/g, " ")).join(", ")}
          </p>
        </div>
        <div>
          <span className="text-sm text-slate-500">Kullanıcı ID</span>
          <p className="font-mono text-xs text-slate-400">{profile.userId}</p>
        </div>
      </div>
    </section>
  );
}
