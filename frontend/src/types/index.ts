export type Department = 'market' | 'engineering' | 'finance' | 'admin';

export type ProjectStatus = 'planning' | 'in_progress' | 'completed' | 'suspended';

export interface User {
  id: string;
  username: string;
  department: Department;
  real_name?: string;
  phone?: string;
  email?: string;
  is_active: boolean;
  created_at: string;
}

export interface UserCreate {
  username: string;
  password: string;
  department: Department;
  real_name?: string;
  phone?: string;
  email?: string;
}

export interface UserUpdate {
  username?: string;
  department?: Department;
  real_name?: string;
  phone?: string;
  email?: string;
  is_active?: boolean;
}

export interface ProfileUpdate {
  real_name?: string;
  phone?: string;
  email?: string;
}

export interface PasswordChange {
  current_password: string;
  new_password: string;
}

export interface RegistrationStatus {
  registration_allowed: boolean;
  message: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Project {
  id: string;
  project_code: string;
  project_name: string;
  description?: string;
  construction_unit?: string;
  location?: string;
  contract_start_date?: string;
  contract_end_date?: string;
  contract_duration?: number;
  actual_start_date?: string;
  status: ProjectStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
  page: number;
  page_size: number;
}

export interface MarketData {
  id: string;
  project_id: string;
  year: number;
  month: number;
  building_area?: number;
  structure?: string;
  floors?: number;
  contract_value?: number;
  prepayment_ratio?: number;
  advance_amount?: number;
  progress_payment_ratio?: number;
  contract_type?: string;
  remarks?: string;
  created_by?: string;
  created_at: string;
}

export interface EngineeringData {
  id: string;
  project_id: string;
  year: number;
  month: number;
  actual_duration?: number;
  end_period_progress?: string;
  contract_value?: number;
  monthly_output?: number;
  planned_output?: number;
  monthly_approval?: number;
  staff_count?: number;
  next_month_plan?: number;
  remarks?: string;
  created_by?: string;
  created_at: string;
}

export interface FinanceData {
  id: string;
  project_id: string;
  year: number;
  month: number;
  monthly_revenue?: number;
  monthly_cost?: number;
  monthly_payment_received?: number;
  target_margin?: number;
  remarks?: string;
  created_by?: string;
  created_at: string;
}

export interface Attachment {
  id: string;
  project_id: string;
  department: Department;
  file_type?: string;
  file_name: string;
  file_path: string;
  file_size: number;
  uploaded_by: string;
  uploaded_at: string;
}

export interface PeriodSummary {
  year: number;
  month?: number;
  quarter?: number;
  total: number;
}

export interface MarketSummary {
  contract_value_monthly: PeriodSummary[];
  contract_value_quarterly: PeriodSummary[];
  contract_value_yearly: PeriodSummary[];
  total_contract_value: number;
}

export interface EngineeringSummary {
  contract_value_monthly: PeriodSummary[];
  contract_value_quarterly: PeriodSummary[];
  contract_value_yearly: PeriodSummary[];
  monthly_output_cumulative: PeriodSummary[];
  monthly_approval_cumulative: PeriodSummary[];
  total_output: number;
  total_approval: number;
  duration_ratio?: number;
  output_rate?: number;
  approval_rate?: number;
  per_capita_output?: number;
}

export interface FinanceSummary {
  revenue_quarterly: PeriodSummary[];
  revenue_yearly: PeriodSummary[];
  cost_quarterly: PeriodSummary[];
  cost_yearly: PeriodSummary[];
  payment_quarterly: PeriodSummary[];
  payment_yearly: PeriodSummary[];
  total_revenue: number;
  total_cost: number;
  total_payment: number;
  gross_margin?: number;
}

export interface ProjectReport {
  project_code: string;
  project_name: string;
  market_summary?: MarketSummary;
  engineering_summary?: EngineeringSummary;
  finance_summary?: FinanceSummary;
}
