/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        // Pengguna memanggil '/api/...', Next.js meneruskannya ke folder Python secara internal
        source: '/api/:path*',
        destination: '/python-api/index.py',
      },
    ];
  },
};

module.exports = nextConfig;
