import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// PENTING: Nama fungsinya wajib menggunakan kata 'proxy' bukan 'middleware'
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Jika ada pengguna yang membuka rute akar utama '/'
  if (pathname === '/') {
    return NextResponse.redirect(new URL('/auth', request.url));
  }

  // Jika rute lain, izinkan akses berlanjut tanpa hambatan
  return NextResponse.next();
}

// Konfigurasi matcher untuk membatasi jalannya fungsi proxy
export const config = {
  matcher: ['/'],
};
