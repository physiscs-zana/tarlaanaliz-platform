/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-081: login payload contract-first üretilir. */
/* KR-071: corr/request metadata login isteğiyle taşınır. */

"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { apiRequest } from "@/lib/apiClient";
import type { LoginResponse } from "@/hooks/useAuth";

interface LoginPayload {
  readonly phone: string;
  readonly pin: string;
}

export default function LoginPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const payload: LoginPayload = { phone: phone.trim(), pin: pin.trim() };

    try {
      await apiRequest<LoginResponse>("/api/auth/login", {
        method: "POST",
        body: payload,
      });
      router.replace("/");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Giriş başarısız");
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
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <button type="submit" disabled={isSubmitting} className="w-full rounded bg-slate-900 px-3 py-2 text-white">
          {isSubmitting ? "Gönderiliyor..." : "Giriş"}
        </button>
      </form>
    </section>
  );
}
