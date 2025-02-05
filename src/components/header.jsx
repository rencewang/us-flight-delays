import React, { useState, useEffect, useRef, useMemo } from 'react';

import { greetingArray } from '../content/index';

const Clock = () => {
  const [time, setTime] = useState(new Date());
  const timerRef = useRef(null);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setTime(new Date());
    }, 1000);

    return () => clearInterval(timerRef.current);
  }, []);

  return <span>{time.toLocaleTimeString()}</span>;
};

const Header = () => {
  const greetingText = useMemo(
    () => greetingArray[Math.floor(Math.random() * greetingArray.length)],
    []
  );

  return (
    <header>
      <div class="header-top">
        <Clock />
        <div id="greeting">{greetingText}</div>
      </div>

      <div class="header-about">
        <details open>
          <summary>Lawrence Wang</summary>
          <div style={{ width: '800px' }}>
            Software Development Engineer, ART19 <br />
            B.S. Computer Science and Economics, Yale University <br />
            B.A. Political Science, Yale University <br />
            <a
              href="https://www.instagram.com/rencewang/"
              target="_blank"
              rel="noopener noreferrer"
              style={{ marginRight: '10px' }}
            >
              Instagram
            </a>
            <a
              href="https://www.linkedin.com/in/rencewang/"
              target="_blank"
              rel="noopener noreferrer"
            >
              LinkedIn
            </a>
          </div>
        </details>
      </div>
    </header>
  );
};

export default Header;
