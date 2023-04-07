import React from 'react';
import clsx from 'clsx';
import Layout from '@theme/Layout';
import YouTube from 'react-youtube';

import styles from './styles.module.css';

const opts = {
      height: '720',
      width: '1280',
    };

export default function Hello() {
  return (
    <Layout title="Demo" description="Demo">
      <section className={`hero hero--primary ${styles.containerWithMinHeight}`}>
      <div className="container">
        <div className="row">
          <div className="col col--12">
            <YouTube videoId="dQw4w9WgXcQ" opts={opts}/>
          </div>
        </div>
      </div>
    </section>
    </Layout>
  );
}