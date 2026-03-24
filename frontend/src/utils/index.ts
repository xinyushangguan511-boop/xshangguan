import type { ProjectStatus, Department, AttachmentModule } from '../types';

export const formatCurrency = (value?: number): string => {
  if (value === undefined || value === null) return '-';
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
  }).format(value);
};

export const formatNumber = (value?: number, decimals = 2): string => {
  if (value === undefined || value === null) return '-';
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

export const formatPercent = (value?: number): string => {
  if (value === undefined || value === null) return '-';
  return `${value.toFixed(2)}%`;
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

export const getStatusColor = (status: ProjectStatus): string => {
  const colors: Record<ProjectStatus, string> = {
    planning: 'blue',
    in_progress: 'green',
    completed: 'gray',
    suspended: 'orange',
  };
  return colors[status] || 'default';
};

export const getStatusText = (status: ProjectStatus): string => {
  const texts: Record<ProjectStatus, string> = {
    planning: '规划中',
    in_progress: '进行中',
    completed: '已完成',
    suspended: '已暂停',
  };
  return texts[status] || status;
};

export const getDepartmentText = (department: Department): string => {
  const texts: Record<Department, string> = {
    market: '市场部',
    engineering: '工程部',
    finance: '财务部',
    admin: '管理员',
  };
  return texts[department] || department;
};

export const getDepartmentColor = (department: Department): string => {
  const colors: Record<Department, string> = {
    market: 'purple',
    engineering: 'cyan',
    finance: 'gold',
    admin: 'red',
  };
  return colors[department] || 'default';
};

export const getAttachmentModuleText = (module: AttachmentModule): string => {
  const texts: Record<AttachmentModule, string> = {
    project: '项目',
    market: '市场',
    engineering: '工程',
    finance: '财务',
  };
  return texts[module] || module;
};

export const getQuarterLabel = (quarter: number): string => {
  return `第${quarter}季度`;
};

export const getMonthLabel = (month: number): string => {
  const months = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'];
  return months[month - 1] || '';
};
