import React from 'react';

const Row = ({ item }) => (
  <tr>
    <td>{item.id}</td>
    <td>{item.name}</td>
    <td>{item.value}</td>
  </tr>
);

export default Row;
