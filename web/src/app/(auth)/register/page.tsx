/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-050: Kayit: Telefon Numarasi + 6 haneli PIN. E-posta ve TCKN toplanmaz. */
/* KR-013: Uyelik: il, ilce, ad, soyad ve telefon numarasi alinir. */
/* KR-081: Register payload contract-first uretilir. */

"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { getApiBaseUrl, decodeJwtPayload } from "@/lib/api";
import { setAuthToken } from "@/lib/authStorage";
import { AUTH_TOKEN_TTL_MS, COOKIE_TOKEN_KEY, COOKIE_ROLE_KEY } from "@/lib/constants";
import { ROLE_TO_GROUP, type AuthRole } from "@/hooks/useAuth";

export default function RegisterPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [pin, setPin] = useState("");
  const [pinConfirm, setPinConfirm] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [province, setProvince] = useState("");
  const [district, setDistrict] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!/^\d{10,15}$/.test(phone.trim())) {
      return setError("Geçerli bir telefon numarası giriniz.");
    }
    if (!/^\d{6}$/.test(pin)) {
      return setError("PIN 6 haneli sayısal olmalıdır.");
    }
    if (pin !== pinConfirm) {
      return setError("PIN tekrarı eşleşmiyor.");
    }
    if (!firstName.trim() || !lastName.trim()) {
      return setError("Ad ve soyad zorunludur.");
    }
    if (!province.trim() || !district.trim()) {
      return setError("İl ve ilçe zorunludur.");
    }

    setIsSubmitting(true);

    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/auth/phone-pin/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone: phone.trim(),
          pin,
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          province: province.trim(),
          district: district.trim(),
        }),
      });

      if (response.status === 409) {
        setError("Bu telefon numarası zaten kayıtlı.");
        return;
      }
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        setError((body as { detail?: string }).detail || "Kayıt başarısız");
        return;
      }

      const data = (await response.json()) as { access_token: string; subject: string };

      // Set auth state so user is immediately logged in after registration
      setAuthToken(data.access_token, AUTH_TOKEN_TTL_MS);
      const maxAgeSec = Math.floor(AUTH_TOKEN_TTL_MS / 1000);
      document.cookie = `${COOKIE_TOKEN_KEY}=${encodeURIComponent(data.access_token)};path=/;max-age=${maxAgeSec};Secure;SameSite=Strict`;

      const claims = decodeJwtPayload(data.access_token);
      const roles = (claims.roles as string[] | undefined) ?? [];
      const primaryRole = (roles[0] ?? "FARMER_SINGLE") as AuthRole;
      const roleGroup = ROLE_TO_GROUP[primaryRole] ?? "farmer";
      document.cookie = `${COOKIE_ROLE_KEY}=${roleGroup};path=/;max-age=${maxAgeSec};Secure;SameSite=Strict`;

      router.replace("/fields");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Kayıt başarısız");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="mx-auto w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="mb-4 text-xl font-semibold">Üye Ol</h1>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label htmlFor="reg-phone" className="mb-1 block text-sm font-medium">Telefon Numarası</label>
          <input id="reg-phone" name="phone" type="tel" autoComplete="tel" required value={phone} onChange={(e) => setPhone(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="reg-first-name" className="mb-1 block text-sm font-medium">Ad</label>
            <input id="reg-first-name" name="firstName" type="text" autoComplete="given-name" required value={firstName} onChange={(e) => setFirstName(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2" />
          </div>
          <div>
            <label htmlFor="reg-last-name" className="mb-1 block text-sm font-medium">Soyad</label>
            <input id="reg-last-name" name="lastName" type="text" autoComplete="family-name" required value={lastName} onChange={(e) => setLastName(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="reg-province" className="mb-1 block text-sm font-medium">İl</label>
            <input id="reg-province" name="province" type="text" required value={province} onChange={(e) => setProvince(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2" />
          </div>
          <div>
            <label htmlFor="reg-district" className="mb-1 block text-sm font-medium">İlçe</label>
            <input id="reg-district" name="district" type="text" required value={district} onChange={(e) => setDistrict(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2" />
          </div>
        </div>
        <div>
          <label htmlFor="reg-pin" className="mb-1 block text-sm font-medium">6 Haneli PIN</label>
          <input id="reg-pin" name="pin" type="password" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} minLength={6} autoComplete="new-password" required value={pin} onChange={(e) => setPin(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2" />
        </div>
        <div>
          <label htmlFor="reg-pin-confirm" className="mb-1 block text-sm font-medium">PIN Tekrarı</label>
          <input id="reg-pin-confirm" name="pinConfirm" type="password" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} minLength={6} autoComplete="new-password" required value={pinConfirm} onChange={(e) => setPinConfirm(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2" />
        </div>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <button type="submit" disabled={isSubmitting} className="w-full rounded bg-slate-900 px-3 py-2 text-white">
          {isSubmitting ? "Kaydediliyor..." : "Üye Ol"}
        </button>
      </form>
      <p className="mt-3 text-center text-sm text-slate-500">
        Hesabınız var mı? <a href="/login" className="text-slate-900 underline">Giriş yapın</a>
      </p>
    </section>
  );
}
