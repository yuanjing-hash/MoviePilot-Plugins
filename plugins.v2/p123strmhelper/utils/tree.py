
import os
from pathlib import Path
from typing import List, Optional


class DirectoryTree:
    """
    目录树生成和对比
    """

    def scan_directory_to_tree(
        self,
        root_path: str,
        output_file: str,
        append: bool = False,
        extensions: Optional[List[str]] = None,
    ):
        """
        扫描目录并生成目录树
        """
        mode = "a" if append else "w"
        with open(output_file, mode, encoding="utf-8") as f:
            for root, _, files in os.walk(root_path):
                for file in files:
                    if extensions and not any(
                        file.lower().endswith(ext) for ext in extensions
                    ):
                        continue
                    relative_path = os.path.relpath(
                        os.path.join(root, file), root_path
                    ).replace("\\", "/")
                    f.write(f"{relative_path}\n")

    def generate_tree_from_list(
        self, path_list: List[str], output_file: str, append: bool = False
    ):
        """
        从列表生成目录树
        """
        mode = "a" if append else "w"
        with open(output_file, mode, encoding="utf-8") as f:
            for path in path_list:
                f.write(f"{path}\n")

    def compare_trees(self, tree_file1: str, tree_file2: str):
        """
        比较两个目录树的差异
        """
        with open(tree_file1, "r", encoding="utf-8") as f1:
            set1 = set(line.strip() for line in f1)
        with open(tree_file2, "r", encoding="utf-8") as f2:
            set2 = set(line.strip() for line in f2)
        return set1.difference(set2)

    def compare_trees_lines(self, tree_file1: str, tree_file2: str):
        """
        比较两个目录树的差异，返回行号
        """
        with open(tree_file1, "r", encoding="utf-8") as f1:
            lines1 = [line.strip() for line in f1]
        with open(tree_file2, "r", encoding="utf-8") as f2:
            set2 = set(line.strip() for line in f2)

        for i, line in enumerate(lines1):
            if line not in set2:
                yield i + 1

    def get_path_by_line_number(self, tree_file: str, line_number: int):
        """
        根据行号获取路径
        """
        with open(tree_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if i == line_number:
                    return line.strip()
