import React from 'react';
import clsx from 'clsx';

import styles from './styles.module.css';

export default function RobotFooterIcon() {
  return (
    <section>
      <div className={clsx("container", styles.robotFooterContainer)}>
       <img className={styles.robotFooterIcon} src="img/robot-footer.svg" />
      </div>
    </section>
  );
}
