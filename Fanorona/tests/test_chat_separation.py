import ast
import pathlib
import unittest


class ChatSeparationTests(unittest.TestCase):
    def test_only_chat_handler_appends_to_history(self):
        path = pathlib.Path(__file__).parents[1] / "ui" / "main_window.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "_append_chat":
                    function = next(
                        (parent for parent in ast.walk(tree) if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)) and node in ast.walk(parent)),
                        None,
                    )
                    calls.append(function.name if function else "")
        self.assertEqual(sorted(calls), ["_handle_message", "_send_chat"])

    def test_status_does_not_write_to_chat_widget(self):
        path = pathlib.Path(__file__).parents[1] / "ui" / "main_window.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        status_function = next(node for node in tree.body if isinstance(node, ast.ClassDef) for node in node.body if isinstance(node, ast.FunctionDef) and node.name == "_set_status")
        self.assertNotIn("chat_history", ast.unparse(status_function))


if __name__ == "__main__":
    unittest.main()
