import React from 'react';
import clsx from 'clsx';

import styles from './styles.module.css';



const FeatureList = [
  {
    title: 'WRITE',
    src: "img/write.svg",
    description: (
      <>
        producers & consumers for Kafka topics in a simplified way
      </>
    ),
  },
  {
    title: 'PROTOTYPE',
    src: "img/prototype.svg",
    description: (
      <>
        quickly & develop high-performance Kafka-based services
      </>
    ),
  },
  {
    title: 'STREAMLINE',
    src: "img/streamline.svg",
    description: (
      <>
        your workflow & accelerate your progress
      </>
    ),
  },
];

function Feature({src, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <img className={styles.featureSvg} src={src}/>
      </div>
      <div className={clsx("text--center padding-horiz--md"), styles.textContainer}>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
      <div className={clsx('col col--12')}>
          <h2 className={styles.title}>Swim with the stream…ing services</h2>
        </div>
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
