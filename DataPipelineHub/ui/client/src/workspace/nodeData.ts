import React from 'react';
import { BuildingBlock } from '@/types/graph';

// this will be changed to be the data we recieve from mongo
export const buildingBlocksData: BuildingBlock[] = [
  {
    id: 'node1',
    type: 'custom',
    label: 'Node1',
    iconType: 'bot',
    color: '#8A2BE2',
    connectIn: 'node2',
    connectOut: 'node2'
  },
  {
    id: 'node2',
    type: 'custom',
    label: 'Node2',
    iconType: 'bot',
    color: '#00B0FF',
    connectIn: ['node1', 'node3'],
    connectOut: ['node1', 'node3']
  },
  {
    id: 'node3',
    type: 'custom',
    label: 'Node3',
    iconType: 'bot',
    color: '#FFB300',
    connectIn: ['node1'],
    connectOut: ['node1']
  },
];