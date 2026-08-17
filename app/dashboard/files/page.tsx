"use client";
import { useSearchParams } from "next/navigation";
import { TopBar } from "@/components/TopBar";
import { FileManagerBody } from "@/components/FileManagerBody";

export default function FileManagerPage() {
  const searchParams = useSearchParams();
  return (
    <div>
      <TopBar title="File Manager" description="Kelola dokumen & pangkalan data AI perusahaan." />
      <div className="p-8">
        <FileManagerBody initialPath={searchParams.get("path") || "/"} />
      </div>
    </div>
  );
}
