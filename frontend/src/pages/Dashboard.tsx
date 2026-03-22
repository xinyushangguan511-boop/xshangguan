import React from 'react';
import { Row, Col, Card, Statistic, Spin, Typography } from 'antd';
import { ProjectOutlined, DollarOutlined, CheckCircleOutlined, SyncOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import ReactECharts from 'echarts-for-react';
import { projectsApi, statisticsApi } from '../services/api';
import { formatCurrency } from '../utils';

const { Title } = Typography;

export const Dashboard: React.FC = () => {
  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(1, 100),
  });

  const { data: marketSummary, isLoading: marketLoading } = useQuery({
    queryKey: ['marketSummary'],
    queryFn: () => statisticsApi.marketSummary(),
  });

  const { data: engineeringSummary, isLoading: engineeringLoading } = useQuery({
    queryKey: ['engineeringSummary'],
    queryFn: () => statisticsApi.engineeringSummary(),
  });

  const { data: financeSummary, isLoading: financeLoading } = useQuery({
    queryKey: ['financeSummary'],
    queryFn: () => statisticsApi.financeSummary(),
  });

  const isLoading = projectsLoading || marketLoading || engineeringLoading || financeLoading;

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    );
  }

  const projectStats = {
    total: projects?.total || 0,
    inProgress: projects?.items.filter(p => p.status === 'in_progress').length || 0,
    completed: projects?.items.filter(p => p.status === 'completed').length || 0,
    planning: projects?.items.filter(p => p.status === 'planning').length || 0,
  };

  const statusChartOption = {
    tooltip: { trigger: 'item' },
    legend: { bottom: '5%', left: 'center' },
    series: [
      {
        name: '项目状态',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 20, fontWeight: 'bold' } },
        labelLine: { show: false },
        data: [
          { value: projectStats.planning, name: '规划中', itemStyle: { color: '#1890ff' } },
          { value: projectStats.inProgress, name: '进行中', itemStyle: { color: '#52c41a' } },
          { value: projectStats.completed, name: '已完成', itemStyle: { color: '#8c8c8c' } },
        ],
      },
    ],
  };

  const contractChartOption = {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: marketSummary?.contract_value_monthly.map(d => `${d.year}-${d.month}`) || [],
    },
    yAxis: { type: 'value', name: '合同金额' },
    series: [
      {
        data: marketSummary?.contract_value_monthly.map(d => d.total) || [],
        type: 'bar',
        itemStyle: { color: '#722ed1' },
      },
    ],
  };

  const outputChartOption = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['产值', '甲供批复'] },
    xAxis: {
      type: 'category',
      data: engineeringSummary?.monthly_output_cumulative.map(d => `${d.year}-${d.month}`) || [],
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '产值',
        data: engineeringSummary?.monthly_output_cumulative.map(d => d.total) || [],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#13c2c2' },
      },
      {
        name: '甲供批复',
        data: engineeringSummary?.monthly_approval_cumulative.map(d => d.total) || [],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#fa8c16' },
      },
    ],
  };

  return (
    <div>
      <Title level={4}>工作台概览</Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="项目总数"
              value={projectStats.total}
              prefix={<ProjectOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="进行中"
              value={projectStats.inProgress}
              prefix={<SyncOutlined spin />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="合同总金额"
              value={marketSummary?.total_contract_value || 0}
              prefix={<DollarOutlined />}
              formatter={(value) => formatCurrency(Number(value))}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="毛利率"
              value={financeSummary?.gross_margin || 0}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              precision={2}
              valueStyle={{ color: (financeSummary?.gross_margin || 0) >= 0 ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12}>
          <Card title="项目状态分布">
            <ReactECharts option={statusChartOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="月度合同金额">
            <ReactECharts option={contractChartOption} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <Card title="产值与批复趋势">
            <ReactECharts option={outputChartOption} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
