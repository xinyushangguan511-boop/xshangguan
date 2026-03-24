import React, { useMemo, useState } from 'react';
import { Button, Modal, Radio, Space, Upload, message, Typography } from 'antd';
import { InboxOutlined, UploadOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { excelApi } from '../services/api';
import { getAttachmentModuleText } from '../utils';
import type { ExcelDataType } from '../types';

const { Dragger } = Upload;
const { Text } = Typography;

type ModuleDataType = Exclude<ExcelDataType, 'project'>;
type ImportMode = 'project' | 'auto';

interface Props {
  dataType: ExcelDataType;
  projectId?: string;
  buttonText?: string;
  onSuccess?: () => void;
}

const dataQueryKeyMap: Record<ModuleDataType, string> = {
  market: 'marketData',
  engineering: 'engineeringData',
  finance: 'financeData',
};

export const ExcelImportModal: React.FC<Props> = ({ dataType, projectId, buttonText, onSuccess }) => {
  const [open, setOpen] = useState(false);
  const [fileList, setFileList] = useState<File[]>([]);
  const [importMode, setImportMode] = useState<ImportMode>('project');
  const queryClient = useQueryClient();

  const isProjectImport = dataType === 'project';
  const canImportToProject = Boolean(projectId);
  const moduleText = isProjectImport ? '项目' : getAttachmentModuleText(dataType);

  const resolvedButtonText = useMemo(() => {
    if (buttonText) return buttonText;
    return isProjectImport ? '导入项目Excel' : `导入${moduleText}Excel`;
  }, [buttonText, isProjectImport, moduleText]);

  const importMutation = useMutation({
    mutationFn: async () => {
      const file = fileList[0];
      if (!file) {
        throw new Error('请选择要导入的文件');
      }

      // 项目导入和业务数据导入走的是两套后端接口，先在这里分流。
      if (isProjectImport) {
        return excelApi.importProjects(file);
      }

      // 自动匹配模式完全依赖 Excel 中的“项目编码”列，不需要当前页面先选中项目。
      if (importMode === 'auto') {
        return excelApi.importAutoMatchedData(dataType, file);
      }

      // 按当前项目导入时，必须有明确的 projectId，否则无法落到后端的指定项目接口。
      if (!projectId) {
        throw new Error('当前未选择项目，无法按项目导入');
      }

      return excelApi.importProjectData(projectId, dataType, file);
    },
    onSuccess: async (result) => {
      message.success(result.message);

      // 导入成功后按数据类型刷新对应列表，避免用户手动刷新页面。
      if (isProjectImport) {
        await queryClient.invalidateQueries({ queryKey: ['projects'] });
      } else {
        await queryClient.invalidateQueries({ queryKey: [dataQueryKeyMap[dataType]] });
      }

      onSuccess?.();
      setOpen(false);
      setFileList([]);
      setImportMode('project');
    },
    onError: (error: Error) => {
      message.error(error.message || 'Excel 导入失败');
    },
  });

  const handleSubmit = () => {
    if (fileList.length === 0) {
      message.warning('请选择要导入的 Excel 文件');
      return;
    }
    importMutation.mutate();
  };

  const handleClose = () => {
    setOpen(false);
    setFileList([]);
    setImportMode('project');
  };

  return (
    <>
      <Button icon={<UploadOutlined />} onClick={() => setOpen(true)}>
        {resolvedButtonText}
      </Button>

      <Modal
        title={resolvedButtonText}
        open={open}
        onOk={handleSubmit}
        onCancel={handleClose}
        confirmLoading={importMutation.isPending}
        okText="开始导入"
        cancelText="取消"
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          {!isProjectImport && (
            <>
              <Radio.Group
                value={importMode}
                onChange={(event) => setImportMode(event.target.value as ImportMode)}
              >
                <Space direction="vertical">
                  <Radio value="project" disabled={!canImportToProject}>
                    {/* 当前项目模式：适合在项目详情页或已选中项目的数据页里直接导入 */}
                    导入到当前项目
                  </Radio>
                  {/* 自动匹配模式：适合批量导入，依赖 Excel 内部项目编码 */}
                  <Radio value="auto">按 Excel 中的项目编码自动匹配</Radio>
                </Space>
              </Radio.Group>

              {!canImportToProject && importMode === 'project' && (
                <Text type="warning">当前未选择项目，请改用自动匹配导入。</Text>
              )}
            </>
          )}

          <Dragger
            accept=".xls,.xlsx"
            beforeUpload={(file) => {
              // 交由 React Query 控制真正的上传时机，这里只缓存用户选择的文件。
              setFileList([file]);
              return false;
            }}
            fileList={fileList.map((file) => ({
              uid: file.name,
              name: file.name,
              status: 'done' as const,
            }))}
            onRemove={() => setFileList([])}
            maxCount={1}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽 Excel 文件到此区域</p>
            <p className="ant-upload-hint">
              仅支持 .xls 和 .xlsx 文件
            </p>
          </Dragger>
        </Space>
      </Modal>
    </>
  );
};