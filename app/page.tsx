"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    router.push("/auth");
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center bg-navy-50 text-sm font-medium text-navy-500">
      Mengalihkan ke halaman masuk...
    </div>
  );
}
