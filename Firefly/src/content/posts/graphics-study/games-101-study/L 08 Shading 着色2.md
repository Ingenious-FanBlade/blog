---
title: Shading 着色2
published: 2026-10-13
description: 主要介绍三种着色方式和实时渲染管线
tags: [graphics,games101]
image: ../../images/graphics-study/games-101-study/cat17.avif
category: 计算机图形学学习
series: "Games101学习之路"
seriesOrder: 6
---

# Shading 着色2

## 着色频率
- Face **面**着色：对每个面着色，每个面的颜色相同
- Vertex **顶点**着色：对每个顶点着色，顶点内的三角形通过一次插值算出来着色
  > 通过计算包含该顶点的所有三角形的法向量的加权平均：
  > $N_v=\frac{\sum_iN_i}{\|\sum_iN_i\|}$
- Pixel **像素**着色：逐像素着色
  > 通过**重心坐标**插值计算每个像素对应的法线

## Graphics Pipeline 实时渲染管线
```mermaid
flowchart LR
    X[顶点] --> A[Vertex Processing 顶点处理] -- 顶点流 -->B[Triangle Processing 三角形处理] -- 三角形流 -->C[Rasterization 光栅化] -- 片元流 --> D[Fragment Processing 片元处理] -- 已着色的片元 --> E[帧缓冲区操作] --> F[显示]
```

## Texture Mapping 纹理映射
- 每一个三角形顶点对应一个纹理点 $(u,v)$
- 纹理坐标系$u-v: [0,1]\times[0,1]$