import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'WRITE',
    Svg: require('@site/static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        producers & consumers for Kafka topics in a simplified way
      </>
    ),
  },
  {
    title: 'PROTOTYPE',
    Svg: require('@site/static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        quickly & develop high-performance Kafka-based services
      </>
    ),
  },
  {
    title: 'STREAMLINE',
    Svg: require('@site/static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        your workflow & accelerate your progress
      </>
    ),
  },
];

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

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
      <div className={clsx('col col--12')}>
          <p className={styles.title}>Swim with the stream…ing services</p>
        </div>
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
        <div className={`${styles.rowWitExtraMargin} row`}>
          <div className={clsx('col col--6')}>
            <div className="text--center padding-horiz--md">
              <p className={styles.subTitle}>Do you love boilerplate code? We neither. That’s why we made the simple way to TEST and automatically DOCUMENT the service.</p>
            </div>
          </div>
          <div className={clsx('col col--6')}>
            <div className="text--center padding-horiz--md">
              <img src="img/docusaurus-plushie-banner.jpeg" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
