/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    serverComponentsExternalPackages: [],
  },
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  },
  async rewrites() {
    // For production builds, we'll handle API routing differently
    // This prevents the undefined issue during build time
    if (process.env.NODE_ENV === 'production') {
      // In production, let the frontend handle API calls directly
      // The NEXT_PUBLIC_API_BASE_URL will be used by the frontend code
      return [];
    }
    
    // For development, proxy API calls to the local backend
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    
    return [
      {
        source: '/api/:path*',
        destination: `${apiBaseUrl}/:path*`,
      },
    ];
  },
}

module.exports = nextConfig 