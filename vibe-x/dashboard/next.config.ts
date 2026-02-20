import type { NextConfig } from "next";

const API_BACKEND = process.env.API_BACKEND_URL || 'http://127.0.0.1:8000';

const nextConfig: NextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${API_BACKEND}/api/:path*`,
      },
      {
        source: '/ws',
        destination: `${API_BACKEND}/ws`,
      },
    ];
  },
};

export default nextConfig;
