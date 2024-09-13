<template>
  <el-container style="height: 100vh;">
    <!-- 侧边栏 -->
    <el-aside width="200px" style="background-color: #2d3a4b;">
      <div class="logo">
        <h2 style="color: #409EFF; text-align: center;">管理后台</h2>
      </div>
      <el-menu
          default-active="1"
          class="el-menu-vertical-demo"
          @select="handleSelect"
      >
        <el-menu-item index="1" @click="currentView = 'Dashboard'">
          <i class="el-icon-menu"></i>
          <span slot="title">首页</span>
        </el-menu-item>
        <el-menu-item index="2" @click="currentView = 'Cities'">
          <i class="el-icon-location"></i>
          <span slot="title">城市</span>
        </el-menu-item>
        <el-menu-item index="3" @click="currentView = 'Attractions'">
          <i class="el-icon-star-on"></i>
          <span slot="title">景点</span>
        </el-menu-item>
        <el-menu-item index="4" @click="currentView = 'IntroductionAnalysis'">
          <i class="el-icon-s-comment"></i>
          <span slot="title">景点简介分析</span>
        </el-menu-item>
        <el-menu-item index="5" @click="currentView = 'ReviewAnalysis'">
          <i class="el-icon-s-data"></i>
          <span slot="title">景点点评分析</span>
        </el-menu-item>
        <el-menu-item index="6" @click="currentView = 'PriceAnalysis'">
          <i class="el-icon-s-marketing"></i>
          <span slot="title">门票价格分析</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
<!--      <el-header>-->
<!--        <h2>{{ currentView }}</h2>-->
<!--      </el-header>-->
      <el-main>
        <component :is="currentView"></component>
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import Cities from './Cities.vue';
import Attractions from './Attractions.vue';
import ReviewAnalysis from './ReviewAnalysis.vue';
import PriceAnalysis from './PriceAnalysis.vue';
import Dashboard from "@/components/Dashboard.vue";
import IntroductionAnalysis from "@/components/IntroductionAnalysis.vue";
import DistributionAnalysis from "@/components/DistributionAnalysis.vue";

export default {
  data() {
    return {
      currentView: 'Dashboard', // 默认显示Dashboard
    };
  },
  components: {
    Dashboard,
    Cities,
    Attractions,
    ReviewAnalysis,
    PriceAnalysis,
    IntroductionAnalysis,
    DistributionAnalysis
  },

  methods: {
    handleSelect(key, keyPath) {
      // console.log(key, keyPath);
    },
  },
};
</script>

<style scoped>
.el-container {
  background-color: #f5f7fa;
}

.logo {
  padding: 20px;
  background-color: #1a2b3c;
  margin-bottom: 20px;
}

.el-menu-vertical-demo {
  background-color: #1f2d3d;
  color: #fff;
}

.el-menu-vertical-demo .el-menu-item {
  color: #bfcbd9;
}

.el-menu-vertical-demo .el-menu-item.is-active {
  background-color: #409EFF;
  color: #fff;
}

.el-menu-vertical-demo .el-menu-item:hover {
  background-color: #2a3a4b;
}

.header {
  background-color: #fff;
  padding: 0 20px;
  border-bottom: 1px solid #e0e6ed;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  color: #1f2d3d;
  line-height: 60px;
}
</style>
