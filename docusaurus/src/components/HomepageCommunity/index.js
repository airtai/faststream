import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

const FeatureList = [
  {
    source: "r/FastAPI",
    description: (
      <>
        Wow! This is really great, thank you for your efforts guys. This is what I really need for one of my future projects.
      </>
    ),
  },
  {
    source: "r/Python",
    description: (
      <>
        I really like the idea of this, as the biggest gripe I have with most pub/sub solutions is all of the tedious boiler plate code needed to correctly subscribe and publish and manage message leases etc. While you often just want to grab a message, do some processing and put it on a different queue.
      </>
    ),
  },
  {
    source: "r/Python",
    description: (
      <>
        Very cool indeed. Currently at work we're using RabbitMQ for messaging so this doesn't apply to us (for now), but this type and style of implementation is exactly what I would expect when searching for libs like this. Great job!
      </>
    ),
  },
  {
    source: "HackerNews",
    description: (
      <>
        It looks incredible and I truly hope your project takes off for my sake since I have to work with Kafka from time to time!
      </>
    ),
  },
  {
    source: "r/FastAPI",
    description: (
      <>
        Thank you for your efforts. I see me pitching this library to my team in the near future!
      </>
    ),
  },
  {
    source: "r/programming",
    description: (
      <>
        Wow, the code in the package is auto-generated from Jupyter-Notebooks
      </>
    ),
  },
];

function Feature({description, source}) {
  return (
    <div className={clsx('col col--4', styles.withExtraMargin)}>
      <div className="text--center padding-horiz--md">
        <p className={styles.testimonialDescription}>{description}</p>
        <p className={styles.testimonialDescription}>{source}</p>
      </div>
    </div>
  );
}

export default function HomepageCommunity() {
  return (
    <section className={`${styles.features}  hero hero--primary`}>
      <div className="container">
      <div className={clsx('col col--12')}>
          <h2 className={styles.title}>The community has spoken!</h2>
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
