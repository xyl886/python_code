<template>
  <div>
    <h1>点评分析</h1>
    <div id="city-chart"></div>
    <div id="attraction-chart"></div>
    <div id="trend-chart"></div>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import {review_analysis} from "@/api/product";

export default {
  name: 'ReviewAnalysis',
  data() {
    return {
      opts: {
        city_chart: {},
        attraction_chart: {},
        trend_chart: {},
      }, // 存储从后端获取的 opts 数据
    };
  },
  mounted() {
    // 在组件加载后调用 API 获取数据
    this.fetchReviewAnalysisData();

  },
  methods: {
    async fetchReviewAnalysisData() {
      // try {
      // 发送请求获取 opts 数据
      review_analysis().then(response => {
        Object.assign(this.opts, response.data);
        this.$nextTick(() => {
          this.renderCharts();
        });
      }).catch(error => {
        this.$message.error('错误' + error);
      });
      // 调用渲染函数
      // } catch (error) {
      //   console.error('Error fetching review analysis data:', error);
      // }
    },
    renderCharts() {
      if (this.opts) {
        // 渲染城市景点数量图表
        const cityChart = echarts.init(document.getElementById('city-chart'));
        cityChart.setOption(this.opts.city_chart);

        // // 渲染景点评价柱状图
        const attractionChart = echarts.init(document.getElementById('attraction-chart'));
        attractionChart.setOption(this.opts.attraction_chart);

        // 渲染评论趋势折线图
        const trendChart = echarts.init(document.getElementById('trend-chart'));
        trendChart.setOption(this.opts.trend_chart);
      } else {
        console.error('No opts data available.' + this.opts);
      }
    },
  },
};
</script>

<style scoped>
/* 可根据需求调整样式 */
#city-chart,
#attraction-chart,
#trend-chart {
  width: 100%;
  height: 400px;
}
</style>
