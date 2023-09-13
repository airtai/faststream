import React from 'react';
import clsx from 'clsx';
import Iframe from 'react-iframe'
import BrowserWindow from '../BrowserWindow';

import styles from './styles.module.css';



// const FeatureList = [
//   {
//     title: 'WRITE',
//     Svg: require('@site/static/img/programming-monitor-svgrepo-com.svg').default,
//     description: (
//       <>
//         producers & consumers for Kafka topics in a simplified way
//       </>
//     ),
//   },
//   {
//     title: 'PROTOTYPE',
//     Svg: require('@site/static/img/rocket-svgrepo-com.svg').default,
//     description: (
//       <>
//         quickly & develop high-performance Kafka-based services
//       </>
//     ),
//   },
//   {
//     title: 'STREAMLINE',
//     Svg: require('@site/static/img/hierarchy-order-svgrepo-com.svg').default,
//     description: (
//       <>
//         your workflow & accelerate your progress
//       </>
//     ),
//   },
// ];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFastkafkaChat() {
  return (
    <section className={`${styles.features} hero hero--primary`}>
      <div className="container">
      <div className={clsx('col col--12')}>
          <h2 className={styles.title}>Check out our code-generation feature!</h2>
          <p className={styles.fastkafkaDescription}>Let us know what you need solved and we’ll generate the FastKafka code for you!</p>
        </div>
        <div className={`row`}>
          <div className={clsx('col col--12')}>
            <div className="text--center padding-horiz--md">
              <BrowserWindow>
                <Iframe url="https://fastkafka-chat.azurewebsites.net/" className={styles.fastkafkaChatIframe} />
              </BrowserWindow>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
