export function createSiteMeta({ base = '/' } = {}) {
  return {
    base,
    title: 'trace',
    description: 'Documentation',
    themeConfig: {
      nav: [
        { text: 'Home', link: base || '/' },
      ],
    },
  }
}
