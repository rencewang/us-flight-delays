import React from 'react';

const Row = ({ index, item }) => (
  <tr>
    <td>{index + 1}</td>
    <td>{item.title}</td>
    <td>{item.year}</td>
    <td>{item.date}</td>
    <td>{item.category}</td>
    <td>
      <a href={item.link} target="_blank" rel="noopener noreferrer">
        See Demo
      </a>
    </td>
  </tr>
);

export default Row;
