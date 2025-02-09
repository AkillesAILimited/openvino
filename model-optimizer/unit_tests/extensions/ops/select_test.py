# Copyright (C) 2018-2021 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import unittest

import numpy as np
from generator import generator, generate

from extensions.ops.select import Select
from mo.graph.graph import Node
from mo.utils.ir_engine.compare_graphs import compare_graphs
from unit_tests.utils.graph import build_graph_with_attrs


@generator
class TestSelect(unittest.TestCase):
    nodes = [
        ('than', {'kind': 'op'}),
        ('than_data', {'value': np.ones((2, 2)), 'kind': 'data', 'executable': True, 'shape': np.array([2, 2])}),
        ('else', {'kind': 'op'}),
        ('else_data', {'value': np.zeros((2, 2)), 'kind': 'data', 'executable': True, 'shape': np.array([2, 2])}),
        ('condition', {'value': None, 'kind': 'op'}),
        ('condition_data', {'value': None, 'kind': 'data', 'executable': True, 'shape': np.array([2, 2])}),
        ('select', {'type': 'Select', 'kind': 'op', 'op': 'Select', 'infer': Select.infer}),
        ('select_output', {'value': None, 'kind': 'data', 'executable': True, 'shape': None}),
    ]
    edges = [
        ('condition', 'condition_data'),
        ('condition_data', 'select', {'in': 0}),
        ('than', 'than_data'),
        ('than_data', 'select', {'in': 1}),
        ('else', 'else_data'),
        ('else_data', 'select', {'in': 2}),
        ('select', 'select_output', {'out': 0}),
    ]

    def test_select_infer_no_condition(self):
        graph = build_graph_with_attrs(nodes_with_attrs=self.nodes, edges_with_attrs=self.edges)

        # We should propagate only shapes
        graph_ref = build_graph_with_attrs(nodes_with_attrs=self.nodes,
                                           edges_with_attrs=self.edges,
                                           update_nodes_attributes=[('select_output', {'shape': np.array([2, 2])})])

        node = Node(graph, 'select')
        node.infer(node)

        (flag, resp) = compare_graphs(graph, graph_ref, 'select_output', check_op_attrs=True)
        self.assertTrue(flag, resp)

    def test_select_infer_condition_true(self):
        graph = build_graph_with_attrs(nodes_with_attrs=self.nodes, edges_with_attrs=self.edges,
                                       update_nodes_attributes=[('condition', {'value': np.array([True])}),
                                                                ('select_output', {'shape': np.array([2, 2]),
                                                                                   'value': np.ones((2, 2))})
                                                                ])

        # We should propagate shapes and values
        graph_ref = build_graph_with_attrs(nodes_with_attrs=self.nodes,
                                           edges_with_attrs=self.edges,
                                           update_nodes_attributes=[('select_output', {'shape': np.array([2, 2]),
                                                                                       'value': np.ones((2, 2))})])

        node = Node(graph, 'select')
        node.infer(node)

        (flag, resp) = compare_graphs(graph, graph_ref, 'select_output', check_op_attrs=True)
        self.assertTrue(flag, resp)

    def test_select_infer_condition_false(self):
        graph = build_graph_with_attrs(nodes_with_attrs=self.nodes, edges_with_attrs=self.edges,
                                       update_nodes_attributes=[('condition', {'value': np.array([False])}),
                                                                ('select_output', {'shape': np.array([2, 2]),
                                                                                   'value': np.zeros((2, 2))})
                                                                ])

        # We should propagate shapes and values
        graph_ref = build_graph_with_attrs(nodes_with_attrs=self.nodes,
                                           edges_with_attrs=self.edges,
                                           update_nodes_attributes=[('select_output', {'shape': np.array([2, 2]),
                                                                                       'value': np.zeros((2, 2))})])

        node = Node(graph, 'select')
        node.infer(node)

        (flag, resp) = compare_graphs(graph, graph_ref, 'select_output', check_op_attrs=True)
        self.assertTrue(flag, resp)

    def test_select_infer_assert_shapes(self):
        graph = build_graph_with_attrs(nodes_with_attrs=self.nodes, edges_with_attrs=self.edges,
                                       update_nodes_attributes=[('else_data', {'shape': np.array([3, 3]),
                                                                               'value':np.zeros((3, 3))})])

        tested_class = Select(graph=graph, attrs={})

        node = Node(graph, 'select')
        with self.assertRaisesRegex(AssertionError, "Input shapes for node select are not broadcast-able"):
            tested_class.infer(node)

    @generate(*[
        ([5, 6], [1], [5, 6]),
        ([15, 3, 5], [15, 1, 5], [15, 3, 5]),
        ([2, 3, 4, 5], [], [2, 3, 4, 5]),
        ([2, 3, 4, 5], [5], [2, 3, 4, 5]),
        ([2, 3, 4, 5], [2, 1, 1, 5], [2, 3, 4, 5]),
        ([2, 3, 4, 5], [1, 3, 1, 5], [2, 3, 4, 5]),
    ])
    def test_select_infer_condition_shapes_broadcast(self, else_data_shape, than_data_shape, select_output_shape):
        graph = build_graph_with_attrs(nodes_with_attrs=self.nodes, edges_with_attrs=self.edges,
                                       update_nodes_attributes=
                                       [('else_data', {'shape': np.array(else_data_shape),
                                                       'value': np.zeros(else_data_shape, dtype=np.float)}),
                                        ('than_data', {'shape': np.array(than_data_shape),
                                                       'value': np.zeros(than_data_shape, dtype=np.float)}),
                                        ('select_output', {'shape': None, 'value': None})
                                        ])

        node = Node(graph, 'select')
        node.infer(node)

        self.assertTrue(np.array_equal(graph.nodes['select_output']['shape'], np.array(select_output_shape)))

    @generate(*[
        ([5, 6], [5, 6], [5, 6], [5, 6], lambda x: np.ones(x, dtype=np.float),
         lambda x: np.zeros(x, dtype=np.float), lambda x: np.ones(x, dtype=np.float),
         lambda x: np.ones(x, dtype=np.float)),
        ([15, 3, 5], [15, 3, 5], [15, 1, 5], [15, 3, 5], lambda x: np.ones(x, dtype=np.float),
         lambda x: np.zeros(x, dtype=np.float), lambda x: np.ones(x, dtype=np.float),
         lambda x: np.ones(x, dtype=np.float)),
        ([15, 3, 5], [15, 3, 5], [15, 1, 5], [15, 3, 5], lambda x: np.ones(x, dtype=np.float),
         lambda x: None, lambda x: np.ones(x, dtype=np.float), lambda x: np.ones(x, dtype=np.float)),
        ([15, 3, 5], [15, 3, 5], [15, 1, 5], [15, 3, 5], lambda x: np.ones(x, dtype=np.float),
         lambda x: np.ones(x, dtype=np.float), lambda x: None, lambda x: None),
        ([15, 3, 5], [15, 3, 5], [15, 1, 5], [15, 3, 5], lambda x: np.zeros(x, dtype=np.float),
         lambda x: None, lambda x: np.ones(x, dtype=np.float), lambda x: None),
        ([15, 3, 5], [15, 3, 5], [15, 1, 5], [15, 3, 5], lambda x: np.zeros(x, dtype=np.float),
         lambda x: np.ones(x, dtype=np.float), lambda x: None, lambda x: np.ones(x, dtype=np.float)),
        ([15, 3, 5], [15, 3, 5], [15, 1, 5], [15, 3, 5], lambda x: np.array([True], np.bool),
         lambda x: np.zeros(x, dtype=np.float), lambda x: np.ones(x, dtype=np.float),
         lambda x: np.ones(x, dtype=np.float)),
        ([15, 3, 5], [15, 3, 5], [15, 1, 5], [15, 3, 5], lambda x: np.array([False], np.bool),
         lambda x: np.zeros(x, dtype=np.float), lambda x: np.ones(x, dtype=np.float),
         lambda x: np.zeros(x, dtype=np.float)),
        ([2, 3, 4, 5], [2, 3, 4, 5], [], [2, 3, 4, 5], lambda x: np.ones(x, dtype=np.float),
         lambda x: np.zeros(x, dtype=np.float), lambda x: np.ones(x, dtype=np.float),
         lambda x: np.ones(x, dtype=np.float)),
        ([2, 3, 4, 5], [2, 3, 4, 5], [5], [2, 3, 4, 5], lambda x: np.ones(x, dtype=np.float),
         lambda x: np.zeros(x, dtype=np.float), lambda x: np.ones(x, dtype=np.float),
         lambda x: np.ones(x, dtype=np.float)),
        ([2, 3, 1, 1], [2, 1, 1, 5], [2, 3, 4, 5], [2, 3, 4, 5], lambda x: np.ones(x, dtype=np.float),
         lambda x: np.zeros(x, dtype=np.float), lambda x: np.ones(x, dtype=np.float),
         lambda x: np.ones(x, dtype=np.float)),
        ([2, 3, 4, 1], [2, 1, 1, 5], [1, 3, 1, 5], [2, 3, 4, 5], lambda x: np.ones(x, dtype=np.float),
         lambda x: np.zeros(x, dtype=np.float), lambda x: np.ones(x, dtype=np.float),
         lambda x: np.ones(x, dtype=np.float)),
    ])
    def test_select_infer_condition_with_value(self, condition_shape, else_data_shape, than_data_shape,
                                               select_output_shape, condition_value, else_value, than_value,
                                               output_value):
        """
        Unit tests generator can sporadic throw exception if we try
        to run generator with call numpy array generation functions.
        So we need to use lambda function for escape the problem.
        """
        condition_value = condition_value(condition_shape)
        else_value = else_value(else_data_shape)
        than_value = than_value(than_data_shape)
        output_value = output_value(select_output_shape)
        graph = build_graph_with_attrs(nodes_with_attrs=self.nodes, edges_with_attrs=self.edges,
                                       update_nodes_attributes=[('condition_data', {'shape': np.array(condition_shape),
                                                                                    'value': condition_value}),
                                                                ('else_data', {'shape': np.array(else_data_shape),
                                                                               'value': else_value}),
                                                                ('than_data', {'shape': np.array(than_data_shape),
                                                                               'value': than_value}),
                                                                ('select_output',
                                                                 {'shape': np.array(select_output_shape),
                                                                  'value': None})
                                                                ])

        node = Node(graph, 'select')
        node.infer(node)

        self.assertTrue(np.array_equal(graph.nodes['select_output']['value'], output_value))
