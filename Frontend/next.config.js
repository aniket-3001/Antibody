/** @type {import('next').NextConfig} */
const nextConfig = {
  // Transpile cytoscape extensions which are CommonJS
  transpilePackages: ['cytoscape-cose-bilkent'],
}

module.exports = nextConfig
