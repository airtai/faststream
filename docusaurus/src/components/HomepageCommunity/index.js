import React, { useState, useEffect } from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

function Testimonial({ testimonialLimitToShow, allTestimonials }) {
  return (
    <div className={`${clsx('col col--4')} ${styles.testimonialWrapper}`}>
      {Object.entries(allTestimonials).map(([key, value]) => {
        if (key.split("_")[1] <= testimonialLimitToShow) {
          return (
            <a
              key={key}
              href={value.source.link}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.testimonialAnchor}
            >
              <div className={styles.testimonialContainer}>
                <div className={styles.testimonialHeader}>
                  <div className={styles.testimonialUserInfo}>
                    <img src={value.user.profilePic} className={styles.testimonialProfilePic} />
                    <div>
                      <h6>{value.user.fullName}</h6>
                      <p>{value.user.userName}</p>
                    </div>
                  </div>
                  <div>
                    <img className={styles.testimonialSourceIcon} src={value.source.icon} alt="" />
                  </div>
                </div>
                <div className="text--center padding-horiz--md">
                  <p className={styles.testimonialDescription}>{value.description}</p>
                </div>
              </div>
            </a>
          );
        }
        return null;
      })}
    </div>
  );
}


const redditUserProfiles = ["deadwisdom", "benbenbang", "Berouald", "baggiponte", "No-Application5593", "code_mc", "teajunky", "SteamingBeer", "BestBottle4517"];
const maxTestimonialSectionToShow = "4"

export default function HomepageCommunity() {
  const [testimonialLimitToShow, setTestimonialLimitToShow] = useState("2");
  const [profiles, setProfiles] = useState(redditUserProfiles.reduce(
    (result, username) => ({
      ...result,
      [username]: {
        icon_img: "https://www.redditstatic.com/avatars/defaults/v2/avatar_default_1.png",
        subreddit: {
          display_name_prefixed: `u/${username}`,
        },
      },
    }),
    {}
  ));
  const testimonials = [
    {
      container_1: {
        source: {
          icon: "img/reddit-logo.png",
          link: "https://www.reddit.com/r/Python/comments/13i0eaz/comment/jk90bwz/?utm_source=share&utm_medium=web2x&context=3",
        },
        user: {
          profilePic: profiles["deadwisdom"]["icon_img"],
          userName: profiles["deadwisdom"]["subreddit"]["display_name_prefixed"],
          fullName: "deadwisdom",
        },
        description: (
          <>
            Well well well, if it isn't the library I was already making but better. Very nice.

            What is your long-term vision for supporting this as a company?

            And are you using this now to support real customers or are you expecting this might help you establish a niche?
          </>
        ),
      },
      container_2: {
        source: {
          icon: "img/twitter-logo.svg",
          link: "https://twitter.com/emaxerrno/status/1635005087721611264?s=20",
        },
        user: {
          profilePic: "img/a-alphabet-round-icon.png",
          userName: "Alexander Gallego",
          fullName: "Alexander Gallego",
        },
        description: (
          <>
            this is cool. let me know if you want to share it w/ the @redpandadata community.
          </>
        ),
      },
      container_3: {
        source: {
          icon: "img/reddit-logo.png",
          link: "https://www.reddit.com/r/Python/comments/11paz9u/comment/jbxbbxp/?utm_source=share&utm_medium=web2x&context=3",
        },
        user: {
          profilePic: profiles["BestBottle4517"]["icon_img"].replace(/&amp;/g, '&'),
          userName: profiles["BestBottle4517"]["subreddit"]["display_name_prefixed"],
          fullName: "BestBottle4517",
        },
        description: (
          <>
            Very cool indeed. Currently at work we're using RabbitMQ for messaging so this doesn't apply to us (for now), but this type and style of implementation is exactly what I would expect when searching for libs like this. Great job!
          </>
        ),
      },
      container_4: {
        source: {
          icon: "img/reddit-logo.png",
          link: "https://www.reddit.com/r/programming/comments/11sjtgm/comment/jceqgml/?utm_source=share&utm_medium=web2x&context=3",
        },
        user: {
          profilePic: profiles["teajunky"]["icon_img"],
          userName: profiles["teajunky"]["subreddit"]["display_name_prefixed"],
          fullName: "teajunky",
        },
        description: (
          <>
            Wow, the code in the package is auto-generated from Jupyter-Notebooks
          </>
        ),
      },
      
    },
    {
      container_1: {
        source: {
          icon: "img/reddit-logo.png",
          link: "https://www.reddit.com/r/FastAPI/comments/124v5di/comment/jfhg2t2/?utm_source=share&utm_medium=web2x&context=3",
        },
        user: {
          profilePic: profiles["benbenbang"]["icon_img"].replace(/&amp;/g, '&'),
          userName: profiles["benbenbang"]["subreddit"]["display_name_prefixed"],
          fullName: "benbenbang",
        },
        description: (
          <>
            Nice 👍🏻 I’ve promoted this project in the team! Also, would like to contribute if there’s some kind of roadmap
          </>
        ),
      },
      container_2: {
        source: {
          icon: "img/reddit-logo.png",
          link: "https://www.reddit.com/r/Python/comments/11paz9u/comment/jbxf1v8/?utm_source=share&utm_medium=web2x&context=3",
        },
        user: {
          profilePic: profiles["code_mc"]["icon_img"],
          userName: profiles["code_mc"]["subreddit"]["display_name_prefixed"],
          fullName: "code_mc",
        },
        description: (
          <>
            I really like the idea of this, as the biggest gripe I have with most pub/sub solutions is all of the tedious boiler plate code needed to correctly subscribe and publish and manage message leases etc. While you often just want to grab a message, do some processing and put it on a different queue.
          </>
        ),
      },
      container_3: {
        source: {
          icon: "img/reddit-logo.png",
          link: "https://www.reddit.com/r/FastAPI/comments/11oq09r/comment/jc4dwit/?utm_source=share&utm_medium=web2x&context=3",
        },
        user: {
          profilePic: profiles["No-Application5593"]["icon_img"],
          userName: profiles["No-Application5593"]["subreddit"]["display_name_prefixed"],
          fullName: "No-Application5593",
        },
        description: (
          <>
            Wow! This is really great, thank you for your efforts guys. This is what I really need for one of my future projects.
          </>
        ),
      },
      container_4: {
        source: {
          icon: "img/reddit-logo.png",
          link: "https://www.reddit.com/r/FastAPI/comments/11oq09r/comment/jbx4dfn/?utm_source=share&utm_medium=web2x&context=3",
        },
        user: {
          profilePic: profiles["SteamingBeer"]["icon_img"].replace(/&amp;/g, '&'),
          userName: profiles["SteamingBeer"]["subreddit"]["display_name_prefixed"],
          fullName: "SteamingBeer",
        },
        description: (
          <>
            Thank you for your efforts. I see me pitching this library to my team in the near future!
          </>
        ),
      },
    },
    {
      container_1: {
        source: {
          icon: "img/reddit-logo.png",
          link: "https://www.reddit.com/r/FastAPI/comments/124v5di/comment/jee9vm9/?utm_source=share&utm_medium=web2x&context=3",
        },
        user: {
          profilePic: profiles["Berouald"]["icon_img"],
          userName: profiles["Berouald"]["subreddit"]["display_name_prefixed"],
          fullName: "Berouald",
        },
        description: (
          <>
            This is great! I've been thinking about making a similar tool for quite some time, nice job sir! I guess it's to fit your use case, by why stop at Kafka? A paradigm like this would be awesome in the form of a microframework. Like a general message consumer framework with pluggable interfaces for Kafka, Rabbitmq, ActiveMQ or even the Redis message broker.
          </>
        ),
      },
      container_2: {
        source: {
          icon: "img/reddit-logo.png",
          link: "https://www.reddit.com/r/Python/comments/120mt5k/comment/jdpwycr/?utm_source=share&utm_medium=web2x&context=3",
        },
        user: {
          profilePic: profiles["baggiponte"]["icon_img"],
          userName: profiles["baggiponte"]["subreddit"]["display_name_prefixed"],
          fullName: "baggiponte",
        },
        description: (
          <>
            Really hope this project becomes as popular as the OG FastAPI!
          </>
        ),
      },
      
      container_3: {
        source: {
          icon: "img/twitter-logo.svg",
          link: "https://twitter.com/perbu/status/1635014207656849408?s=20",
        },
        user: {
          profilePic: "img/p-alphabet-round-icon.png",
          userName: "Per Buer",
          fullName: "Per Buer",
        },
        description: (
          <>
            I really like how we're getting these more specialized ways to leverage streaming databases, instead of the somewhat intimidating access libraries.
          </>
        ),
      },
      container_4: {
        source: {
          icon: "img/Y_Combinator_Logo.png",
          link: "https://news.ycombinator.com/item?id=35086594",
        },
        user: {
          profilePic: "img/I.svg",
          userName: "iknownothow",
          fullName: "iknownothow",
        },
        description: (
          <>
            It looks incredible and I truly hope your project takes off for my sake since I have to work with Kafka from time to time!
          </>
        ),
      },
    },
  ];

  const handleLoadMore = () => {
    setTestimonialLimitToShow(testimonialLimitToShow === "2" ? "3" : Object.keys(testimonials[0]).length);
  };

  useEffect(() => {
    async function fetchData() {
      try {
        let profilesData = {};
        for (const profile of redditUserProfiles) {
          const response = await fetch(`https://www.reddit.com/user/${profile}/about.json`);
          let data = await response.json();
          data.data.icon_img = data.data.icon_img.split("?")[0]
          profilesData[profile] = data.data;
        }
        setProfiles(profilesData);
      } catch (error) {
        console.error(error);
      }
    }
    fetchData();
  }, []);
  return (
    <section className={`${styles.features}  hero hero--primary`}>
      <div className="container">
        <div className={clsx('col col--12')}>
          <h2 className={styles.title}>The community has spoken!</h2>
        </div>
        <div className="row">
          {testimonials.map((props, idx) => (
            <Testimonial key={idx} testimonialLimitToShow={testimonialLimitToShow} allTestimonials = {props}  />
          ))}
        </div>
        {testimonialLimitToShow < Object.keys(testimonials[0]).length && (
          <div className={styles.buttons}>
            <button className={clsx("button button--lg", styles.heroButton)} onClick={handleLoadMore}>
                Load More
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
