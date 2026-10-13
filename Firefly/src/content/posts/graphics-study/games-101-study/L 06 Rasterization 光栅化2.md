---
title: Rasterization 光栅化2
published: 2026-10-13
description: 介绍光栅化的操作
tags: [graphics,games101]
image: ../../images/graphics-study/games-101-study/cat15.avif
category: 计算机图形学学习
series: "Games101学习之路"
seriesOrder: 4
---

# Rasterization 2

## Sample 采样

- 时间上的采样
- 空间上的采样
- Artifacts 走样
> 采样频率跟不上信号的变化

采样之前先做一遍模糊 filter

高频信号需要更快的采样

傅立叶变换 时域=>频域

filtering 去掉频域上特定的频段

图片：空间=>频域 
中间低频，向外辐射越来越高频 

低频纹理内容，高频图像相关边界

滤波=平均=卷积
两个信号的卷积等于两个信号频域上的乘积 

更大的卷积核=更低的频域
采样=重复原始信号的频谱

采样稀疏=>信号频谱过于密集，导致了走样 

反走样=>1.增加采样率 2.反走样=>先模糊，再采样
对三角形覆盖面积求平均=>表征灰度
在连续域内对三角形的二值函数（表征点在三角形内还是三角形外）⬆️用一个卷积核卷积
msaa：用4个点分划一个像素，通过计算点是否在三角形内确定对应的像素的灰度
fxaa：先拿到有锯齿的图=>再处理掉锯齿
taa：复用上一帧的画面，msaa的样本分布到时间上
super resolution
## 信号 