---
title: Shading 着色1
published: 2026-10-13
description: 介绍深度缓冲和Bling-Phong反射模型
tags: [graphics,games101]
image: ../../images/graphics-study/games-101-study/cat16.avif
category: 计算机图形学学习
series: "Games101学习之路"
seriesOrder: 5
---

# Z-Buffer 深度缓冲

- 用来描述像素的前后关系
- 每个像素存储对应的深度值
  > - frame buffer帧缓冲存储像素的颜色
  > - depth buffer深度缓冲存储像素的深度值

## Z-Buffer 要求

1. $z\in[0,1]$
2. z更小更近，更大更远

```
    // 深度缓存初始化为∞
    for(each triangle T)
        for(each sample(x,y,z) in T)
            if(z < z_buffer[x,y])
                z_buffer[x,y] = z;
                frame_buffer[x,y] = rgb;
            else
                ...
```

# Bling- Phong反射模型

- 高光：镜面反射
- 漫反射
- 环境光照

## 一些概念和符号

- shading point 着色点：在物体表面
- inputs 光线方向 $I$：指向光源
- 法线方向 $n$
- viewer direction观测者方向 $v$：指向观测者

> 着色的局部性：只考虑这个点的着色情况 => 不产生阴影，只有明暗变化

## 漫反射

- 漫反射：$L_d=k_d(I/r^2)max(0,\boldsymbol{n}\cdot\boldsymbol{l})$

## 高光

- 观察方向和反射方向接近 => 半程向量h和n接近 => 镜面反射法线是角平分线 => $\mathbf{h}=\frac{\mathbf{v}+\mathbf{l}}{\|\mathbf{v}+\mathbf{l}\|}$
- 镜面反射：$L_s=k_s(I/r^2)max(0,\mathbf{n}\cdot\mathbf{h})^p$
  > p指数用于控制高光在夹角稍大时能量迅速衰减，收束高光的范围

## 环境光照

- 环境光照：$L_a = k_aI_a$，$I_a$是环境光

## 总光能量

- 总能量（对应颜色）：环境光+漫反射+高光反射
