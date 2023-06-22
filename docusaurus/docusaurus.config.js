// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require('prism-react-renderer/themes/github');
const darkCodeTheme = require('prism-react-renderer/themes/dracula');

module.exports = async function configCreatorAsync() {
  /** @type {import('@docusaurus/types').Config} */
  const config = {
    title: 'FastKafka',
    tagline: 'Effortless Kafka integration for web services',
    customFields: {
      description:
        'Powerful and easy-to-use open-source framework for building asynchronous web services that interact with Kafka.',
    },
    favicon: 'img/AIRT_icon_blue.svg',

    // Set the production url of your site here
    url: 'https://fastkafka.airt.ai/',
    // Set the /<baseUrl>/ pathname under which your site is served
    // For GitHub pages deployment, it is often '/<projectName>/'
    baseUrl: '/',

    // GitHub pages deployment config.
    // If you aren't using GitHub pages, you don't need these.
    organizationName: 'airt', // Usually your GitHub org/user name.
    projectName: 'fastkafka', // Usually your repo name.
    trailingSlash: false,
    onBrokenLinks: 'warn',
    onBrokenMarkdownLinks: 'warn',

    // Even if you don't use internalization, you can use this field to set useful
    // metadata like html lang. For example, if your site is Chinese, you may want
    // to replace "en" with "zh-Hans".
    i18n: {
      defaultLocale: 'en',
      locales: ['en'],
    },

    presets: [
      [
        'classic',
        /** @type {import('@docusaurus/preset-classic').Options} */
        ({
          docs: {
            sidebarPath: require.resolve('./sidebars.js'),
            // Please change this to your repo.
            // Remove this to remove the "edit this page" links.
  //           editUrl:
  //             'https://github.com/facebook/docusaurus/tree/main/packages/create-docusaurus/templates/shared/',
            exclude: [
              // '**/_*.{js,jsx,ts,tsx,md,mdx}',
              // '**/_*/**',
              '**/*.test.{js,jsx,ts,tsx}',
              '**/__tests__/**',
            ],
            versions: {
              current: {
                label: `dev 🚧`,
              },
            },
          },
          blog: {
            showReadingTime: true,
            // Please change this to your repo.
            // Remove this to remove the "edit this page" links.
  //           editUrl:
  //             'https://github.com/facebook/docusaurus/tree/main/packages/create-docusaurus/templates/shared/',
          },
          theme: {
            customCss: require.resolve('./src/css/custom.css'),
          },
          gtag: {
            trackingID: 'G-WLMWPELHMB',
          },
        }),
      ],
    ],

    themeConfig:
      /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
      ({
        algolia: {
          appId: 'EHYNSIUGMY',
          // Public API key: it is safe to commit it
          // nosemgrep
          apiKey: '2680cd13947844a00a5a657b959e6211',
          indexName: 'fastkafka-airt',
        },
        // Replace with your project's social card
        image: 'https://opengraph.githubassets.com/1671805243.560327/airtai/fastkafka',
        // colorMode: {
        //   disableSwitch: true,
        // },
        navbar: {
          title: 'airt',
          logo: {
            alt: 'airt logo',
            src: 'img/AIRT_icon_blue.svg',
            href: 'https://airt.ai',
            target: '_blank'
          },
          items: [
            {to: '/', html: '<div><img src="/img/home-icon.svg"><p>FastKafka</p></div>', position: 'right', className: 'fastkafka-home'},
            {
              type: 'docsVersionDropdown',
              position: 'right',
              dropdownActiveClassDisabled: true,
              // dropdownItemsAfter: [{to: '/versions', label: 'All versions'}],
            },
            {
              type: 'docSidebar',
              sidebarId: 'tutorialSidebar',
              position: 'right',
              label: 'Docs',
            },
  //           {to: '/blog', label: 'Blog', position: 'left'},
            {
              type: 'html',
              position: 'right',
              className: 'github-stars',
              value: '<iframe src="https://ghbtns.com/github-btn.html?user=airtai&repo=fastkafka&type=star&count=true&size=large" frameborder="0" scrolling="0" width="170" height="30" title="GitHub"></iframe>',
            },
            {
              href: 'https://discord.gg/CJWmYpyFbc',
              position: 'right',
              className: "header-discord-link",
              "aria-label": "Discord Link",
            },
            {to: '/', html: '<div><img src="/img/home-icon.svg"></div>', position: 'right', className: 'fastkafka-home-mobile'},
          ],
        },
        footer: {
          style: 'dark',
          links: [
            {
              title: 'COMMUNITY',
              items: [
                {
                  html: `
                      <a class="footer-discord-link" href="https://discord.gg/CJWmYpyFbc" target="_blank" rel="noreferrer noopener" aria-label="Discord link"></a>
                    `,
                },
                {
                  html: `
                      <a class="footer-github-link" href="https://github.com/airtai" target="_blank" rel="noreferrer noopener" aria-label="Github link"></a>
                    `,
                },
                {
                  html: `
                      <a class="footer-twitter-link" href="https://twitter.com/airt_AI" target="_blank" rel="noreferrer noopener" aria-label="Twitter link"></a>
                    `,
                },
                {
                  html: `
                      <a class="footer-facebook-link" href="https://www.facebook.com/airt.ai.api/" target="_blank" rel="noreferrer noopener" aria-label="Facebook link"></a>
                    `,
                },
                {
                  html: `
                      <a class="footer-linkedin-link" href="https://www.linkedin.com/company/airt-ai/" target="_blank" rel="noreferrer noopener" aria-label="LinkedIn link"></a>
                    `,
                },
              ],
            },
            {
              title: 'EXPLORE DOCS',
              items: [
                {
                  label: 'Get Started',
                  to: '/docs',
                },
              ],
            },
            {
              title: 'EXPLORE MORE',
              items: [
                {
                  label: 'News',
                  to: 'https://airt.ai/news',
                },
                {
                  label: 'About Us',
                  to: 'https://airt.ai/about-us',
                },
                {
                  label: 'Company information',
                  to: 'https://airt.ai/company-information',
                },
                // {
                //   label: 'Contact',
                //   to: 'contact',
                // },
                
              ],
            },
          ],
          copyright: `© 2023 airt. All rights reserved.`,
        },
        // prism: {
        //   theme: lightCodeTheme,
        //   darkTheme: darkCodeTheme,
        // },
        prism: {
          theme: ( await import('./src/utils/prismLight.mjs')).default,
          darkTheme: ( await import('./src/utils/prismDark.mjs')).default,
        },
      }),
  };
  return config
};
