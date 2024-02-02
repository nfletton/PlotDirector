import ast
import operator
import unittest
from unittest.mock import patch, mock_open

from pyaxidraw import axidraw

from axipaint import AxiPaint, convert_params


class TestAxidrawCommandProcessing(unittest.TestCase):

    @patch('os.path.isfile', return_value=False)
    def test_process_nonexistent_file(self, mock_isfile):
        axi_paint = AxiPaint()
        axi_paint.process_axidraw_file('fakefile.ad')
        mock_isfile.assert_called_once_with('fakefile.ad')

    @patch('pyaxidraw.axidraw.AxiDraw.connect', return_value=True)
    @patch('pyaxidraw.axidraw.AxiDraw.interactive')
    @patch("builtins.open",
           new_callable=mock_open,
           read_data="# SE/A3\noptions model 2\n# millimeter unit\noptions units 2\nupdate\n")
    def test_process_axidraw_file(self, mock_file, mock_interactive, mock_connect):
        axi_paint = AxiPaint()
        axi_paint.process_axidraw_file('assets/commands1.txt')
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
        axi_paint = AxiPaint()
        axi_paint.process_function(['moveto', '2.0', '3.0'])
        mock_method.assert_called_once()

    @patch.object(axidraw.AxiDraw, "penup")
    def test_process_function_with_no_params(self, mock_method):
        axi_paint = AxiPaint()
        axi_paint.process_function(['penup'])
        mock_method.assert_called_once()

    @patch.object(axidraw.AxiDraw, "draw_path")
    def test_process_function_with_list_param(self, mock_method):
        axi_paint = AxiPaint()
        axi_paint.process_function(['draw_path', '[[2,2],[3,2],[3,3],[2,3],[2,2]]'])
        mock_method.assert_called_once()

    def test_process_option(self):
        axi_paint = AxiPaint()
        axi_paint.process_option(['units', '2'])
        assert operator.attrgetter('options.units')(axi_paint.ad) == 2

    @patch.object(axidraw.AxiDraw, "draw_path")
    def test_process_statement_with_function(self, mock_method):
        axi_paint = AxiPaint()
        axi_paint.process_statement('draw_path [[2,2],[3,2],[3,3],[2,3],[2,2]]')
        mock_method.assert_called_once()

    def test_process_statement_with_option(self):
        axi_paint = AxiPaint()
        axi_paint.process_statement('options delay 20000')
        assert operator.attrgetter('options.delay')(axi_paint.ad) == 20000

    def test_process_statement_with_definition(self):
        axi_paint = AxiPaint()
        axi_paint.process_statement('def wash penup\nmoveto 100 100\npendown\nmoveto 110 110\npenup\n')
        assert axi_paint.definitions['wash'] == "penup\nmoveto 100 100\npendown\nmoveto 110 110\npenup\n"

    @patch.object(axidraw.AxiDraw, "moveto")
    @patch.object(axidraw.AxiDraw, "penup")
    @patch.object(axidraw.AxiDraw, "pendown")
    def test_process_statement_that_uses_a_definition(self, mock_pendown, mock_penup, mock_moveto):
        axi_paint = AxiPaint()
        axi_paint.process_statement('def wash penup\nmoveto 100 100\npendown\nmoveto 110 110\npendown\n')
        axi_paint.process_statement('wash')
        assert mock_pendown.call_count == 2
        mock_penup.assert_called_once()
        assert mock_moveto.call_count == 2
