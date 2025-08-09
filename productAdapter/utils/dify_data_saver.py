#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dify数据保存工具模块
提供保存Dify返回数据到本地文件的功能
"""

import os
import json
import time
import logging
import threading
import queue
from datetime import datetime
from typing import List, Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

def save_dify_response_data(
    response_id: str,
    query: Any,
    all_content: List[str],
    chunk_count: int,
    processing_time: float,
    project_root: str,
    filename_prefix: str = "dify"
) -> Optional[str]:
    """
    保存Dify返回的数据到本地文件
    
    Args:
        response_id: 响应ID
        query: 查询内容
        all_content: 所有数据块内容列表
        chunk_count: 数据块数量
        processing_time: 处理时间
        project_root: 项目根目录
        filename_prefix: 文件名前缀，默认为"dify"
        
    Returns:
        str: 保存的文件路径，如果保存失败则返回None
    """
    try:
        # 生成文件名：dify_年月日时分秒
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.txt"
        
        # 确保logs目录存在
        logs_dir = os.path.join(project_root, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # 文件完整路径
        file_path = os.path.join(logs_dir, filename)
        
        # 准备保存的数据
        save_data = {
            "response_id": response_id,
            "query": query,
            "timestamp": timestamp,
            "chunk_count": chunk_count,
            "processing_time": processing_time,
            "content": all_content
        }
        
        # 保存到文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Dify响应数据 - {timestamp}\n")
                f.write(f"# 响应ID: {response_id}\n")
                f.write(f"# 查询内容: {json.dumps(query, ensure_ascii=False, indent=2)}\n")
                f.write(f"# 数据块数量: {chunk_count}\n")
                f.write(f"# 处理时间: {save_data['processing_time']:.2f}秒\n")
                f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                
                # 写入所有数据块内容
                for i, content in enumerate(all_content, 1):
                    f.write(f"## 数据块 {i}\n")
                    f.write(content)
                    f.write("\n\n")
            
            # 检查文件是否成功创建
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                logger.info(f"💾 Dify响应数据已保存到文件: {file_path} (大小: {file_size} 字节)")
                print(f"💾 Dify响应数据已保存到文件: {file_path}")
                print(f"📁 文件路径: {os.path.abspath(file_path)}")
                print(f"📊 数据块数量: {chunk_count}")
                print(f"⏱️ 处理时间: {save_data['processing_time']:.2f}秒")
                print(f"📄 文件大小: {file_size} 字节")
                return file_path
            else:
                logger.error(f"❌ 文件保存失败，文件不存在: {file_path}")
                print(f"❌ 文件保存失败，文件不存在: {file_path}")
                return None
                
        except IOError as io_error:
            error_msg = f"写入文件时出错: {str(io_error)}"
            logger.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            return None
        except Exception as write_error:
            error_msg = f"保存文件时发生未知错误: {str(write_error)}"
            logger.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            return None
            
    except Exception as save_error:
        error_msg = f"保存Dify响应数据到文件时出错: {str(save_error)}"
        logger.error(f"❌ {error_msg}")
        print(f"❌ {error_msg}")
        return None

def save_dify_response_data_with_metadata(
    response_id: str,
    query: Any,
    all_content: List[str],
    chunk_count: int,
    processing_time: float,
    project_root: str,
    additional_metadata: Optional[Dict[str, Any]] = None,
    filename_prefix: str = "dify"
) -> Optional[str]:
    """
    保存Dify返回的数据到本地文件（带额外元数据）
    
    Args:
        response_id: 响应ID
        query: 查询内容
        all_content: 所有数据块内容列表
        chunk_count: 数据块数量
        processing_time: 处理时间
        project_root: 项目根目录
        additional_metadata: 额外的元数据字典
        filename_prefix: 文件名前缀，默认为"dify"
        
    Returns:
        str: 保存的文件路径，如果保存失败则返回None
    """
    try:
        # 生成文件名：dify_年月日时分秒
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.txt"
        
        # 确保logs目录存在
        logs_dir = os.path.join(project_root, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # 文件完整路径
        file_path = os.path.join(logs_dir, filename)
        
        # 准备保存的数据
        save_data = {
            "response_id": response_id,
            "query": query,
            "timestamp": timestamp,
            "chunk_count": chunk_count,
            "processing_time": processing_time,
            "content": all_content
        }
        
        # 如果有额外元数据，添加到保存数据中
        if additional_metadata:
            save_data.update(additional_metadata)
        
        # 保存到文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Dify响应数据 - {timestamp}\n")
                f.write(f"# 响应ID: {response_id}\n")
                f.write(f"# 查询内容: {json.dumps(query, ensure_ascii=False, indent=2)}\n")
                f.write(f"# 数据块数量: {chunk_count}\n")
                f.write(f"# 处理时间: {save_data['processing_time']:.2f}秒\n")
                f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                # 写入额外元数据
                if additional_metadata:
                    f.write(f"# 额外元数据: {json.dumps(additional_metadata, ensure_ascii=False, indent=2)}\n")
                
                f.write("=" * 50 + "\n\n")
                
                # 写入所有数据块内容
                for i, content in enumerate(all_content, 1):
                    f.write(f"## 数据块 {i}\n")
                    f.write(content)
                    f.write("\n\n")
            
            # 检查文件是否成功创建
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                logger.info(f"💾 Dify响应数据已保存到文件: {file_path} (大小: {file_size} 字节)")
                print(f"💾 Dify响应数据已保存到文件: {file_path}")
                print(f"📁 文件路径: {os.path.abspath(file_path)}")
                print(f"📊 数据块数量: {chunk_count}")
                print(f"⏱️ 处理时间: {save_data['processing_time']:.2f}秒")
                print(f"📄 文件大小: {file_size} 字节")
                return file_path
            else:
                logger.error(f"❌ 文件保存失败，文件不存在: {file_path}")
                print(f"❌ 文件保存失败，文件不存在: {file_path}")
                return None
                
        except IOError as io_error:
            error_msg = f"写入文件时出错: {str(io_error)}"
            logger.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            return None
        except Exception as write_error:
            error_msg = f"保存文件时发生未知错误: {str(write_error)}"
            logger.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            return None
            
    except Exception as save_error:
        error_msg = f"保存Dify响应数据到文件时出错: {str(save_error)}"
        logger.error(f"❌ {error_msg}")
        print(f"❌ {error_msg}")
        return None


class DifyStreamingFileWriter:
    """
    边流边写的文件保存器：在后台线程中顺序写入，避免阻塞事件循环/SSE。
    使用方法：
      writer = DifyStreamingFileWriter(response_id, query, project_root, filename_prefix)
      writer.start()
      writer.write(line)
      ...
      writer.set_final_stats(chunk_count, processing_time)
      writer.close()  # 非阻塞，后台线程完成收尾
    """

    def __init__(
        self,
        response_id: str,
        query: Any,
        project_root: str,
        filename_prefix: str = "dify",
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.response_id = response_id
        self.query = query
        self.project_root = project_root
        self.filename_prefix = filename_prefix
        self.additional_metadata = additional_metadata or {}

        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logs_dir = os.path.join(self.project_root, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        self.file_path = os.path.join(logs_dir, f"{self.filename_prefix}_{self.timestamp}.txt")

        self._queue: "queue.Queue[Optional[str]]" = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._chunk_index: int = 0
        self._final_stats: Dict[str, Any] = {}

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _worker() -> None:
            try:
                with open(self.file_path, "w", encoding="utf-8") as f:
                    # header
                    f.write(f"# Dify响应数据 - {self.timestamp}\n")
                    f.write(f"# 响应ID: {self.response_id}\n")
                    f.write(f"# 查询内容: {json.dumps(self.query, ensure_ascii=False, indent=2)}\n")
                    if self.additional_metadata:
                        f.write(f"# 额外元数据: {json.dumps(self.additional_metadata, ensure_ascii=False, indent=2)}\n")
                    f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")

                    # stream body
                    while True:
                        item = self._queue.get()
                        if item is None:
                            break
                        self._chunk_index += 1
                        f.write(f"## 数据块 {self._chunk_index}\n")
                        f.write(item)
                        if not item.endswith("\n"):
                            f.write("\n")
                        f.write("\n")
                        f.flush()

                    # footer with stats
                    if self._final_stats:
                        f.write("=" * 50 + "\n")
                        if "chunk_count" in self._final_stats:
                            f.write(f"# 数据块数量: {self._final_stats['chunk_count']}\n")
                        if "processing_time" in self._final_stats:
                            f.write(f"# 处理时间: {self._final_stats['processing_time']:.2f}秒\n")
                        f.flush()

                if os.path.exists(self.file_path):
                    try:
                        file_size = os.path.getsize(self.file_path)
                        logger.info(
                            f"💾 Dify响应数据已保存到文件: {self.file_path} (大小: {file_size} 字节)"
                        )
                        print(f"💾 Dify响应数据已保存到文件: {self.file_path}")
                    except Exception:
                        pass
                else:
                    logger.error(f"❌ 文件保存失败，文件不存在: {self.file_path}")
            except Exception as e:
                logger.error(f"❌ 流式保存线程异常: {e}")

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()
        # 启动时就打印计划写入的文件路径，便于定位
        try:
            print(f"🗂️ 计划写入Dify流式文件: {os.path.abspath(self.file_path)}")
            logger.info(f"🗂️ 计划写入Dify流式文件: {os.path.abspath(self.file_path)}")
        except Exception:
            pass

    def write(self, line: str) -> None:
        try:
            self._queue.put_nowait(line)
        except Exception:
            pass

    def set_final_stats(self, chunk_count: int = None, processing_time: float = None) -> None:
        if chunk_count is not None:
            self._final_stats["chunk_count"] = chunk_count
        if processing_time is not None:
            self._final_stats["processing_time"] = processing_time

    def close(self) -> None:
        # 非阻塞关闭，后台线程完成收尾
        try:
            self._queue.put_nowait(None)
        except Exception:
            pass


def start_dify_stream_saver(
    response_id: str,
    query: Any,
    project_root: str,
    filename_prefix: str = "dify",
    additional_metadata: Optional[Dict[str, Any]] = None,
    enable_stream_save: Optional[bool] = None,
    use_env: bool = False,
) -> Tuple[Optional[DifyStreamingFileWriter], bool]:
    """
    根据开关决定是否启动流式保存器。
    返回 (stream_saver, enable_stream_save)。未启用时返回 (None, False)。
    - enable_stream_save: 显式开关；
    - use_env: 若为 True 且 enable_stream_save 为 None，则读取环境变量 DIFY_ENABLE_STREAM_SAVE；
      否则默认 False（符合“外部默认不传就是 false”）。
    """
    if enable_stream_save is None:
        if use_env:
            enable_stream_save = os.getenv("DIFY_ENABLE_STREAM_SAVE", "0").lower() in ["1", "true", "yes"]
        else:
            enable_stream_save = False

    if not enable_stream_save:
        return None, False

    writer = DifyStreamingFileWriter(
        response_id=response_id,
        query=query,
        project_root=project_root,
        filename_prefix=filename_prefix,
        additional_metadata=additional_metadata,
    )
    writer.start()
    return writer, True
