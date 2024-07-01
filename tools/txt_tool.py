# -*- coding: utf-8 -*-

import os
import re

import portalocker
from loguru import logger


class TxtTool:

    def __init__(self, file_path, encoding='utf-8'):
        self.file_path = file_path
        self.encoding = encoding
        # 如果文件不存在，创建一个新的空文件
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding=self.encoding) as file:
                logger.info("创建文件：{}".format(self.file_path))
                pass

    def read(self):
        """读取文本文件内容"""
        with open(self.file_path, 'r', encoding=self.encoding) as file:
            with portalocker.Lock(self.file_path, flags=portalocker.LOCK_EX):
                lines = file.readlines()
        logger.info("{}条数据，成功读取文件：{}".format(len(lines), self.file_path))
        return lines

    def write(self, data, overwrite=False):
        """写入数据到文本文件"""
        mode = 'w' if overwrite else 'a'
        with open(self.file_path, mode, encoding=self.encoding) as file:
            with portalocker.Lock(self.file_path, flags=portalocker.LOCK_EX):
                for item in data:
                    file.write(str(item) + '\n')
        logger.info("{}条数据，成功写入文件：{}".format(len(data), self.file_path))

    def append(self, data):
        """追加数据到文本文件末尾"""
        self.write(data, overwrite=False)

    def delete(self, pattern=None, line_numbers=None):
        """
        删除匹配指定模式或行号的数据。

        参数:
        - pattern: 正则表达式模式，用于匹配需要删除的行（可选）
        - line_numbers: 需要删除的行的行号列表（可选）

        注意：pattern 和 line_numbers 不能同时指定。

        返回值: 无
        """
        if pattern is not None and line_numbers is not None:
            raise ValueError("delete() 方法只能接受 pattern 或 line_numbers 之一作为参数，不能同时指定两者")

        if not os.path.exists(self.file_path):
            print(f"文件 {self.file_path} 不存在，无法执行删除操作")
            return

        if pattern is not None:
            # 删除匹配正则表达式的行
            pattern = re.compile(pattern)
            with open(self.file_path, 'r', encoding=self.encoding) as file:
                with portalocker.Lock(self.file_path, flags=portalocker.LOCK_EX):
                    lines = file.readlines()
                    logger.info("{}条数据，成功读取文件：{}".format(len(lines), self.file_path))
            filtered_lines = [line for line in lines if not pattern.search(line)]
        elif line_numbers is not None:
            # 删除指定行号的行
            with open(self.file_path, 'r', encoding=self.encoding) as file:
                with portalocker.Lock(self.file_path, flags=portalocker.LOCK_EX):
                    lines = file.readlines()
                    logger.info("{}条数据，成功读取文件：{}".format(len(lines), self.file_path))
            filtered_lines = [line for i, line in enumerate(lines) if i not in line_numbers]
        else:
            raise ValueError("delete() 方法必须指定 pattern 或 line_numbers 参数")

        with open(self.file_path, 'w', encoding=self.encoding) as file:
            with portalocker.Lock(self.file_path, flags=portalocker.LOCK_EX):
                file.writelines(filtered_lines)
                logger.info("{}条数据，成功写入文件：{}".format(len(filtered_lines), self.file_path))

    def deduplicate(self):
        """去除文本文件中的重复行"""
        with open(self.file_path, 'r', encoding=self.encoding) as file:
            with portalocker.Lock(self.file_path, flags=portalocker.LOCK_EX):
                lines = file.readlines()
        unique_lines = list(set(lines))
        with open(self.file_path, 'w', encoding=self.encoding) as file:
            with portalocker.Lock(self.file_path, flags=portalocker.LOCK_EX):
                file.writelines(unique_lines)
        logger.info("去重前:{},去重后{},成功写入文件：{}".format(len(lines), len(unique_lines), self.file_path))


if __name__ == '__main__':
    txt_tool = TxtTool('example.txt', encoding='utf-8')  # 初始化一个TxtTool对象
    content = txt_tool.read()
    print(content)

    data_to_write = ['This is the first line.', 'This is the second line.', 'This is the third line.']
    txt_tool.write(data_to_write, overwrite=True)

    txt_tool.append(['This is an appended line.'])
    txt_tool.delete(pattern=r'^This is the (first|second) line\.$')
    txt_tool.delete(line_numbers=[0, 2])
    txt_tool.deduplicate()
