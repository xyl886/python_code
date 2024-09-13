<template>
  <div>
    <h1>价格分析</h1>
    <!-- 图表容器1: 城市和价格类型的分布 -->
    <div id="city-price-type-chart" style="width: 1400px; height: 800px;"></div>
    <!-- 图表容器2: 价格区间和价格类型的分布 -->
    <div id="price-type-price-chart" style="width: 1400px; height: 800px; margin-top: 40px;"></div>
  </div>
</template>

<script>
import * as echarts from 'echarts'; // 引入 echarts
import { price_analyze } from "@/api/product"; // 使用 axios 获取数据

export default {
  name: 'PriceAnalysis',
  data() {
    return {
      cityPriceTypeChart: null, // 城市和价格类型图表实例
      priceTypePriceChart: null, // 价格区间和价格类型图表实例
      opts: {
        city_price_type_heatmap: {},
        price_type_price_heatmap: {},
      },
    };
  },
  mounted() {
    // 初始化图表
    this.cityPriceTypeChart = echarts.init(document.getElementById('city-price-type-chart'));
    this.priceTypePriceChart = echarts.init(document.getElementById('price-type-price-chart'));
    this.fetchPriceAnalysisData();
  },
  methods: {
    // 获取后端数据
    async fetchPriceAnalysisData() {
      try {
        const response = await price_analyze();
        // 分别设置两个图表的数据
        Object.assign(this.opts, response.data);

        this.$nextTick(() => {
          // 渲染第一个图表：城市和价格类型的分布
          this.cityPriceTypeChart.setOption(this.opts.city_price_type_heatmap);
          // 渲染第二个图表：价格区间和价格类型的分布
          this.priceTypePriceChart.setOption(this.opts.price_type_price_heatmap);
        });

      } catch (error) {
        console.error('Error fetching price analysis data:', error);
        this.$message.error('获取数据失败，请稍后重试' + error);
      }
    },
  },
};
</script>

<style scoped>
#city-price-type-chart,
#price-type-price-chart {
  margin-top: 20px;
}
</style>
