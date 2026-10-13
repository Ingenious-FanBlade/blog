---
title: Shading 着色1
published: 2026-10-13
description: 介绍光栅化的操作
tags: [graphics,games101]
image: ../../images/graphics-study/games-101-study/cat17.avif
category: 计算机图形学学习
series: "Games101学习之路"
seriesOrder: 5
---

# Shading 1

### Bling- Phone反射模型
- 高光：镜面反射
- 漫反射
- 环境光照

shading point 着色点：在物体表面
inputs 光线方向 $I$：指向光源
法线方向 $n$
viewer direction观测者方向 $v$：指向观测者

> 着色的局部性：只考虑这个点的着色情况 => 不产生阴影，只有明暗变化

### 漫反射

- 漫反射：$L_d=k_d(I/r^2)max(0,\boldsymbol{n}\cdot\boldsymbol{l})$
- $Color_{new} = k_d(Color_{old}/r^2)max(0,\boldsymbol{n}\cdot\boldsymbol{l})$