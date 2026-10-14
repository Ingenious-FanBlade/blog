---
title: Shading 着色2
published: 2026-10-13
description: 介绍重心坐标
tags: [graphics,games101]
image: ../../images/graphics-study/games-101-study/cat18.avif
category: 计算机图形学学习
series: "Games101学习之路"
seriesOrder: 7
---

# Shading 着色3

## Barycentric Coordinates 重心坐标

在一个二维三角形ABC内，某点$(x,y)$满足：
$$
    \alpha A+\beta B +\gamma C = (x,y)
$$
其中$\alpha + \beta + \gamma = 1$，则称$(\alpha,\beta,\gamma)$为该点的**重心坐标**
- 当$\alpha , \beta , \gamma \geq 0$时，则$(x,y)$在三角形内部
- 三角形重心的重心坐标：$(1/3,1/3,1/3)$

### 重心坐标插值

设$\triangle{ABC}$中$A,B,C$点各自有属性$V_1,V_2,V_3$，则三角形内某一点的属性：
$$
    V = \alpha V_1 +\beta V_2 +\gamma V_3
$$
其中$\alpha + \beta + \gamma = 1$，则称$(\alpha,\beta,\gamma)$为该点的**重心坐标**<br>
由于重心坐标不能保证投影后坐标不变，因此理论上重心坐标的插值必须在3维空间中插值。
但实际上，在投影后的2维三角形上进行重心坐标插值有许多好处
> GPU 在光栅化阶段主要需要回答两个问题：
> 1. 屏幕上的某个像素采样点是否位于三角形内？ => 重心坐标可解
> 2. 如果位于内部，应该如何插值该点的深度、颜色、纹理坐标等属性？

实际上，我们一样可以在2维进行重心坐标插值，只需要对2维的重心坐标作一个修正，就可以还原为3维的重心坐标。<br>
这就是**透视正确插值**

### 透视正确插值
设屏幕空间计算出的重心坐标为：
$$
    (\lambda_A,\lambda_B,\lambda_C)
$$
三个顶点在透视投影后的齐次坐标的$w$分量分别为
$$
    w_A,w_B,w_C
$$
则对应的透视修正为：
$$
    \beta_i = \frac{\lambda_i/w_i}{\lambda_A/w_A+\lambda_B/w_B+\lambda_C/w_C}
$$
这就是修正后的重心坐标，对应的就是三维空间中真正的重心坐标

### 推导透视正确修正

设三角形三个点在三维空间中的齐次坐标为：
$$
    C'_i
$$
三角形内某点在**三维空间**中的坐标为：
$$
    P'= \sum_i{\beta_i C'_i},\quad\sum{\beta_i}=1
$$
其中$\beta$为三维空间中的重心坐标<br>
然后经过投影矩阵$M$后：
$$
    P = MP'= M\sum_i{\beta_i C'_i} = \sum_i{\beta_i MC'_i} = \sum_i{\beta_i C_i}
$$
其中$P$是该点在**裁剪空间**中的坐标，$C_i$是三角形顶点在**裁剪空间**中的坐标<br>
取该点的$x$坐标为例，有：
$$
    X_P = \sum_i{\beta_iX_i},\quad w_P = \sum_i{\beta_iw_i}
$$
接下来做透视除法，$x$坐标为：
$$
    x = \frac{X_P}{w_P} = \frac{\sum_i{\beta_iX_i}}{\sum_i{\beta_iw_i}}
$$
整理上式，令$S = \sum_i{\beta_iw_i}$：
$$
    x = \frac{\sum_i{\beta_iX_i}}{S} = \sum_i{\frac{\beta_iw_i}{S}\frac{X_i}{w_i}} = \sum_i{\boxed{\frac{\beta_iw_i}{\sum_j{\beta_jw_j}}}\frac{X_i}{w_i}}
$$
由于$X_i/w_i$即为原先的三角形投影到屏幕后的**屏幕**$x$坐标，根据重心坐标的定义，有：
$$
    \lambda_i = \frac{\beta_iw_i}{\sum_j{\beta_jw_j}}
$$
根据重心坐标的性质，有$\sum_i{\beta_i}=1$，设$S = \sum_j{\beta_jw_j}$，经过一些数学计算：
$$
    \lambda_i = \frac{\beta_iw_i}{\sum_j{\beta_jw_j}} \Longrightarrow \frac{\lambda_i}{w_i} = \frac{\beta_i}{S} \Longrightarrow \sum_j{\frac{\lambda_j}{w_j}} = \frac{\sum_j{\beta_j}}{S} = \frac{1}{S} \Longrightarrow \beta_i = S\frac{\lambda_i}{w_i} = \frac{\lambda_i/w_i}{\sum_j{\lambda_j/w_j}}
$$
原命题得证