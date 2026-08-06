/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        // Meneruskan permintaan /api ke fungsi Python di dalam folder yang sama
        source: '/api/:path*',
        destination: '/api/index.py',
      },
    ];
  },
};

module.exports = nextConfig;
