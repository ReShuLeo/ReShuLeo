import type { NextConfig } from 'next';
const config: NextConfig = {
  poweredByHeader: false,
  allowedDevOrigins: ['terminal.local'],
  async headers() { return [{source: '/(.*)', headers: [
    {key:'X-Content-Type-Options',value:'nosniff'},
    {key:'Referrer-Policy',value:'strict-origin-when-cross-origin'},
    {key:'Permissions-Policy',value:'geolocation=(self), camera=(), microphone=()'},
    // Same-origin frames are allowed only for the local responsive QA harness.
    {key:'X-Frame-Options',value:process.env.NODE_ENV==='development'?'SAMEORIGIN':'DENY'}
  ]}]; }
};
export default config;
