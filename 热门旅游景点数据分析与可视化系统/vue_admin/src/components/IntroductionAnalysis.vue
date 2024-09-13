<template>
  <div class="attraction-type-chart">
      <h2>景点简介分析</h2>
      <div id="attraction-type-pie" style="width: 1400px; height: 600px;"></div>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import {analyze_attraction_introduction} from "@/api/product";

export default {
  name: 'AttractionTypeChart',
  data() {
    return {
      chart: null,
      chartOptions: null,
    };
  },
  mounted() {
    this.fetchChartData();
  },
  methods: {
    fetchChartData() {
      // 调用后端API获取数据
      analyze_attraction_introduction()
        .then(response => {
          this.chartOptions = response.data;
          this.initChart();
        })
        .catch(error => {
          console.error('API Error:', error);
        });
    },
    initChart() {
      if (this.chartOptions) {
        // 初始化ECharts实例
        this.chart = echarts.init(document.getElementById('attraction-type-pie'));

        // 设置图表选项
        this.chart.setOption(this.chartOptions);
      }
    },
  },
};
</script>

<style scoped>
.attraction-type-chart {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}
</style>
