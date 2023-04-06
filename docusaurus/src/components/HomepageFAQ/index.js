import React from 'react';
import clsx from 'clsx';
import {
  Accordion,
  AccordionItem,
  AccordionItemHeading,
  AccordionItemButton,
  AccordionItemPanel,
} from 'react-accessible-accordion';

import styles from './styles.module.css';
import 'react-accessible-accordion/dist/fancy-example.css';

const items = [
  {
    "heading": "How much does FastKafka cost?",
    "content": "FastKafka is under Apache 2.0 license and free to use. That being said, if you want  to show us some love (read: if you’d need and like support, e.g., you want a certain feature or an issue prioritized :-)), you can subscribe for support here."
  },
  {
    "heading": "How can I contribute or request features?",
    "content": "We love and welcome community contributions! Here is a doc to get you started. To request features, add a “Feature request” using the New issue button in Github from this link, or join our feature-request Discord channel."
  },
  {
    "heading": "Do you support any streaming platforms other than Kafka?",
    "content": "No, as in, not yet. We built the initial version for Kafka service and for our needs, but we reached out to the wider community to find out what to do next. We got requests for RabbitMQ, Pulsar, and Redpanda that went to our backlog and we’ll support them in our future releases."
  },
  {
    "heading": "Does FastKafka integrate with AsyncAPI in the way that FastAPi integrates with OpenAPI?",
    "content": "Very much the same, but with a small difference due to dependancies of AsyncAPI. You write your code using decorators and you get AsyncAPI specification generated automatically as YAML file. You can convert that file to static HTML file ether by Python API call, CLI or github action. AsyncAPI requires Node.js, and you don’t necessarily want this in production."
  },
  {
    "heading": "Does it assume that Kafka messages are in JSON format? What if we want to use protobuf, for example?",
    "content": "For the first implementation we just released uses with JSON encoded messages, but we can easily add additional formats/protocols. We’ve created an issue on github and will try to prioritize it for one of the next releases."
  },
]

export default function HomepageFAQ() {
  return (
    <section className={styles.features}>
      <div className="container">
      <div className={clsx('col col--12')}>
          <p className={styles.title}>FAQ's</p>
        </div>
        <div className={clsx('col col--12 text--left padding-horiz--md')}>
        <Accordion allowZeroExpanded>
          {items.map((item, idx) => (
              <AccordionItem key={idx}>
                  <AccordionItemHeading>
                      <AccordionItemButton>
                          {item.heading}
                      </AccordionItemButton>
                  </AccordionItemHeading>
                  <AccordionItemPanel>
                    {item.content}
                  </AccordionItemPanel>
              </AccordionItem>
          ))}
      </Accordion>
        </div>
      </div>
    </section>
  );
}
