import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import HomepageWhatYouGet from '@site/src/components/HomepageWhatYouGet';
import HomepageCommunity from '@site/src/components/HomepageCommunity';
import HomepageFAQ from '@site/src/components/HomepageFAQ';
import HomepageFastkafkaChat from '@site/src/components/HomepageFastkafkaChat';
import RobotFooterIcon from '@site/src/components/RobotFooterIcon';

import styles from './index.module.css';

function HomepageHeader() {
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <img className={styles.heroRobot} src="img/robot-hero.svg" />
        <p className={styles.description}>Open-source framework for building asynchronous web </p>
        <p className={styles.description}>services that interact with Kafka</p>
        <p className={styles.descriptionMobile}>Open-source framework for building asynchronous web services that interact with Kafka</p>
        <div className={styles.buttons}>
          <Link
            className={clsx("button button--lg", styles.heroButton)}
            to="/docs">
              Get Started
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={siteConfig.tagline}
      description={siteConfig.customFields.description}>
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        <HomepageFastkafkaChat />
        <HomepageWhatYouGet />
        <HomepageCommunity />
        <HomepageFAQ />
        <RobotFooterIcon />
      </main>
    </Layout>
  );
}
