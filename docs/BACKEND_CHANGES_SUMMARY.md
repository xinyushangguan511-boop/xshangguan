# MIS 系统后端修改总结

**生成日期**: 2026年3月22日  
**状态**: 完成

---

## 目录
1. [总体架构变更](#总体架构变更)
2. [Excel导入系统](#excel导入系统)
3. [项目编码自动匹配](#项目编码自动匹配)
4. [附件系统扩展](#附件系统扩展)
5. [API端点汇总](#api端点汇总)
6. [数据库迁移](#数据库迁移)
7. [使用指南](#使用指南)

---

## 总体架构变更

### 新增模块
1. **Excel导入模块** - 自动化数据导入系统
   - `app/utils/excel_parser.py` - Excel解析引擎
   - `app/services/excel_service.py` - Excel业务逻辑层
   - `app/routers/excel_router.py` - Excel API端点
   - `app/schemas/excel_schema.py` - Excel数据验证模型

2. **附件板块系统** - 支持多板块附件管理
   - 项目级 (project)、市场 (market)、工程 (engineering)、财务 (finance)

---

## Excel导入系统

### 1. Excel解析器 (app/utils/excel_parser.py)

#### 功能
- 支持多模块解析：project, market, engineering, finance
- 自动类型转换（字符串→整数、字符串→Decimal）
- 原始数据保留（用于后续字段映射）
- 详细错误报告（行号 + 字段名 + 错误原因）

#### 关键方法
```python
class ExcelParser:
    def __init__(self, module: str)  # 初始化解析器
    def parse_file(file_path: str) -> ExcelImportResult  # 本地文件解析
    def parse_bytes(file_bytes: bytes) -> ExcelImportResult  # 字节流解析
    def get_valid_data() -> List[BaseModel]  # 获取有效数据
    def get_import_objs() -> List[Dict]  # 获取原始导入对象
    def _convert_to_create_model(import_obj)  # 转换为业务模型
```

#### 支持的数据类型转换
- 整数：安全处理None、空字符串、浮点数
- Decimal：金额类字段精确计算
- 日期：YYYY-MM-DD格式

---

### 2. Excel服务 (app/services/excel_service.py)

#### 核心职责
- 文件验证（扩展名、文件大小）
- 权限检查（project_id对应的项目编辑权限）
- 项目编码自动匹配
- 批量数据创建和事务管理

#### 关键方法
```python
class ExcelService:
    async def validate_excel_file(file: UploadFile) -> bytes
    async def import_excel_to_project(project_id, file, user, data_type)
    async def _import_project_data(file, user)
    async def _import_market_data_v2(project_id, content, user)
    async def _import_engineering_data_v2(project_id, content, user)
    async def _import_finance_data_v2(project_id, content, user)
```

#### 两种导入模式
1. **指定项目模式**：`project_id` 不为 None
   - 使用 URL 中的 project_id
   - Excel 可选包含项目编码
   - 如果 Excel 有项目编码，优先使用 Excel 中的编码进行匹配

2. **自动匹配模式**：`project_id` 为 None
   - Excel 必须包含项目编码列
   - 系统自动查询数据库进行匹配
   - 每行数据可关联不同的项目

---

### 3. Excel导入数据模型 (app/schemas/excel_schema.py)

#### ProjectExcelImport
```python
class ProjectExcelImport(BaseModel):
    项目编码: str  # 必填
    项目名称: str  # 必填
    项目描述: Optional[str]
    建设单位: Optional[str]
    项目地点: Optional[str]
    合同开始时间: Optional[date]
    合同结束时间: Optional[date]
    合同工期: Optional[int]
    实际开工时间: Optional[date]
    项目状态: Optional[str]  # 自动转换：规划中|进行中|已完成|已暂停
```

#### MarketDataExcelImport
```python
class MarketDataExcelImport(BaseModel):
    项目编码: str  # 必填，用于自动匹配project_id
    年份: int  # 必填，2000-2100
    月份: int  # 必填，1-12
    建筑面积: Optional[str]
    结构形式: Optional[str]
    层数: Optional[str]
    合同金额: Optional[str]
    预付款比例: Optional[str]
    预付款金额: Optional[str]
    进度款比例: Optional[str]
    合同类型: Optional[str]
    备注: Optional[str]
```

#### EngineeringDataExcelImport
```python
class EngineeringDataExcelImport(BaseModel):
    项目编码: str  # 必填，用于自动匹配project_id
    年份: int  # 必填，2000-2100
    月份: int  # 必填，1-12
    实际工期: Optional[str]
    期末进度: Optional[str]
    合同金额: Optional[str]
    月产值: Optional[str]
    计划产值: Optional[str]
    月批复: Optional[str]
    管理人员: Optional[str]
    下月计划: Optional[str]
    备注: Optional[str]
```

#### FinanceDataExcelImport
```python
class FinanceDataExcelImport(BaseModel):
    项目编码: str  # 必填，用于自动匹配project_id
    年份: int  # 必填，2000-2100
    月份: int  # 必填，1-12
    月营收: Optional[str]
    月成本: Optional[str]
    月回款: Optional[str]
    目标毛利率: Optional[str]
    备注: Optional[str]
```

#### ExcelImportResult (返回结果)
```python
class ExcelImportResult(BaseModel):
    success_count: int = 0  # 成功导入数量
    fail_count: int = 0  # 失败数量
    errors: List[ExcelImportErrorItem]  # 详细错误信息

class ExcelImportErrorItem(BaseModel):
    row: int  # Excel行号
    field: str  # 错误字段
    message: str  # 错误原因
```

---

## 项目编码自动匹配

### 工作流程

```
Excel文件
    ↓
读取项目编码列 (项目编码)
    ↓
调用 ProjectService.get_by_code(project_code)
    ↓
查询数据库匹配对应project_id
    ↓
若匹配成功，数据关联到对应项目
若匹配失败，报错并指出第X行的无效编码
```

### 应用场景

**场景1**: 单个项目数据导入
```
POST /api/excel/import/{project_id}?data_type=market
- Excel可选包含项目编码
- 如果Excel没有项目编码，使用URL中的project_id
- 如果Excel有项目编码，优先使用Excel中的编码
```

**场景2**: 多项目数据批量导入
```
POST /api/excel/import/auto/data?data_type=market
- Excel必须包含项目编码列
- 每行可以关联不同的项目
- 系统自动查询数据库进行匹配

示例Excel数据：
| 项目编码 | 年份 | 月份 | 建筑面积 | ...
| P001     | 2024 | 1    | 5000   | ...
| P002     | 2024 | 1    | 8000   | ...
```

### 关键实现

**ExcelService._import_market_data_v2()** 的自动匹配逻辑：

```python
# 如果project_id为None（自动匹配模式）
if project_id is None:
    # 检查每行都有项目编码
    for idx, import_obj in enumerate(import_objs):
        project_code = import_obj.get("项目编码")
        if not project_code:
            raise HTTPException(
                detail=f"自动匹配模式下，第{idx+2}行必须包含项目编码"
            )

# 批量导入时的匹配逻辑
for idx, data_obj in enumerate(valid_data):
    import_obj = import_objs[idx]
    project_code = import_obj.get("项目编码")
    
    if project_code:
        # 查询项目编码对应的project_id
        matched_project = await project_service.get_by_code(project_code)
        if not matched_project:
            raise HTTPException(
                detail=f"Excel第{idx+2}行：项目编码'{project_code}'在数据库中不存在"
            )
        actual_project_id = matched_project.id
    
    # 使用匹配的project_id创建记录
    record = MarketData(
        project_id=actual_project_id,
        created_by=user.id,
        **data_dict
    )
```

---

## 附件系统扩展

### 1. Attachment模型改造 (app/models/attachment.py)

#### 新增AttachmentModule枚举
```python
class AttachmentModule(str, PyEnum):
    PROJECT = "project"  # 项目级附件
    MARKET = "market"    # 市场数据板块
    ENGINEERING = "engineering"  # 工程数据板块
    FINANCE = "finance"  # 财务数据板块
```

#### 表结构变更
```sql
-- 新增字段
ALTER TABLE attachments ADD COLUMN module VARCHAR(50) DEFAULT 'project';

-- 新增索引（可选，用于优化查询）
CREATE INDEX idx_attachments_project_module ON attachments(project_id, module);
```

#### Attachment类更新
```python
class Attachment(Base):
    __tablename__ = "attachments"
    
    id: Mapped[uuid.UUID]  # 主键
    project_id: Mapped[uuid.UUID]  # 项目外键
    module: Mapped[AttachmentModule]  # 【新增】所属板块
    department: Mapped[Department]  # 部门
    file_type: Mapped[str | None]  # 文件类型标签
    file_name: Mapped[str]  # 文件原始名称
    file_path: Mapped[str]  # 文件存储路径
    file_size: Mapped[int]  # 文件大小（字节）
    uploaded_by: Mapped[uuid.UUID]  # 上传者ID
    uploaded_at: Mapped[datetime]  # 上传时间
```

### 2. 附件API扩展 (app/routers/attachments.py)

#### 查询端点

**GET /api/attachments/{project_id}**
```
功能：查询项目所有附件（支持按板块筛选）
参数：
  - project_id: 项目ID (路径参数)
  - module: 可选，按板块筛选 (query参数)
    值：project | market | engineering | finance

示例：
  GET /api/attachments/{project_id}  # 查询所有附件
  GET /api/attachments/{project_id}?module=market  # 仅查询市场板块
```

#### 通用上传端点

**POST /api/attachments/{project_id}/upload**
```
功能：通用附件上传（支持各板块）
参数：
  - project_id: 项目ID (路径参数)
  - file: 上传文件 (form-data)
  - file_type: 文件类型标签 (form, 可选)
  - module: 板块 (form, 可选，默认为project)
    值：project | market | engineering | finance

示例：
  POST /api/attachments/{project_id}/upload
  Form Data:
    - file: <选择文件>
    - module: market
    - file_type: 市场调研报告
```

#### 板块专用上传端点

**1. 市场数据 - POST /api/attachments/{project_id}/market/upload**
```
功能：市场数据板块专用附件上传
文件保存路径：{UPLOAD_DIR}/{project_id}/market/
推荐file_type：市场调研报告、竞争对手分析、市场趋势分析、行业报告等

示例请求：
  POST /api/attachments/550e8400-e29b-41d4-a716-446655440000/market/upload
  Form Data:
    - file: market_analysis_2024Q1.pdf
    - file_type: 市场调研报告
```

**2. 工程数据 - POST /api/attachments/{project_id}/engineering/upload**
```
功能：工程数据板块专用附件上传
文件保存路径：{UPLOAD_DIR}/{project_id}/engineering/
推荐file_type：施工图、质检报告、进度照片、安全检查表、竣工文件等

示例请求：
  POST /api/attachments/550e8400-e29b-41d4-a716-446655440000/engineering/upload
  Form Data:
    - file: construction_drawings.dwg
    - file_type: 施工图
```

**3. 财务数据 - POST /api/attachments/{project_id}/finance/upload**
```
功能：财务数据板块专用附件上传
文件保存路径：{UPLOAD_DIR}/{project_id}/finance/
推荐file_type：收款凭证、发票、财务报表、成本单据、审计报告等

示例请求：
  POST /api/attachments/550e8400-e29b-41d4-a716-446655440000/finance/upload
  Form Data:
    - file: invoice_2024.pdf
    - file_type: 收款凭证
```

#### 下载和删除端点（已有，无改动）

**GET /api/attachments/{attachment_id}/download**
```
功能：下载附件
```

**DELETE /api/attachments/{attachment_id}**
```
功能：删除附件
权限：上传者或管理员
```

---

## API端点汇总

### Excel导入API

| 端点 | 方法 | URL | 功能 | 必填参数 | 可选参数 |
|---|---|---|---|---|---|
| 项目导入 | POST | `/api/excel/import/project` | 导入新项目 | file | - |
| 指定项目导入 | POST | `/api/excel/import/{project_id}` | 导入到指定项目 | project_id, data_type, file | - |
| 自动匹配导入 | POST | `/api/excel/import/auto/data` | 自动匹配项目编码导入 | data_type, file | - |

**data_type参数值**：market | engineering | finance

### 附件API

| 端点 | 方法 | URL | 功能 | 必填参数 |
|---|---|---|---|---|
| 查询附件 | GET | `/api/attachments/{project_id}` | 查询项目附件 | project_id |
| 通用上传 | POST | `/api/attachments/{project_id}/upload` | 通用上传 | project_id, file |
| 市场上传 | POST | `/api/attachments/{project_id}/market/upload` | 市场数据上传 | project_id, file |
| 工程上传 | POST | `/api/attachments/{project_id}/engineering/upload` | 工程数据上传 | project_id, file |
| 财务上传 | POST | `/api/attachments/{project_id}/finance/upload` | 财务数据上传 | project_id, file |
| 下载附件 | GET | `/api/attachments/{attachment_id}/download` | 下载附件 | attachment_id |
| 删除附件 | DELETE | `/api/attachments/{attachment_id}` | 删除附件 | attachment_id |

---

## 数据库迁移

### 需要执行的迁移步骤

#### 1. Attachment表字段增加
```sql
-- 添加module字段（附件所属板块）
ALTER TABLE attachments 
ADD COLUMN module VARCHAR(50) DEFAULT 'project' NOT NULL;

-- 添加索引以优化查询性能
CREATE INDEX idx_attachments_project_module 
ON attachments(project_id, module);
```

#### 2. 现有数据处理
```sql
-- 将现有所有附件标记为项目级 (project)
UPDATE attachments SET module = 'project' WHERE module = 'project' OR TRUE;
```

#### 3. 验证迁移
```sql
-- 查看字段是否添加成功
SELECT * FROM attachments LIMIT 1;

-- 查看索引是否创建成功
SELECT * FROM pg_indexes WHERE tablename = 'attachments';
```

### Alembic自动迁移（推荐）

```python
# 在 backend/alembic/versions/ 下创建新迁移文件
# 例如：002_add_attachment_module.py

from alembic import op
import sqlalchemy as sa

def upgrade():
    # 添加module列
    op.add_column('attachments', 
        sa.Column('module', sa.String(50), 
            nullable=False, server_default='project'))
    
    # 创建索引
    op.create_index('idx_attachments_project_module',
        'attachments', ['project_id', 'module'])

def downgrade():
    op.drop_index('idx_attachments_project_module')
    op.drop_column('attachments', 'module')
```

---

## 使用指南

### 1. Excel文件格式要求

#### 列名必须使用中文
所有Excel文件的第一行必须是列名，且列名必须使用中文，以匹配数据库字段。

#### 项目数据示例
```
| 项目编码 | 项目名称 | 项目描述 | 建设单位 | 项目地点 | 合同开始时间 | 合同结束时间 | 合同工期 | 实际开工时间 | 项目状态 |
| P001     | 商业中心 | 城市综合体 | ABC公司 | 北京市朝阳区 | 2024-01-01 | 2026-12-31 | 24 | 2024-02-01 | 进行中 |
| P002     | 办公楼   | 甲级写字楼 | XYZ公司 | 深圳市南山区 | 2024-03-01 | 2025-12-31 | 12 | 2024-04-01 | 规划中 |
```

#### 市场数据示例
```
| 项目编码 | 年份 | 月份 | 建筑面积 | 结构形式 | 层数 | 合同金额 | 预付款比例 | 预付款金额 | 进度款比例 | 合同类型 | 备注 |
| P001     | 2024 | 1    | 5000   | 框架     | 20   | 100000  | 0.30      | 30000     | 0.50      | 固定价格 | 一期工程 |
| P002     | 2024 | 1    | 8000   | 钢混     | 25   | 150000  | 0.25      | 37500     | 0.50      | 浮动价格 | 二期工程 |
```

#### 工程数据示例
```
| 项目编码 | 年份 | 月份 | 实际工期 | 期末进度 | 合同金额 | 月产值 | 计划产值 | 月批复 | 管理人员 | 下月计划 | 备注 |
| P001     | 2024 | 1    | 8       | 15%      | 100000  | 8000  | 10000  | 8000   | 5      | 12000   | 按计划进行 |
```

#### 财务数据示例
```
| 项目编码 | 年份 | 月份 | 月营收 | 月成本 | 月回款 | 目标毛利率 | 备注 |
| P001     | 2024 | 1    | 100000 | 60000 | 80000 | 0.40      | 第一个月 |
```

### 2. 导入流程

#### 方式一：指定项目导入（推荐用于单项目数据）
```
1. 准备Excel文件（可选包含项目编码）
2. 调用 POST /api/excel/import/{project_id}?data_type=market
3. 选择文件并上传
4. 等待导入完成
```

#### 方式二：自动匹配导入（推荐用于多项目批量导入）
```
1. 准备Excel文件（必须包含项目编码列）
2. 调用 POST /api/excel/import/auto/data?data_type=market
3. 选择文件并上传
4. 系统自动查询并匹配每行数据的项目ID
5. 等待导入完成
```

### 3. 附件上传流程

#### 方式一：使用板块专用端点（推荐）
```
市场数据：
  POST /api/attachments/{project_id}/market/upload
  
工程数据：
  POST /api/attachments/{project_id}/engineering/upload
  
财务数据：
  POST /api/attachments/{project_id}/finance/upload
```

#### 方式二：使用通用端点（灵活）
```
POST /api/attachments/{project_id}/upload
参数：module=market (或 engineering/finance/project)
```

### 4. 错误处理

#### Excel导入错误示例
```json
{
  "detail": "Excel解析失败：\n第2行 项目编码：Field required\n第2行 项目名称：Field required"
}
```

**常见错误及解决方案**：
| 错误 | 原因 | 解决方案 |
|---|---|---|
| 项目编码: Field required | 缺少必填字段 | 确保Excel第一行包含正确的中文列名 |
| 年份: ensure this value is less than or equal to 2100 | 年份超出范围 | 输入2000-2100之间的年份 |
| 项目编码'P999'在数据库中不存在 | 自动匹配失败 | 确保项目编码在数据库中存在 |

#### 附件上传错误示例
```json
{
  "detail": "File type not allowed. Allowed: ['.xls', '.xlsx', '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.jpg', '.png', '.dwg']"
}
```

---

## 文件清单

### 新创建文件
1. `app/utils/excel_parser.py` - Excel解析器
2. `app/services/excel_service.py` - Excel服务
3. `app/routers/excel_router.py` - Excel路由
4. `app/schemas/excel_schema.py` - Excel数据模型

### 修改的文件
1. `app/models/attachment.py` - 添加AttachmentModule枚举和module字段
2. `app/schemas/attachment.py` - 添加module字段到响应模型
3. `app/routers/attachments.py` - 添加三个板块的专用上传端点
4. `app/models/__init__.py` - 导出AttachmentModule
5. `app/schemas/__init__.py` - 导出AttachmentModule

### 配置文件（无改动）
- `app/config.py` - 文件配置（ALLOWED_EXTENSIONS、MAX_FILE_SIZE、UPLOAD_DIR）已在原有配置中

---

## 部署检查清单

在部署前请确保：

- [ ] 所有新文件已正确创建
- [ ] 所有修改的文件已正确更新
- [ ] `__init__.py` 文件已更新（导出新的类和枚举）
- [ ] 数据库迁移已执行（添加attachment.module字段）
- [ ] 后端服务已重启
- [ ] Excel导入测试通过（项目、市场、工程、财务各一条记录）
- [ ] 自动匹配导入测试通过（多项目批量导入）
- [ ] 附件上传测试通过（各板块各一个文件）

---

## 技术栈

| 组件 | 版本 | 用途 |
|---|---|---|
| FastAPI | 0.100+ | Web框架 |
| SQLAlchemy | 2.0+ | ORM框架 |
| Pydantic | 2.0+ | 数据验证 |
| Pandas | 2.0+ | Excel解析 |
| openpyxl | 3.0+ | Excel引擎 |
| PostgreSQL | 12+ | 数据库 |

---

## 性能优化建议

1. **数据库索引**：已为attachments添加(project_id, module)复合索引
2. **Excel解析优化**：支持大文件分块处理（当前实现单次加载）
3. **项目编码缓存**：可考虑缓存常用项目编码以加快匹配速度
4. **并发限制**：考虑添加API限流以防止大量并发上传

---

## 文档维护

- 更新日期：2026年3月22日
- 维护人员：系统架构师
- 下一步审查：部署前检查

---

**文档完整性验证**：✅ 所有改动已完整记录

---

## 本次后端补充更新（2026-03-22，新增）

> 本节用于补充本轮联调中新增的后端修复与增强，重点覆盖“项目删除失败修复、枚举兼容修复、上传文件句柄释放、统计方案文档收敛、代码注释完善”等内容。

### 1. 项目删除失败问题修复（关键）

#### 1.1 问题现象
- 删除项目时出现数据库报错，根因是线上/本地已有库缺少 `attachments.module` 列，导致删除链路中的附件相关 SQL 失败。

#### 1.2 修复动作
- 增量迁移与初始化脚本同时补齐：
- 在 `attachments` 表新增 `module` 字段。
- 新增附件模块枚举类型 `attachmentmodule`。
- 为 `attachments.module` 设置默认值并补索引。

#### 1.3 涉及文件
- `backend/migrate_db.py`
- `backend/init_database.py`
- `backend/alembic/versions/002_add_attachment_module.py`

---

### 2. PostgreSQL 枚举兼容性修复（关键）

#### 2.1 问题原因
- 在实际迁移中发现枚举标签大小写与当前数据库类型定义不一致，触发枚举值不兼容或默认值转换失败。

#### 2.2 修复动作
- 统一了附件模块枚举标签与数据库枚举定义的兼容表示。
- 对默认值赋值过程补充显式类型转换，避免隐式转换导致的迁移失败。

#### 2.3 结果
- 迁移可重复执行。
- 目标库可正确包含 `attachments.module` 字段并保持默认值可用。

---

### 3. Excel 导入接口资源释放增强

#### 3.1 改动说明
- 在 Excel 导入路由中补充了统一 `finally` 关闭上传文件句柄逻辑，防止异常路径遗漏释放。

#### 3.2 涉及文件
- `backend/app/routers/excel_router.py`

#### 3.3 设计结论
- 导入流程仍为“内存解析 + 数据入库”，不会把原始 Excel 文件长期落盘保存。

---

### 4. 附件模块筛选稳健性增强

#### 4.1 改动说明
- 附件查询接口中，先将 `module` 查询参数转换为枚举再参与数据库过滤，降低字符串直比导致的兼容问题。

#### 4.2 涉及文件
- `backend/app/routers/attachments.py`

---

### 5. 统计需求文档收敛（A+ 方案）

#### 5.1 文档新增与修订
- 新增统计权限化查询需求文档，并按最终结论收敛为仅保留 DB 方案 A+。

#### 5.2 涉及文件
- `docs/20260322统计权限化查询需求改造说明.md`

---

### 6. 后端代码可维护性注释补充

#### 6.1 改动说明
- 对本轮修改过的后端关键文件增加了“具体且可执行”的注释，聚焦：
- 枚举转换意图。
- 导入接口资源生命周期。
- 迁移脚本幂等判断与兼容分支。

#### 6.2 价值
- 降低后续维护门槛。
- 提升排障时对设计意图的可追溯性。

---

### 7. 本次补充修改文件清单

- `backend/app/routers/attachments.py`
- `backend/app/routers/excel_router.py`
- `backend/migrate_db.py`
- `backend/init_database.py`
- `backend/alembic/versions/002_add_attachment_module.py`
- `docs/20260322统计权限化查询需求改造说明.md`

---

### 8. 验证状态

- 已验证：数据库中存在 `attachments.module` 字段。
- 已验证：迁移修复后不再触发该删除链路阻塞问题。
- 已验证：后端相关修改文件无新增语法/结构错误。
