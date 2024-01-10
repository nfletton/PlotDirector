import ast
import operator
import unittest
from unittest.mock import patch, mock_open

from pyaxidraw import axidraw

from axipaint import convert_params, process_axidraw_file, process_function, process_option, process_statement


class TestAxidrawCommandProcessing(unittest.TestCase):

    @patch('os.path.isfile', return_value=False)
    def test_process_nonexistent_file(self, mock_isfile):
        process_axidraw_file('fakefile.ad')
        mock_isfile.assert_called_once_with('fakefile.ad')

    @patch('pyaxidraw.axidraw.AxiDraw.connect', return_value=True)
    @patch('pyaxidraw.axidraw.AxiDraw.interactive')
    @patch("builtins.open", new_callable=mock_open, read_data="# SE/A3\noptions model 2\n# millimeter unit\noptions units 2\nupdate\n")
    def test_process_axidraw_file(self, mock_file, mock_interactive, mock_connect):
        process_axidraw_file('assets/commands1.txt')
        mock_file.assert_called_once_with('assets/commands1.txt', 'r')

    def test_convert_params(self):
        conversions = {
            'f1': [int, float],
            'f2': [int, ast.literal_eval],
            'f3': [lambda x: x],
        }
        self.assertEqual(convert_params(conversions, "f1", ["1", "5.896"]), [1, 5.896])
        self.assertEqual(convert_params(conversions, "f2", ["10", "[1.33, 4 , True]"]), [10, [1.33, 4, True]])
        self.assertEqual(convert_params(conversions, "f3", ["abcd"]), ["abcd"])
        self.assertEqual(convert_params(conversions, "f_no_params", []), [])

    @patch.object(axidraw.AxiDraw, "moveto")
    def test_process_function_with_2_params(self, mock_method):
        ad = axidraw.AxiDraw()
        process_function(ad, ['moveto', '2.0', '3.0'])
        mock_method.assert_called_once()

    @patch.object(axidraw.AxiDraw, "penup")
    def test_process_function_with_no_params(self, mock_method):
        ad = axidraw.AxiDraw()
        process_function(ad, ['penup'])
        mock_method.assert_called_once()

    @patch.object(axidraw.AxiDraw, "draw_path")
    def test_process_function_with_list_param(self, mock_method):
        ad = axidraw.AxiDraw()
        ad.interactive()
        process_function(ad, ['draw_path', '[[2,2],[3,2],[3,3],[2,3],[2,2]]'])
        mock_method.assert_called_once()

    def test_process_option(self):
        ad = axidraw.AxiDraw()
        ad.interactive()
        process_option(ad, ['units', '2'])
        assert operator.attrgetter('options.units')(ad) == 2

    @patch.object(axidraw.AxiDraw, "draw_path")
    def test_process_statement_with_function(self, mock_method):
        ad = axidraw.AxiDraw()
        ad.interactive()
        process_statement(ad, 'draw_path [[2,2],[3,2],[3,3],[2,3],[2,2]]')
        mock_method.assert_called_once()

    def test_process_statement_with_option(self):
        ad = axidraw.AxiDraw()
        ad.interactive()
        process_statement(ad, 'options delay 20000')
        assert operator.attrgetter('options.delay')(ad) == 20000
