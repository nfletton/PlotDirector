import ast
import operator
import unittest
from unittest.mock import mock_open, patch

from plot_director import PlotDirector, convert_params

from nextdraw import NextDraw


class TestNextDrawCommandProcessing(unittest.TestCase):

    @patch('os.path.isfile', return_value=False)
    def test_process_nonexistent_file(self, mock_isfile):
        director = PlotDirector(NextDraw(), '')
        director.process_commands('fakefile.ad')
        mock_isfile.assert_called_once_with('fakefile.ad')

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

    @patch.object(NextDraw, "moveto")
    def test_process_function_with_2_params(self, mock_method):
        director = PlotDirector(NextDraw(), '')
        director.process_function(['moveto', '2.0', '3.0'])
        mock_method.assert_called_once()

    @patch.object(NextDraw, "penup")
    def test_process_function_with_no_params(self, mock_method):
        director = PlotDirector(NextDraw(), '')
        director.process_function(['penup'])
        mock_method.assert_called_once()

    @patch.object(NextDraw, "draw_path")
    def test_process_function_with_list_param(self, mock_method):
        director = PlotDirector(NextDraw(), '')
        director.process_function(['draw_path', '[[2,2],[3,2],[3,3],[2,3],[2,2]]'])
        mock_method.assert_called_once()

    def test_process_option(self):
        director = PlotDirector(NextDraw(), '')
        director.apply_option(['units', '2'])
        assert operator.attrgetter('options.units')(director.nd) == 2

    @patch.object(NextDraw, "draw_path")
    def test_process_statement_with_function(self, mock_method):
        director = PlotDirector(NextDraw(), '')
        director.process_statement('draw_path [[2,2],[3,2],[3,3],[2,3],[2,2]]')
        mock_method.assert_called_once()

    def test_process_statement_with_option(self):
        director = PlotDirector(NextDraw(), '')
        director.process_statement('options delay 20000')
        assert operator.attrgetter('options.delay')(director.nd) == 20000

    def test_process_statement_with_definition(self):
        director = PlotDirector(NextDraw(), '')
        director.process_statement('def repeat_me penup|moveto 100 100|pendown|moveto 110 110|penup')
        assert director.definitions['repeat_me'] == "penup|moveto 100 100|pendown|moveto 110 110|penup"

    @patch.object(NextDraw, "moveto")
    @patch.object(NextDraw, "penup")
    @patch.object(NextDraw, "pendown")
    def test_process_statement_that_uses_a_definition(self, mock_pendown, mock_penup, mock_moveto):
        director = PlotDirector(NextDraw(), '')
        director.process_statement('def repeat_me penup|moveto 100 100|pendown|moveto 110 110|pendown')
        director.process_statement('repeat_me')
        assert mock_pendown.call_count == 2
        mock_penup.assert_called_once()
        assert mock_moveto.call_count == 2
