import type { NextConfig } from "next";

/**
 * Kokat bazë të sigurisë në çdo faqe (ADR 0018). `no-referrer` ka rëndësi të veçantë: faqet `/confirm` dhe
 * `/reset-password` mbajnë një token te adresa, dhe adresa nuk duhet të dalë te asnjë faqe tjetër si `Referer`
 * (faqet heqin tokenin nga adresa pas leximit, por ky është shtresa e dytë). Të njëjtat tri koka vendos edhe API-ja.
 */
const securityHeaders = [
  { key: "Referrer-Policy", value: "no-referrer" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
];

const nextConfig: NextConfig = {
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
