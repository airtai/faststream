import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

const FeatureList = [
  {
    containerOne: {
      source: {
        name: "r/Python",
        icon: "/img/reddit-logo.png",
        link: "https://www.google.com",
      },
      user: {
        profilePic: "",
        userName: "@username",
        fullName: "Full Name",
      },
      description: (
        <>
          I really like the idea of this, as the biggest gripe I have with most pub/sub solutions is all of the tedious boiler plate code needed to correctly subscribe and publish and manage message leases etc. While you often just want to grab a message, do some processing and put it on a different queue.
        </>
      ),
    },
    containerTwo: {
      source: {
        name: "r/FastAPI",
        icon: "/img/reddit-logo.png",
        link: "https://www.google.com",
      },
      user: {
        profilePic: "",
        userName: "@username",
        fullName: "Full Name",
      },
      description: (
        <>
          Thank you for your efforts. I see me pitching this library to my team in the near future!
        </>
      ),
    },
  },
  {
    containerOne: {
      source: {
        name: "r/Python",
        icon: "/img/reddit-logo.png",
        link: "https://www.google.com",
      },
      user: {
        profilePic: "",
        userName: "@username",
        fullName: "Full Name",
      },
      description: (
        <>
          Very cool indeed. Currently at work we're using RabbitMQ for messaging so this doesn't apply to us (for now), but this type and style of implementation is exactly what I would expect when searching for libs like this. Great job!
        </>
      ),
    },
    containerTwo: {
      source: {
        name: "HackerNews",
        icon: "/img/reddit-logo.png",
        link: "https://www.google.com",
      },
      user: {
        profilePic: "",
        userName: "@username",
        fullName: "Full Name",
      },
      description: (
        <>
          It looks incredible and I truly hope your project takes off for my sake since I have to work with Kafka from time to time!
        </>
      ),
    },
  },
  {
    containerOne: {
      source: {
        name: "r/FastAPI",
        icon: "/img/reddit-logo.png",
        link: "https://www.google.com",
      },
      user: {
        profilePic: "",
        userName: "@username",
        fullName: "Full Name",
      },
      description: (
        <>
          Wow! This is really great, thank you for your efforts guys. This is what I really need for one of my future projects.
        </>
      ),
    },
    containerTwo: {
      source: {
        name: "r/programming",
        icon: "/img/reddit-logo.png",
        link: "https://www.google.com",
      },
      user: {
        profilePic: "",
        userName: "@username",
        fullName: "Full Name",
      },
      description: (
        <>
          Wow, the code in the package is auto-generated from Jupyter-Notebooks
        </>
      ),
    },
  },
];

function Feature({containerOne, containerTwo}) {
  return (
      <div className={`${clsx('col col--4')} ${styles.testimonialWrapper}`}>
        <a href={containerOne.source.link} target="_blank" className={styles.testimonialAnchor}>
          <div className={styles.testimonialContainer}>
            <div className={styles.testimonialHeader}>
              <div className={styles.testimonialUserInfo}>
                {/* <img src={containerOne.user.profilePic} className={styles.testimonialProfilePic} /> */}
                <div> 
                  <h6>{containerOne.user.fullName}</h6>
                  <p>{containerOne.user.userName}</p>
                </div>
              </div>
              <div> 
                <img className={styles.testimonialSourceIcon} src={containerOne.source.icon} />  
              </div>
            </div>
            <div className="text--center padding-horiz--md">
              <p className={styles.testimonialDescription}>{containerOne.description}</p>
              <p className={styles.testimonialDescription}>{containerOne.source.name}</p>
            </div>
          </div>
        </a>
        <a href={containerTwo.source.link} target="_blank" className={styles.testimonialAnchor}>
          <div className={styles.testimonialContainer}>
            <div className={styles.testimonialHeader}>
              <div className={styles.testimonialUserInfo}>
                {/* <img src={containerTwo.user.profilePic} className={styles.testimonialProfilePic} /> */}
                <div> 
                  <h6>{containerTwo.user.fullName}</h6>
                  <p>{containerTwo.user.userName}</p>
                </div>
              </div>
              <div> 
                <img className={styles.testimonialSourceIcon} src={containerTwo.source.icon} />  
              </div>
            </div>
            <div className="text--center padding-horiz--md">
              <p className={styles.testimonialDescription}>{containerTwo.description}</p>
              <p className={styles.testimonialDescription}>{containerTwo.source.name}</p>
            </div>
          </div>
        </a>
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
