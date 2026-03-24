"""
记忆存储
使用 SQLite 存储交互历史
"""
import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class Interaction:
    """交互记录数据类"""
    id: Optional[int] = None
    timestamp: float = 0.0
    app_name: str = ""
    input_context: str = ""
    output_completion: str = ""
    accepted: bool = False
    metadata: Optional[Dict] = None


class MemoryStorage:
    """
    记忆存储器

    使用 SQLite 存储用户交互历史
    支持查询、统计和上下文增强
    """

    def __init__(self, db_path: str = "data/copilot.db"):
        """
        初始化记忆存储

        Args:
            db_path: SQLite 数据库路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 交互历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                app_name TEXT NOT NULL,
                input_context TEXT NOT NULL,
                output_completion TEXT NOT NULL,
                accepted INTEGER DEFAULT 0,
                metadata TEXT
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON interactions (timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_app_name ON interactions (app_name)')

        conn.commit()
        conn.close()

    def store_interaction(
        self,
        input_context: str,
        output_completion: str,
        app_name: str = "Unknown",
        accepted: bool = False,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        存储一次交互

        Args:
            input_context: 输入的上下文
            output_completion: AI 生成的补全
            app_name: 应用名称
            accepted: 用户是否接受
            metadata: 额外元数据

        Returns:
            int: 插入的记录 ID
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO interactions (timestamp, app_name, input_context, output_completion, accepted, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            time.time(),
            app_name,
            input_context,
            output_completion,
            1 if accepted else 0,
            json.dumps(metadata, ensure_ascii=False) if metadata else None
        ))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return record_id

    def get_interaction(self, interaction_id: int) -> Optional[Interaction]:
        """获取单条交互记录"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM interactions WHERE id = ?', (interaction_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_interaction(row)
        return None

    def get_interactions(
        self,
        limit: int = 50,
        offset: int = 0,
        app_name: Optional[str] = None,
        accepted_only: bool = False
    ) -> List[Interaction]:
        """
        获取交互记录列表

        Args:
            limit: 返回数量限制
            offset: 偏移量
            app_name: 按应用名称过滤
            accepted_only: 只返回接受的记录

        Returns:
            List[Interaction]: 交互记录列表
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        query = 'SELECT * FROM interactions WHERE 1=1'
        params = []

        if app_name:
            query += ' AND app_name = ?'
            params.append(app_name)

        if accepted_only:
            query += ' AND accepted = 1'

        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_interaction(row) for row in rows]

    def search_interactions(self, query_text: str, limit: int = 20) -> List[Interaction]:
        """
        搜索交互记录

        Args:
            query_text: 搜索关键词
            limit: 返回数量限制

        Returns:
            List[Interaction]: 匹配的交互记录
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM interactions
            WHERE input_context LIKE ? OR output_completion LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (f'%{query_text}%', f'%{query_text}%', limit))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_interaction(row) for row in rows]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 总记录数
        cursor.execute('SELECT COUNT(*) FROM interactions')
        total = cursor.fetchone()[0]

        # 接受的记录数
        cursor.execute('SELECT COUNT(*) FROM interactions WHERE accepted = 1')
        accepted = cursor.fetchone()[0]

        # 数据库大小
        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

        conn.close()

        return {
            "total_interactions": total,
            "accepted_interactions": accepted,
            "accept_rate": accepted / total if total > 0 else 0,
            "database_size_mb": round(db_size / (1024 * 1024), 2),
        }

    def delete_interaction(self, interaction_id: int) -> bool:
        """删除交互记录"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('DELETE FROM interactions WHERE id = ?', (interaction_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    def clear_all(self):
        """清空所有记录"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('DELETE FROM interactions')

        conn.commit()
        conn.close()

    def _row_to_interaction(self, row: tuple) -> Interaction:
        """将数据库行转换为 Interaction 对象"""
        return Interaction(
            id=row[0],
            timestamp=row[1],
            app_name=row[2],
            input_context=row[3],
            output_completion=row[4],
            accepted=bool(row[5]),
            metadata=json.loads(row[6]) if row[6] else None
        )


# 全局存储实例
_storage: Optional[MemoryStorage] = None


def get_memory_storage(db_path: str = None) -> MemoryStorage:
    """获取全局记忆存储实例"""
    global _storage
    if _storage is None:
        path = db_path or "data/copilot.db"
        _storage = MemoryStorage(path)
    return _storage
