import React from 'react';
import clsx from 'clsx';
import Layout from '@theme/Layout';

import styles from './styles.module.css';

export default function Hello() {
  return (
    <Layout title="Demo" description="Demo">
      <section className={`hero hero--primary ${styles.containerWithMinHeight}`}>
      <div className="container">
        <div className="row">
          <div className="col col--12">
            <p className={styles.header}>Demo</p>
          </div>
        </div>
        <div className={`text--center padding-horiz--md ${styles.description}`}>
        </div>
      </div>
    </section>
    </Layout>
  );
}