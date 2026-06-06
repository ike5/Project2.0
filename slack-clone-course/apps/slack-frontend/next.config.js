/** @type {import('next').NextConfig} */
const nextConfig = {
  // 'standalone' produces a minimal self-contained server for the Docker image (Module 12).
  output: "standalone",
  reactStrictMode: true,
};

module.exports = nextConfig;
