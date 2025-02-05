import React from 'react';

import { projects } from '../content/projects';
import { art } from '../content/art';
import Row from './row';

const Table = () => {
  return (
    <table>
      <thead>
        <tr>
          <th>N</th>
          <th>Title</th>
          <th>Year</th>
          <th>Date</th>
          <th rowspan="3">Category</th>
          <th rowspan="2">Link</th>
        </tr>
        <tr>
          <th colspan="2">For Projects</th>
          <th colspan="2">Year</th>
        </tr>
        <tr>
          <th colspan="2">For Art</th>
          <th colspan="2">Year</th>
          <th colspan="2">Media</th>
        </tr>
      </thead>
      <tbody>
        <tr></tr>
        {projects.map((item, index) => (
          <Row key={index} item={item} index={index} />
        ))}
      </tbody>
    </table>
  );
};

export default Table;
