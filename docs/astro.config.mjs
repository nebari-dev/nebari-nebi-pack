import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { nebari } from '@nebari/starlight';
import rehypeMermaid from 'rehype-mermaid';
import remarkBaseLinks from './src/plugins/remark-base-links';

export default defineConfig({
  base: process.env.BASE || '/',
  site: process.env.SITE || 'https://packs.nebari.dev',
  integrations: [
    starlight({
      title: 'Nebari Nebi Pack',
      description: 'Environment management for Nebari.',
      plugins: [nebari({ logoHref: 'https://packs.nebari.dev/' })],
      sidebar: [
        { label: 'Introduction', slug: 'index' },
      ],
    }),
  ],
  markdown: {
    syntaxHighlight: { type: 'shiki', excludeLangs: ['mermaid'] },
    remarkPlugins: [[remarkBaseLinks, { base: process.env.BASE || '/' }]],
    rehypePlugins: [[rehypeMermaid, { strategy: 'inline-svg' }]],
  },
});
