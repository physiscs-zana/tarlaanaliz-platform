/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-081: login payload contract-first üretilir. */
/* KR-071: corr/request metadata login isteğiyle taşınır. */
/* KR-033: Auth artefact lifecycle — useAuth kanonik kaynak; cookie + localStorage birlikte yazılır. */

"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth, ROLE_TO_GROUP } from "@/hooks/useAuth";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [phone, setPhone] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const data = await login({ phone: phone.trim(), pin: pin.trim() });
      // useAuth.login() cookie + localStorage yazımını halleder.
      const roleHome: Record<string, string> = {
        admin: "/analytics",
        expert: "/queue",
        farmer: "/benim-sayfam",
        pilot: "/pilot/missions",
      };
      const group = ROLE_TO_GROUP[data.user.role] ?? "farmer";
      router.replace(roleHome[group] ?? "/");
    } catch (submitError) {
      // KR-050 + BÖLÜM 4: Rate limit (HTTP 429) ve lockout durumu için kullanıcı bildirimi
      const msg = submitError instanceof Error ? submitError.message : "";
      if (msg.includes("429") || msg.toLowerCase().includes("rate limit")) {
        setError("Çok fazla deneme yaptınız. Lütfen birkaç dakika bekleyip tekrar deneyin.");
      } else if (msg.toLowerCase().includes("locked") || msg.toLowerCase().includes("lockout")) {
        setError("Hesabınız geçici olarak kilitlendi. 30 dakika sonra tekrar deneyin.");
      } else {
        setError("Telefon numarası veya PIN hatalı. Lütfen kontrol edip tekrar deneyin.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="mx-auto w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="mb-4 text-xl font-semibold">Giriş Yap</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="phone" className="mb-1 block text-sm font-medium">
            Telefon
          </label>
          <input
            id="phone"
            name="phone"
            type="tel"
            autoComplete="tel"
            required
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2"
          />
        </div>
        <div>
          <label htmlFor="pin" className="mb-1 block text-sm font-medium">
            PIN
          </label>
          <input
            id="pin"
            name="pin"
            type="password"
            inputMode="numeric"
            pattern="[0-9]{6}"
            maxLength={6}
            minLength={6}
            autoComplete="current-password"
            required
            value={pin}
            onChange={(event) => setPin(event.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2"
          />
        </div>
        {error ? (
          <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm font-medium text-red-700">
            {error}
          </div>
        ) : null}
        <button type="submit" disabled={isSubmitting} className="w-full rounded bg-slate-900 px-3 py-2 text-white">
          {isSubmitting ? "Gönderiliyor..." : "Giriş"}
        </button>
      </form>
      <p className="mt-3 text-center text-sm text-slate-500">
        Hesabınız yok mu? <a href="/register" className="text-slate-900 underline">Üye olun</a>
      </p>
    </section>
  );
}
