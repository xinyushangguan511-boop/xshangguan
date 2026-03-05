import type { ProjectStatus, Department } from '../types';

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
    planning: 'Planning',
    in_progress: 'In Progress',
    completed: 'Completed',
    suspended: 'Suspended',
  };
  return texts[status] || status;
};

export const getDepartmentText = (department: Department): string => {
  const texts: Record<Department, string> = {
    market: 'Marketing',
    engineering: 'Engineering',
    finance: 'Finance',
    admin: 'Admin',
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

export const getQuarterLabel = (quarter: number): string => {
  return `Q${quarter}`;
};

export const getMonthLabel = (month: number): string => {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return months[month - 1] || '';
};
