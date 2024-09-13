<template>
  <div id="attraction-distribution-map" style="width: 100%; height: 600px;"></div>
</template>

<script>
import * as echarts from 'echarts';
import {analyze_city_attraction_distribution} from "@/api/product";

export default {
  name: 'AttractionDistributionMap',
  mounted() {
    this.renderMap();
  },
  methods: {
    async renderMap() {
      try {
        // 调用封装好的接口获取数据
        analyze_city_attraction_distribution().then(response => {
          const chartOptions = response.data;
          this.initChart(chartOptions);
        })
      } catch (error) {
        console.error('请求失败:', error);
      }
    },
    initChart(chartOptions) {
      // 在 mounted 钩子内渲染图表
      const chartDom = document.getElementById('attraction-distribution-map');
      const chart = echarts.init(chartDom);
      chart.setOption(chartOptions);
    },
  },
};
</script>

<style scoped>
#attraction-distribution-map {
  width: 100%;
  height: 600px;
}
</style>
