// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require('prism-react-renderer/themes/github');
const darkCodeTheme = require('prism-react-renderer/themes/dracula');

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'FastKafka',
  tagline: 'Effortless Kafka integration for your web services',
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
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: 'https://opengraph.githubassets.com/1671805243.560327/airtai/fastkafka',
      navbar: {
        title: '',
        logo: {
          alt: 'FastKafka Logo',
          src: 'img/AIRT_icon_blue.svg',
        },
        items: [
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
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Get Started',
                to: '/docs/',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'Discord',
                href: 'https://discord.gg/CJWmYpyFbc',
              },
              {
                label: 'GitHub',
                href: 'https://github.com/airtai/fastkafka',
              },
              {
                label: 'Twitter',
                href: 'https://twitter.com/airt_AI',
              },
              {
                label: 'Facebook',
                href: 'https://www.facebook.com/airt.ai.api/',
              },
              {
                label: 'LinkedIn',
                href: 'https://www.linkedin.com/company/airt-ai/',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'About Us',
                to: 'https://airt.ai/about-us',
              },
//               {
//                 label: 'Contact',
//                 to: 'https://airt.ai/contact',
//               },
              {
                label: 'Company information',
                to: 'https://airt.ai/company-information',
              },
            ],
          },
        ],
        copyright: `© 2023 airt`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
    }),
};

module.exports = config;
