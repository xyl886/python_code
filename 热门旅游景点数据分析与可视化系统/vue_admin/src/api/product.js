import request from "@/utils/request";

export const API = '/api/';

// 城市管理
export async function get_cities(params) {
    return await request({
        method: 'get',
        url: API + 'cities',
        params: params
    });
}

export async function find_city() {
    return await request({
        method: 'get',
        url: API + 'city',
    });
}

//景点管理
export async function get_attractions(params) {
    return await request({
        method: 'get',
        url: API + 'attractions',
        params: params
    });
}

export async function analyze_attraction_reviews(params) {
    return await request({
        method: 'get',
        url: API + 'analyze_attraction_reviews',
        params: params
    });
}

export async function analyze_attraction_introduction() {
    return await request({
        method: 'get',
        url: API + 'analyze_attraction_introduction',
    });
}

export async function analyze_city_attraction_distribution() {
    return await request({
        method: 'get',
        url: API + 'analyze_city_attraction_distribution',
    });
}

export async function review_analysis() {
    return await request({
        method: 'get',
        url: API + 'review_analysis',
    });
}

export async function price_analyze() {
    return await request({
        method: 'get',
        url: API + 'price_analyze',
    });
}
export async function analyze_hot(){
    return await request({
        method: 'get',
        url: API + 'analyze_hot',
    });
}