/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        // Semua panggil ke /api/ akan diteruskan ke server Python Anda yang aktif
        source: '/api/:path*',
        destination: 'https://vercel.app*', // Ganti dengan URL dari Langkah 1
      },
    ];
  },
};

module.exports = nextConfig;
