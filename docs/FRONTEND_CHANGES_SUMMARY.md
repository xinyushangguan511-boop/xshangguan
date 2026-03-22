# MIS 系统前端修改总结（本轮联调）

**生成日期**: 2026年3月22日  
**状态**: 完成

---

## 目录
1. 总体目标与改造范围
2. 类型系统与 API 层改造
3. 新增通用组件
4. 页面与业务流接入改造
5. 查询缓存与一致性策略
6. 权限与交互约束
7. 可维护性与注释补充
8. 影响评估与结果
9. 变更文件清单

---

## 1. 总体目标与改造范围

本轮前端改造围绕以下两条主线展开：

1. **Excel 导入能力前端化**
- 接入后端新增的项目导入、按项目导入、自动匹配导入接口。
- 在项目页和各业务板块页提供统一、可复用的导入入口。

2. **附件“板块化”能力前端化**
- 将附件从“仅项目级”扩展为“项目级 + 市场 + 工程 + 财务”多板块管理。
- 实现模块筛选、按模块上传、按模块展示、下载与删除联动刷新。

---

## 2. 类型系统与 API 层改造

### 2.1 类型定义扩展

对 `frontend/src/types/index.ts` 做了结构扩展，使前端类型与后端协议对齐：

- 新增/完善 `AttachmentModule`：
- `project`
- `market`
- `engineering`
- `finance`

- 新增/完善 Excel 导入相关类型：
- `ExcelDataType`
- `ExcelImportResponse`

改造结果：
- 页面层调用 API 时具备更强类型约束，减少 module 与 data_type 误传。
- 减少跨页面重复字面量字符串使用，提升维护一致性。

### 2.2 API 能力扩展

对 `frontend/src/services/api.ts` 做了分层增强：

#### 附件 API 增强
- `attachmentsApi.list(projectId, module?)`
  - 支持按项目查询全部附件。
  - 支持可选 module 过滤查询。

- `attachmentsApi.upload(...)` / `uploadByModule(...)`
  - 增强上传参数以携带模块上下文。
  - 新增“按模块上传”便捷方法，统一前端调用入口。

#### Excel API 新增
- `excelApi.importProjects(file)`
  - 对应“项目基础信息导入”场景。

- `excelApi.importProjectData(projectId, dataType, file)`
  - 对应“已选项目上下文内导入市场/工程/财务数据”场景。

- `excelApi.importAutoMatchedData(dataType, file)`
  - 对应“依据 Excel 中项目编码自动匹配”的批量导入场景。

改造结果：
- 页面层不再直接拼接 URL 与表单字段。
- API 层成为唯一协议入口，降低后续后端协议调整时的改造成本。

### 2.3 工具函数补充

在 `frontend/src/utils/index.ts` 增加模块文案转换方法（如 `getAttachmentModuleText`），统一页面展示文字。

改造结果：
- 模块文案在各页面保持一致。
- 避免页面层散落硬编码中文标签。

---

## 3. 新增通用组件

### 3.1 ExcelImportModal（新增）

文件：`frontend/src/components/ExcelImportModal.tsx`

核心能力：
- 支持项目导入与业务数据导入两种流程。
- 对业务数据导入支持两种模式：
- 导入到当前项目。
- 按 Excel 项目编码自动匹配。

关键实现点：
- 使用 `Upload.Dragger` + `beforeUpload return false`，实现“先选文件，再由 mutation 触发上传”。
- 根据 `dataType` 与 `importMode` 动态分流到不同后端接口。
- 导入成功后自动 `invalidateQueries`，按数据类型刷新对应列表。
- 提供错误提示与状态回收（关闭弹窗时清理文件与模式状态）。

业务价值：
- 将 Excel 导入交互标准化、可复用化。
- 避免各页面重复实现导入弹窗逻辑。

### 3.2 ModuleAttachmentsModal（新增）

文件：`frontend/src/components/ModuleAttachmentsModal.tsx`

核心能力：
- 仅拉取当前模块附件（弹窗打开时才请求）。
- 支持按模块上传、附件列表展示、下载、删除。
- 与用户权限关联，控制上传与删除按钮可见性。

关键实现点：
- `queryKey: ['attachments', projectId, module]` 做模块级缓存隔离。
- 上传成功后同时刷新：
- 模块附件列表缓存。
- 项目附件总列表缓存。
- 下载使用 Blob URL + 动态 `a` 标签触发浏览器下载。
- 删除行为配合二次确认，防止误删。

业务价值：
- 把“附件板块化”能力从后端扩展到用户可感知的前端操作。
- 提高附件数据与业务板块的可追踪性。

---

## 4. 页面与业务流接入改造

### 4.1 组件级接入

#### AttachmentsTab
文件：`frontend/src/components/AttachmentsTab.tsx`

改造点：
- 接入模块化上传行为。
- 统一上传后查询失效策略，确保附件列表实时更新。

#### MarketDataTab / EngineeringDataTab / FinanceDataTab
文件：
- `frontend/src/components/MarketDataTab.tsx`
- `frontend/src/components/EngineeringDataTab.tsx`
- `frontend/src/components/FinanceDataTab.tsx`

改造点：
- 增加 Excel 导入入口。
- 增加对应模块附件管理入口。
- 形成“数据录入 + 附件管理”同屏操作闭环。

### 4.2 页面级接入

#### ProjectDetail
文件：`frontend/src/pages/ProjectDetail.tsx`

改造点：
- 附件查询增加模块维度约束（重点聚焦项目级附件展示语义）。
- 减少混入其它业务模块附件导致的认知混淆。

#### MarketPage / EngineeringPage / FinancePage
文件：
- `frontend/src/pages/MarketPage.tsx`
- `frontend/src/pages/EngineeringPage.tsx`
- `frontend/src/pages/FinancePage.tsx`

改造点：
- 页面操作区接入 Excel 导入能力。
- 页面操作区接入模块附件管理能力。

#### Projects
文件：`frontend/src/pages/Projects.tsx`

改造点：
- 增加“项目 Excel 导入”入口，支持项目主数据批量初始化。

#### AttachmentsPage
文件：`frontend/src/pages/AttachmentsPage.tsx`

改造点：
- 支持根据路由参数预选项目。
- 增加模块过滤器与模块列展示。
- 统一附件中心页与项目详情页的数据语义。

---

## 5. 查询缓存与一致性策略

本轮重点优化 React Query 的缓存一致性策略，避免“操作成功但界面未刷新”的体验问题。

### 5.1 导入后刷新

- 项目导入成功：刷新 `['projects']`。
- 业务数据导入成功：按类型刷新 `['marketData']` / `['engineeringData']` / `['financeData']`。

### 5.2 附件操作后刷新

- 模块附件上传/删除成功后同时刷新：
- `['attachments', projectId, module]`
- `['attachments', projectId]`

结果：
- 模块视图与总览视图数据同步。
- 用户无需手动刷新页面。

---

## 6. 权限与交互约束

### 6.1 权限约束

在模块附件管理组件中沿用既有权限模型：
- 管理员可上传任意板块。
- 业务部门用户仅可上传自己对应板块附件。

删除权限：
- 上传者本人可删。
- 管理员可删。

### 6.2 交互约束

- 当前项目模式导入在无 `projectId` 时禁用或提示改用自动匹配。
- 上传采用“显式点击提交”而非自动直传，降低误操作概率。
- 删除前二次确认，保障可控性。

---

## 7. 可维护性与注释补充

本轮对新增与重点改造文件补充了具体注释，重点说明：

- 导入模式分流的意图与前置条件。
- 为什么使用 `beforeUpload return false` 进行手动上传控制。
- 缓存刷新要同时覆盖模块列表与总览列表的原因。
- 下载采用 Blob URL 的浏览器兼容性实践。

结果：
- 后续开发人员可更快理解改造背景与数据流。
- 降低重复踩坑概率。

---

## 8. 影响评估与结果

### 8.1 用户侧结果

- 用户可在项目页和业务页直接进行 Excel 导入。
- 用户可按业务板块管理附件，操作路径更清晰。
- 导入、上传、删除完成后数据即时刷新，反馈一致。

### 8.2 系统一致性结果

- 前端协议与后端新增能力已对齐。
- 模块维度贯穿类型、API、组件、页面与缓存策略。

### 8.3 风险收敛

- 通过类型约束与显式交互降低误调用风险。
- 通过注释与封装降低后续迭代维护成本。

---

## 9. 变更文件清单

### 9.1 类型与基础层
- `frontend/src/types/index.ts`
- `frontend/src/services/api.ts`
- `frontend/src/utils/index.ts`

### 9.2 新增组件
- `frontend/src/components/ExcelImportModal.tsx`
- `frontend/src/components/ModuleAttachmentsModal.tsx`

### 9.3 组件改造
- `frontend/src/components/AttachmentsTab.tsx`
- `frontend/src/components/MarketDataTab.tsx`
- `frontend/src/components/EngineeringDataTab.tsx`
- `frontend/src/components/FinanceDataTab.tsx`

### 9.4 页面改造
- `frontend/src/pages/ProjectDetail.tsx`
- `frontend/src/pages/MarketPage.tsx`
- `frontend/src/pages/EngineeringPage.tsx`
- `frontend/src/pages/FinancePage.tsx`
- `frontend/src/pages/Projects.tsx`
- `frontend/src/pages/AttachmentsPage.tsx`

---

**文档完整性验证**：✅ 已覆盖本轮前端所有核心改造与落地点
