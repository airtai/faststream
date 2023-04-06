import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';

import styles from './styles.module.css';

export default function HomepageWhatYouGet() {
  return (
    <section className={styles.features}>
      <div className="container">
      <div className={clsx('col col--12')}>
          <p className={styles.title}>You get what you expect</p>
        </div>
        <div className={`row ${styles.childrenWithExtraPadding}`}>
          <div className={clsx('col col--6 text--center padding-horiz--md')}>
            <p>Function decorators with type hints specifying Pydantic classes for JSON encoding/decoding, automatic message routing and documentation generation.</p>
          </div>
          <div className={clsx('col col--6 text--center padding-horiz--md')}>
            <p>Built on top of <a className={styles.link} href="https://docs.pydantic.dev/" target="_blank">Pydantic</a>, <a className={styles.link} href="https://github.com/aio-libs/aiokafka/" target="_blank">AIOKafka</a> and <a className={styles.link} href="https://www.asyncapi.com/" target="_blank">AsyncAPI</a>, FastKafka simplifies the process of writing producers and consumers for Kafka topics, handling all the parsing, networking, task scheduling and data generation automatically. </p>
          </div>
        </div>
        {/* <div className={`${styles.rowWitExtraMargin} row`}>
          <div className={clsx('col col--6', styles.wrapper)}>
            <div className={`text--center padding-horiz--md ${styles.verticalAndHorizontalCenter}`}>
            <Link
              className="btn-github-link button button--secondary button--lg"
              to="https://github.com/airtai/fastkafka">
                Check it out
            </Link>
            </div>
          </div>
          <div className={clsx('col col--6')}>
            <div className="text--center padding-horiz--md">
              <img src="img/docusaurus-plushie-banner.jpeg" />
            </div>
          </div>
        </div> */}
      </div>
    </section>
  );
}
