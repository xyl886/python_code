<template>
  <div>
              <el-header>
        <h2>景点</h2>
      </el-header>
    <!-- 城市筛选框 -->
    <el-select v-model="city.id" placeholder="选择城市" @change="fetchAttractions"
               style="width: 200px; margin-bottom: 20px;">
      <el-option
          v-for="city in cities"
          :key="city.id"
          :label="city.name"
          :value="city.id">
      </el-option>
    </el-select>

    <!-- 景点列表 -->
    <el-table :data="attractions" stripe style="width: 100%; margin-top: 20px;">
      <el-table-column prop="name" label="景点名称" width="150"></el-table-column>
      <el-table-column prop="address" label="地址" width="150"></el-table-column>
      <el-table-column prop="phone" label="联系电话" width="150"></el-table-column>
      <el-table-column prop="ticket_info" label="票务信息" width="350" show-overflow-tooltip></el-table-column>
      <el-table-column prop="summary" label="摘要" width="350" show-overflow-tooltip></el-table-column>
      <el-table-column prop="review_num" label="点评数" width="100"></el-table-column>
      <el-table-column label="操作" width="200">
        <template slot-scope="scope">
          <el-button @click="viewDetails(scope.row)" type="primary" size="small">跳转</el-button>
          <!--          <el-button @click="spider(scope.row)" type="primary" size="small">重新爬取</el-button>-->
          <el-button @click="analysis(scope.row)" type="primary" size="small">分析</el-button>
        </template>
      </el-table-column>
    </el-table>
    <!-- 分析结果弹窗 -->
    <el-dialog :visible.sync="dialogVisible" title="景点点评分析" width="50%">
      <div v-if="sentimentCounts || wordcloudOpts" style="display: flex; justify-content: space-between;">
        <!-- 左侧情感分析结果 -->
        <div v-if="sentimentCounts" style="flex: 1; margin-right: 20px;">
          <h3>情感分析结果</h3>
          <div id="sentiment-pie-chart" style="width: 400px; height: 300px;"></div>
        </div>

        <!-- 右侧热词词云图 -->
        <div v-if="wordcloudOpts" style="flex: 1;">
          <h3>热词词云图</h3>
          <div id="wordcloud-chart" style="width: 400px; height: 300px;"></div>
        </div>
      </div>

      <span slot="footer" class="dialog-footer">
    <el-button @click="dialogVisible = false">关闭</el-button>
  </span>
    </el-dialog>

    <!-- 分页 -->
    <el-pagination
        background
        layout="prev, pager, next, jumper"
        :current-page="currentPage"
        :page-size="pageSize"
        :total="totalItems"
        @current-change="handlePageChange"
        style="margin-top: 20px; text-align: center;">
    </el-pagination>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import 'echarts-wordcloud';

import {get_attractions, find_city, analyze_attraction_reviews} from "@/api/product";

export default {
  data() {
    return {
      city: [],         // 存储所有城市的数据
      cities: [],
      city_id: null,      // 当前选择的城市ID
      attractions: [],    // 存储景点列表
      totalItems: 0,      // 总景点数
      currentPage: 1,     // 当前页码
      pageSize: 10,       // 每页显示的景点数
      dialogVisible: false,  // 控制弹窗显示
      sentimentCounts: null,  // 情感分析数据
      wordcloudOpts: null,  // 词云图数据
    };
  },
  methods: {
    // 获取城市列表
    fetchCities() {
      find_city().then(response => {
        if (response.code === 200) {
          this.cities = response.data;
          if (this.cities.length > 0) {
            // 默认选择第一个城市
            this.city = this.cities[0];
            this.fetchAttractions();  // 加载该城市的景点
          }
        } else {
          this.$message.error('获取城市数据失败');
        }
      }).catch(error => {
        this.$message.error('网络错误');
      });
    },
    // 获取当前城市的景点列表
    fetchAttractions() {
      get_attractions({
        city_id: this.city.id,
        page: this.currentPage,
        page_size: this.pageSize
      }).then(response => {
        if (response.code === 200) {
          this.attractions = response.data.data;
          this.totalItems = response.data.total;
        } else {
          this.$message.error('获取景点数据失败');
        }
      }).catch(error => {
        this.$message.error('网络错误');
      });
    },
    // 处理分页变化
    handlePageChange(page) {
      this.currentPage = page;
      this.fetchAttractions();
    },
    // 查看景点详情
    viewDetails(attraction) {
      if (attraction.url) {
        window.open(attraction.url, '_blank');
      } else {
        this.$message.error('无效的URL');
      }
    },
    spider(attraction) {
      this.$confirm('确定要重新爬取该景点的详细信息吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        attraction(attraction.id).then(response => {
          if (response.data.code === 200) {
            this.$message.success('爬取成功！');
          } else {
            this.$message.error('爬取失败，请重试。');
          }
        })
            .catch(error => {
              this.$message.error('网络错误');
            });
      });
    },
    analysis(attraction) {
      this.$confirm('确定要查看该景点的点评分析吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        analyze_attraction_reviews({attraction_id: attraction.attraction_id}).then(response => {
          // if (response.data.code === 200) {
          this.sentimentCounts = response.data.sentiment_counts;
          this.wordcloudOpts = response.data.wordcloud_opts;

          // 渲染弹窗内的图表
          this.$nextTick(() => {
            this.renderSentimentChart();
            this.renderWordcloudChart();
          });

          this.dialogVisible = true;
          // } else {
          //   this.$message.error('分析失败，请重试。');
          // }
        })
            .catch(error => {
              this.$message.error('网络错误');
            })
      });
    },
    renderSentimentChart() {
      const sentimentChart = echarts.init(document.getElementById('sentiment-pie-chart'));
      const option = {
        // title: {
        //   text: '景点情感分析',
        //   left: 'center'
        // },
        tooltip: {
          trigger: 'item'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
        },
        series: [
          {
            name: '情感态度',
            type: 'pie',
            radius: '50%',
            data: [
              {value: this.sentimentCounts.positive, name: '正面'},
              {value: this.sentimentCounts.negative, name: '负面'},
            ],
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      };
      sentimentChart.setOption(option);
    },
    renderWordcloudChart() {
      const wordcloudChart = echarts.init(document.getElementById('wordcloud-chart'));
      const option = this.wordcloudOpts;
      wordcloudChart.setOption(option);
    }
  },
  created() {
    this.fetchCities(); // 初次加载时获取城市数据
  }
}
;
</script>
