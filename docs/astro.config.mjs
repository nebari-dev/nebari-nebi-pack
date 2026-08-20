import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { nebari } from '@nebari/starlight';
import rehypeMermaid from 'rehype-mermaid';
import remarkBaseLinks from './src/plugins/remark-base-links';

// Deploy conventions, set by .github/workflows/docs.yml (PACK_SLUG: nebi-pack):
//
//   main    SITE=https://packs.nebari.dev              BASE=/nebi-pack/
//   preview SITE=https://<branch>.nebi-pack.pages.dev  BASE=/
//
// The `site` default mirrors the production origin so a plain `npm run build`
// still emits correct canonical URLs and a sitemap. `base` stays `/` by default
// so the dev server and local previews serve from the root.
const SITE = process.env.SITE || 'https://packs.nebari.dev';
const BASE = process.env.BASE || '/';

export default defineConfig({
  base: BASE,
  site: SITE,
  integrations: [
    starlight({
      title: 'Nebari Nebi Pack',
      description: 'Environment management for Nebari.',
      // Shared Nebari identity (brand colors, fonts, logo, favicon, footer, and
      // GitHub social link) comes from the @nebari/starlight theme plugin. On the
      // portal the header logo returns users to the pack catalog.
      plugins: [nebari({ logoHref: 'https://packs.nebari.dev/' })],
      sidebar: [
        {
          label: 'Getting Started',
          items: [
            { label: 'Introduction', link: '/' },
            { label: 'Getting started', link: '/getting-started/' },
            { label: 'Branding', link: '/branding/' },
            { label: 'Local development', link: '/local-development/' },
          ],
        },
        {
          label: 'Reference',
          items: [
            { label: 'Helm values', link: '/helm-values/' },
            { label: 'Architecture & auth', link: '/architecture/' },
          ],
        },
      ],
    }),
  ],
  markdown: {
    syntaxHighlight: { type: 'shiki', excludeLangs: ['mermaid'] },
    remarkPlugins: [[remarkBaseLinks, { base: BASE }]],
    rehypePlugins: [[rehypeMermaid, { strategy: 'inline-svg' }]],
  },
});
