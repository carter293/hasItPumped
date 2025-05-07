import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "coin-images.coingecko.com",
        port: "",          
        pathname: "/**",   
      },
      {
        protocol: "https",
        hostname: "assets.geckoterminal.com",
        port: "",          
        pathname: "/**",   
      },
    ],
    
    
  },
};

export default nextConfig;
