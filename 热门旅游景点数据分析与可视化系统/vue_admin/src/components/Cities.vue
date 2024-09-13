<template>
  <div>
          <el-header>
        <h2>城市</h2>
      </el-header>
    <el-table :data="cities" stripe style="width: 100%;">
      <el-table-column prop="name" label="城市名称" width="180"></el-table-column>
      <el-table-column prop="pinyin" label="拼音" width="180"></el-table-column>
      <el-table-column prop="nums" label="访问人数" width="180"></el-table-column>
      <el-table-column prop="detail" label="简介"></el-table-column>
      <el-table-column prop="top3" label="TOP3景点" width="220"></el-table-column>
      <el-table-column
          label="操作"
          width="120">
        <template slot-scope="scope">
          <el-button @click="viewDetails(scope.row)" type="primary" size="small">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
        background
        layout="prev, pager, next, jumper"
        :current-page="currentPage"
        :page-size="pageSize"
        :total="totalItems"
        @current-change="handlePageChange"
        style="margin-top: 20px; text-align: center;"
    ></el-pagination>
  </div>
</template>

<script>


import {get_cities} from "@/api/product";

export default {
  data() {
    return {
      cities: [],
      totalItems: 0,
      currentPage: 1,
      pageSize: 10,
    };
  },
  methods: {
    fetchCities() {
      get_cities({page: this.currentPage, page_size: this.pageSize}).then(response => {
        if (response.code === 200) {
          this.cities = response.data.cities;
          this.totalItems = response.data.total;
        } else {
          this.$message.error('获取城市数据失败');
        }
      }).catch(error => {
        this.$message.error('网络错误');
      });
    },
    handlePageChange(page) {
      this.currentPage = page;
      this.fetchCities();
    },
    viewDetails(city) {
         if (city.url) {
      window.open(city.url, '_blank');
    } else {
      this.$message.error('无效的URL');
    }
    }
  },
  created() {
    this.fetchCities();
  }
};
</script>
