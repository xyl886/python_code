# -*- coding: utf-8 -*-

import os
import re
import time

import pandas as pd
from loguru import logger


def read_excel_to_dict_list(file_path):
    """从 Excel 文件读取数据至字典列表"""
    try:
        df = pd.read_excel(file_path)
        df.fillna(0, inplace=True)  # 使用 inplace=True 以避免创建额外的 DataFrame 对象
    except (FileNotFoundError, ValueError) as e:
        logger.info(f"读取 Excel 文件时出错：{e}")
        return []  # 或者根据需要抛出异常或返回一个空列表
    return df.to_dict(orient='records')


def save_dict_list_to_excel_batch(data_list, output_file, sheet_name, batch_size=1000000):
    df = pd.DataFrame(data_list)
    num_batches = len(df) // batch_size + (len(df) % batch_size > 0)
    for i in range(num_batches):
        batch_start = i * batch_size
        batch_end = min((i + 1) * batch_size, len(df))
        batch_df = df[batch_start:batch_end]
        save_dict_list_to_excel(batch_df.to_dict('records'),
                                output_file=output_file,
                                sheet_name=sheet_name,
                                check_columns=False)


def save_dict_list_to_excel(data_list, output_file, sheet_name='Sheet1', check_columns=True):
    """将字典列表保存到 Excel 文件中
    :param data_list: 字典列表
    :param output_file: 输出 Excel 文件路径
    :param sheet_name: sheet 名称
    :param check_columns: 是否检查列名是否一致
    """
    if isinstance(data_list, list):
        # 过滤掉列表中的None元素
        filtered_data_list = [d for d in data_list if d is not None]
        df = pd.DataFrame(filtered_data_list)
        # 把nan替换掉
        df.fillna('', inplace=True)
        if check_columns:
            column_set = set(df.columns)
            for dictionary in data_list:
                if set(dictionary.keys()) != column_set:
                    raise ValueError("字典列表中列名不一致，请检查数据格式")
        save_df_to_excel(df, output_file, sheet_name=sheet_name, check_columns=check_columns)
    else:
        raise ValueError("Expected a list, got something else.")


def save_dict_to_excel(data_dict, output_file, sheet_name='Sheet1', check_columns=True):
    """将字典保存到 Excel 文件中
    :param data_dict: 字典
    :param output_file: 输出 Excel 文件路径
    :param sheet_name: sheet 名称
    :param check_columns: 是否检查列名是否一致
    """

    df = pd.DataFrame([data_dict])
    save_df_to_excel(df, output_file, sheet_name=sheet_name, check_columns=check_columns)


def sanitize_filename(filename):
    invalid_chars = '*?"<>|'
    sanitized_filename = filename
    for char in invalid_chars:
        sanitized_filename = sanitized_filename.replace(char, '_')
    return sanitized_filename


def save_df_to_excel(df, output_file, sheet_name, check_columns):
    """将df保存到 Excel 文件中
    :param df: df
    :param output_file: 输出 Excel 文件路径
    :param sheet_name: sheet 名称
    :param check_columns: 是否检查列名是否一致
    """
    start_time = time.perf_counter()
    # 检查文件名是否合法，不合法则处理
    output_file = sanitize_filename(output_file)

    def safe_clean_illegal_chars(s):
        if isinstance(s, str):
            return re.sub(r'[\x00-\x1F\x7F]', '', s)
        else:
            return str(s)  # 转换非字符串为字符串

    try:
        # 假设df是你的DataFrame
        for col_name in df.columns:
            df[col_name] = df[col_name].apply(safe_clean_illegal_chars)

        # 检查文件是否存在
        if os.path.isfile(output_file):
            # 打开已存在的 Excel 文件
            excel_book = pd.ExcelFile(output_file, engine='openpyxl')
            # 检查指定的 sheet 是否存在
            if sheet_name in excel_book.sheet_names:
                # 读取已存在的 sheet
                existing_df = pd.read_excel(output_file, sheet_name=sheet_name, engine='openpyxl')

                # 检查列名是否一致
                if check_columns and set(existing_df.columns) != set(df.columns):
                    raise ValueError("列名不匹配，请检查数据格式")

                # 追加数据到现有的 sheet
                with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                    combined_data = pd.concat([existing_df, df], ignore_index=True)
                    combined_data.to_excel(writer, sheet_name=sheet_name, index=False, header=(not existing_df.empty))
                    logger.info(
                        f"{len(df)} 条数据已追加保存到 {output_file} 的 {sheet_name} 表格, "
                        f"耗时 {time.perf_counter() - start_time:.6f} 秒")
            else:
                # sheet 不存在，新建 sheet
                with pd.ExcelWriter(output_file, engine='openpyxl', mode='a') as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    logger.info(
                        f"新建sheet页 {sheet_name}, {len(df)} 条数据已保存到 {output_file} 的 {sheet_name} 表格, "
                        f"耗时 {time.perf_counter() - start_time:.6f} 秒")
        else:
            # 文件不存在，新建文件并新建 sheet
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                logger.info(
                    f"新建文件{output_file}，新建sheet页 {sheet_name}， {len(df)} 条数据已保存到 {sheet_name} 表格, "
                    f"耗时 {time.perf_counter() - start_time:.6f} 秒")
    except Exception as e:
        logger.error(f"保存数据时发生错误: {str(e)}")
