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
    "content": "FastKafka is under Apache 2.0 license and free to use."
  },
  {
    "heading": "How can I contribute or request features?",
    "content": "We love and welcome community contributions! Here is a <a href='https://github.com/airtai/fastkafka/blob/main/CONTRIBUTING.md' target='_blank'>doc</a> to get you started. To request features, add a “Feature request” using the New issue button in GitHub from <a href='https://github.com/airtai/fastkafka/issues' target='_blank'>this link</a>, or join our feature-request <a href='https://discord.gg/CJWmYpyFbc' target='_blank'>Discord channel</a>."
  },
  {
    "heading": "Do you support any streaming platforms other than Kafka?",
    "content": "Slowly, but surely. We built the initial version for Kafka service and for our needs, but we reached out to the wider community to find out what to do next. We added support for Redpanda, and also got requests for RabbitMQ and Pulsar that went to our backlog and we’ll support them in our future releases."
  },
  {
    "heading": "Does FastKafka integrate with AsyncAPI in the way that FastAPi integrates with OpenAPI?",
    "content": "Very much the same, but with a small difference due to dependencies of AsyncAPI. You write your code using decorators and you get AsyncAPI specification generated automatically as YAML file. You can convert that file to static HTML file ether by Python API call, CLI or github action. AsyncAPI requires Node.js, and you don’t necessarily want this in production."
  },
  {
    "heading": "Does it assume that Kafka messages are in JSON format? What if we want to use protobuf, for example?",
    "content": "For the first implementation we just released uses with JSON encoded messages, but we can easily add additional formats/protocols. We’ve created an issue on GitHub and will try to prioritize it for one of the next releases."
  },
]

export default function HomepageFAQ() {
  return (
    <section className={styles.features}>
      <div className="container">
      <div className={clsx('col col--12')}>
          <h2 className={styles.title}>FAQs</h2>
          <p>For anything not covered here, join <a className={styles.href} href="https://discord.gg/CJWmYpyFbc" target="_blank">our Discord</a></p>
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
                  <p className={styles.faqAnswer} dangerouslySetInnerHTML={{__html: item.content}} />
                  </AccordionItemPanel>
              </AccordionItem>
          ))}
      </Accordion>
        </div>
      </div>
    </section>
  );
}
