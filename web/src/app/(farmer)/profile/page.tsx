/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: Profil sayfası — kullanıcı bilgileri ve oturum yönetimi. */
/* KR-050: PIN değiştirme (6 haneli sayısal PIN). */

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
  const [showPinChange, setShowPinChange] = useState(false);
  const [currentPin, setCurrentPin] = useState("");
  const [newPin, setNewPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");
  const [pinError, setPinError] = useState<string | null>(null);
  const [pinSuccess, setPinSuccess] = useState(false);
  const [pinLoading, setPinLoading] = useState(false);

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

  const handlePinChange = async () => {
    setPinError(null);
    setPinSuccess(false);

    if (!/^\d{6}$/.test(currentPin)) {
      setPinError("Mevcut PIN 6 haneli sayı olmalıdır.");
      return;
    }
    if (!/^\d{6}$/.test(newPin)) {
      setPinError("Yeni PIN 6 haneli sayı olmalıdır.");
      return;
    }
    if (newPin !== confirmPin) {
      setPinError("Yeni PIN ve tekrarı eşleşmiyor.");
      return;
    }
    if (currentPin === newPin) {
      setPinError("Yeni PIN mevcut PIN'den farklı olmalıdır.");
      return;
    }

    setPinLoading(true);
    try {
      const token = getTokenFromCookie();
      if (!token) {
        setPinError("Oturum bulunamadı. Lütfen tekrar giriş yapın.");
        return;
      }
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/auth/phone-pin/change-pin`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ current_pin: currentPin, new_pin: newPin }),
      });

      if (res.status === 401) {
        setPinError("Mevcut PIN hatalı.");
        return;
      }
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setPinError((body as { detail?: string }).detail || "PIN değiştirilemedi.");
        return;
      }

      setPinSuccess(true);
      setCurrentPin("");
      setNewPin("");
      setConfirmPin("");
      setTimeout(() => {
        setShowPinChange(false);
        setPinSuccess(false);
      }, 2000);
    } catch {
      setPinError("Bir hata oluştu. Lütfen tekrar deneyin.");
    } finally {
      setPinLoading(false);
    }
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

      {/* PIN Değiştir */}
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        {!showPinChange ? (
          <button
            onClick={() => setShowPinChange(true)}
            className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800"
          >
            Şifre (PIN) Değiştir
          </button>
        ) : (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold">PIN Değiştir</h2>
            <p className="text-xs text-slate-500">PIN 6 haneli sayısal olmalıdır.</p>
            <input
              type="password"
              inputMode="numeric"
              maxLength={6}
              placeholder="Mevcut PIN"
              value={currentPin}
              onChange={(e) => setCurrentPin(e.target.value.replace(/\D/g, "").slice(0, 6))}
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              type="password"
              inputMode="numeric"
              maxLength={6}
              placeholder="Yeni PIN"
              value={newPin}
              onChange={(e) => setNewPin(e.target.value.replace(/\D/g, "").slice(0, 6))}
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              type="password"
              inputMode="numeric"
              maxLength={6}
              placeholder="Yeni PIN (Tekrar)"
              value={confirmPin}
              onChange={(e) => setConfirmPin(e.target.value.replace(/\D/g, "").slice(0, 6))}
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
            />
            {pinError && <p className="text-sm text-rose-600">{pinError}</p>}
            {pinSuccess && <p className="text-sm text-emerald-600">PIN başarıyla değiştirildi!</p>}
            <div className="flex gap-2">
              <button
                onClick={handlePinChange}
                disabled={pinLoading}
                className="rounded bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700 disabled:opacity-50"
              >
                {pinLoading ? "Değiştiriliyor..." : "Değiştir"}
              </button>
              <button
                onClick={() => {
                  setShowPinChange(false);
                  setPinError(null);
                  setCurrentPin("");
                  setNewPin("");
                  setConfirmPin("");
                }}
                className="rounded border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
              >
                İptal
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
