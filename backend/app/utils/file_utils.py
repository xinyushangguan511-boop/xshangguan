import os
import uuid
from typing import List, Optional, BinaryIO
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from starlette.datastructures import UploadFile as StarletteUploadFile


class FileUtils:
    """通用文件操作工具类，兼容FastAPI UploadFile，适配attachments.py业务场景"""

    @staticmethod
    def validate_file_extension(filename: Optional[str], allowed_extensions: List[str]) -> bool:
        """
        校验文件后缀是否合法（适配attachments.py的ALLOWED_EXTENSIONS）
        :param filename: 文件名（可为None）
        :param allowed_extensions: 允许的后缀列表（如 ['.pdf', '.docx']）
        :return: 校验结果
        """
        if not filename:
            return False
        ext = os.path.splitext(filename)[1].lower()
        return ext in allowed_extensions

    @staticmethod
    def validate_file_size(file, max_size: int) -> bool:
        """
        校验文件大小是否超出限制（单位：字节，适配attachments.py的MAX_FILE_SIZE）
        :param file: FastAPI UploadFile对象或bytes内容
        :param max_size: 最大允许大小（字节）
        :return: 校验结果
        """
        try:
            if isinstance(file, bytes):
                return len(file) <= max_size
            # 重置文件指针（避免读取后指针偏移导致后续操作异常）
            file.file.seek(0, os.SEEK_END)
            file_size = file.file.tell()
            file.file.seek(0)  # 重置指针
            return file_size <= max_size
        except Exception:
            return False

    @staticmethod
    async def read_upload_file_bytes(file: UploadFile) -> bytes:
        """
        安全读取UploadFile的字节内容（自动重置指针）
        :param file: FastAPI UploadFile对象
        :return: 文件字节内容
        """
        content = await file.read()
        await file.seek(0)  # 重置指针，避免后续操作异常
        return content

    @staticmethod
    def create_dir_if_not_exists(dir_path: str) -> None:
        """
        创建目录（不存在则创建，存在则忽略）
        :param dir_path: 目录路径
        """
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """
        生成唯一文件名（保留原后缀，适配attachments.py的uuid命名逻辑）
        :param original_filename: 原始文件名
        :return: 唯一文件名（如：f82e9c37-7e0b-4a8a-9f0c-8c7d6e5f4a3b.pdf）
        """
        if not original_filename:
            raise ValueError("Original filename cannot be empty")
        ext = os.path.splitext(original_filename)[1].lower()
        unique_name = str(uuid.uuid4()) + ext
        return unique_name

    @staticmethod
    def get_safe_file_path(base_dir: str, filename: str) -> str:
        """
        安全拼接文件路径（防止路径遍历攻击）
        :param base_dir: 基础目录
        :param filename: 文件名
        :return: 安全的文件路径
        """
        # 清理文件名中的危险字符
        safe_filename = os.path.basename(filename)  # 移除路径部分
        safe_filename = safe_filename.replace("../", "").replace("..\\", "")  # 防御遍历
        # 拼接绝对路径
        abs_base = os.path.abspath(base_dir)
        abs_path = os.path.abspath(os.path.join(abs_base, safe_filename))
        # 校验路径是否在基础目录内（防止越界）
        if not abs_path.startswith(abs_base):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path (path traversal detected)"
            )
        return abs_path

    @staticmethod
    def delete_file_safely(file_path: str) -> bool:
        """
        安全删除文件（不存在则返回True，避免报错）
        :param file_path: 文件路径
        :return: 是否删除成功（或文件不存在）
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            # 可根据需要记录日志
            print(f"Delete file error: {e}")
            return False

    @staticmethod
    def get_file_size(file_path: str) -> Optional[int]:
        """
        获取文件大小（字节）
        :param file_path: 文件路径
        :return: 文件大小（None表示文件不存在）
        """
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return None